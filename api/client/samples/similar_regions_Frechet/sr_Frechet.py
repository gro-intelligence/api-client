import os, glob
import tempfile
import pickle
import logging
from datetime import date

import numpy as np
from scipy.linalg import sqrtm
import pandas as pd
from tqdm import tqdm

from sklearn.neighbors import BallTree, DistanceMetric
from api.client.batch_client import BatchClient, BatchError
from api.client.lib import get_default_logger
#from api.client.samples.similar_regions.similar_region_state import SimilarRegionState
from sklearn.metrics.pairwise import euclidean_distances

""" API Config """
API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

""" Cache dir and file names """
# cache directory should already exist when SR object is created (otherwise /tmp will be used)
CACHE_PATH = "sr_cache"
REGION_INFO_CACHE = "region_info"
DATA_CACHE = "region_data_"
PICKLE_PROTOCOL = 4
REGIONS_PER_QUERY = 100

class SimilarRegionFrechet(object):

    def __init__(self, metric_properties,
                 search_region=0,
                 update_mode="reload",
                 data_dir=None,
                 region_info_reload=False,
                 t_int_per_year=12,
                 resume=False,
                 metric_instance=None):
        """
        :param metric_properties: A dict containing the properties of regions to use when doing the similarity
        computation. This is by default defined in region_properties.py, but can be adjusted.
        :param search_region: region_id to search for similar regions. Default is 0 (entire world).
        :param update: If 'reload', full reload from Gro API after which cache is completely overwritten. If 'no' take only cached data,
        nothing read from Gro API, If 'update', read cached data, then read from API whatever is missing.
        :param region_info_reload: If True, reload region info from Gro, otherwise use cached. Only valid for update_mode='update' or 'reload' (always read cache with update_mode='no')
        :param t_int_per_year: into how many intervals to split calendar year when generating time series from raw data. Default is 12 (roughly monthly). High values (such as 365 - daily) are not recommended for world-wide searches due to storage requirements)
        """
        self.data = None
        self.t_int_per_year = t_int_per_year
        self.t_int_days = 365 / self.t_int_per_year # number of days in single t interval (can be float)
        self.to_retry = []
        self.available_regions = []
        self.available_properties = []
        self._logger = get_default_logger()
        self._logger.setLevel(logging.INFO)
        self.resume = resume

        # extract needed parameters from inputs
        self.metric_properties = metric_properties
        self.needed_properties = sorted(list(set(metric_properties.keys())))
        if metric_instance is not None:
            unresolved_items = [item for item in metric_instance if item not in self.metric_properties]
            assert not unresolved_items, "Found items {} in metric instance not present in metric description".format(unresolved_items)
            self.metric_instance = metric_instance
        else:
            self.metric_instance = dict(zip(self.metric_properties.keys(),[1.0]*len(self.metric_properties)))
            
        if data_dir:
            self.data_dir = data_dir
        elif os.path.isdir(CACHE_PATH) and os.access(CACHE_PATH, os.W_OK):
            self.data_dir = CACHE_PATH
        else:
            # no access to CACHE_PATH - likely doesn't exist => attempt to create directory
            try:
                os.mkdir(CACHE_PATH)
                self.data_dir = CACHE_PATH
            except:
                # last resort
                self.data_dir = tempfile.gettempdir()
        
        self._logger.info("*********Creating similar region object with *******\n\tregion {}\n\tupdate_mode {}\n\tdata_dir {}\n\tregion_info_reload {}\n\tt_int_per_year {}\n".format(search_region,update_mode,self.data_dir,region_info_reload,t_int_per_year))
            
        # if we do not have cache file, switch to reload
        data_path = os.path.join(self.data_dir, DATA_CACHE+str(t_int_per_year)+'.gzip')
        info_path = os.path.join(self.data_dir, REGION_INFO_CACHE)
        update=update_mode
        if update!='reload' and not os.path.isfile(data_path):
            self._logger.info("Do not have cache file {}\n Switching to 'reload' mode".format(data_path))
            update='reload'
        
        if update != 'no': # will be reading from Gro => do some setup (reading just region info, no real data)
            self.client = BatchClient(API_HOST, ACCESS_TOKEN)
            # ask for full info on all world regions
            # region_info is potentially large, used just for info lookiup
            # self.available_regions gives real list of IDs we have
            self.region_info = []
            if region_info_reload or not os.path.isfile(info_path):
                for l in [2,3,4,5]:
                    self._logger.info("Loading region info for geo level {}".format(l))
                    self.region_info += self.client.get_descendant_regions(search_region,descendant_level=l,
                                                                  include_historical=False,
                                                                  include_details=True)
                #reformat as dict with region_id as key
                self.region_info = dict(zip([item['id'] for item in self.region_info], self.region_info))
                
                # immediately save region_info since this is the largest possible reference set
                # (assume we never ask to reload region info for smaller regions)
                with open(info_path, 'wb') as f:
                    self._logger.info("Saving region info file {}".format(info_path))
                    pickle.dump(self.region_info,f)
            else:
                self._logger.info("Reading region info from cache {}".format(info_path))
                with open(info_path, 'rb') as f:
                    self.region_info = pickle.load(f)
                # We might have too many regions in the info cache - this ONLY happens if cache was filled for a parent
                # of region currently requested (filled for entire world but we want only US, for example)
                # this means search region itself is present in the cache
                top_info = self.region_info.get(search_region)
                if top_info:
                    self._logger.info("Search region is present in cache of size {}".format(len(self.region_info)))
                    level = top_info['level'] # can only have 2/3/4/5
                    ri = dict()
                    # get direct descendants for the search region (no op for level==5)
                    ri.update(dict([(r,self.region_info[r]) for r in top_info['contains']
                                    if self.region_info.get(r,{'level':-1})['level']==level+1]))
                    if level<=3: #need to go down one/two more level for countries/continents
                        # will be modifying ri dict, so create a copy first for safety (ok to have it shallow)
                        ri_copy = ri.copy()
                        for item in ri_copy.items():
                            level_dict = dict([(r,self.region_info[r]) for r in item[1]['contains']
                                            if self.region_info.get(r,{'level':-1})['level']==level+2])
                            if level==2: # one more level if started from continents
                                for item_down in level_dict.items():
                                    level_down_dict = dict([(r,self.region_info[r]) for r in item_down[1]['contains']
                                            if self.region_info.get(r,{'level':-1})['level']==level+3])
                                    ri.update(level_down_dict)
                            ri.update(level_dict)
                    self.region_info = ri
                    self._logger.info("Trimmed region info to {} items".format(len(self.region_info)))
            assert self.region_info, "Search region {} is below province level or has no cached info (rerun with region_info_reload=True if so)".format(search_region)
                
            # list of id'd for which we want data - collect countries, provinces and districts
            self.needed_regions = sorted(list(set(self.region_info.keys())))
            
        if update != 'reload': # read from cache
            try:
                self._logger.info("Reading cached data from {} ...".format(data_path))
                self.data = pd.read_pickle(data_path)
                self.available_regions = self.data.index.get_level_values('region').unique()
                self.available_properties = self.data.columns
            except:
                self.data = None
                self._logger.info("Could not load cached data from {} Full re-download will occur if update_mode=update".format(data_path))
                
        if update == 'no': # by definition, should have everything we need just from cache (which is read already)
            missing_regions = set()
            self.needed_regions = sorted(list(self.available_regions))
            missing_properties = set(self.needed_properties) - set(self.available_properties)
            assert not missing_properties, "Local cache is missing properties {} needed by metric. Can not proceed with update_mode=no".format(missing_properties)
            
            # loaded region info (for update !='no' it was read from Gro already)
            with open(info_path, 'rb') as f:
                self.region_info = pickle.load(f) 
             ######### Done with all data for update='no'###################
        else:
            missing_regions = set(self.needed_regions) - set(self.available_regions)
            missing_properties = set(self.needed_properties) - set(self.available_properties)
        
        # eventually self.data is a multi-index DataFrame
        # with first index level being region_id, second is time in months
        # columns are properties
        # Dealing with DF is very slow => use raw np arrays at this stage
        if self.data is None:
            # only happens if reloading from scratch
            #self.data = pd.DataFrame(
            #    index=pd.MultiIndex.from_product([self.needed_regions,range(1,13)], names=['region','month']),
            #    columns=list(self.metric_properties.keys())).sort_index()
            self.data = np.zeros((self.t_int_per_year*len(self.needed_regions),len(self.metric_properties)))
        elif update=='update':            
            # collect regions with any missing properties, add to missing_regons set
            # region is considered missing if any month is missing
            # This is less efficient but simpler then doing individual reg/prop combinations
            # (since we will already be d/l missing regions)
            for m in range(1,1+self.t_int_per_year):
                tmp = pd.isnull(self.data.xs(m,level='month')).any(axis=1)
                missing_regions.update(tmp[tmp].index)
            # Note: Could collect (prop,region) blocks and re-download each separately as
            #month1 = self.data.xs(1,level='month')
            #na_set = np.argwhere(pd.isnull(month1).values)
            #for c in na_set:
            #    self.to_retry.append((month1.columns[c[1]],
            #                          month1.index.get_level_values('region')[c[0]]
            #                         ))
            # and then perform extra d/l phase just for to_retry
                        
            # if we have self.data it was read from cache => it is a pandas DF
            # temporarily convert to numpy array to avoid the need to use
            # different (np vs pd) assignments
            self.data = self.data.values

        # generate lookup maps from regions/properties to their positions in the data array
        self.region_index = dict(zip(self.needed_regions,range(len(self.needed_regions))))
        self.prop_index = dict(zip(self.needed_properties,range(len(self.needed_properties))))

        # counters will be zeroed out later only if we attempt to d/l corresponding block
        # will stay 1 if no action is taken (so that division by counter does not change original value)
        self.data_counters = np.ones(self.data.shape)
        #self.data_counters = pd.DataFrame(0, index=self.data.index, columns=self.data.columns)
        
        
        ################################################
        #
        # Start actual data download - this part should never be executed if update='no'
        #
        # Phase I: each missing property triggers full update for all regions
        # missing_properties/regions are already sets, needed_region - list
        # operates during update_mode=reload or if new properties are added to the metric
        if missing_properties:
            reached_chkpt = False
            #self.processed_q = []
            for property_name in sorted(list(missing_properties)): # convert to sorted list to maintain d/l order
                fn = os.path.join(self.data_dir, property_name+'.npz')
                if self.resume and not reached_chkpt:
                    try:
                        with np.load(fn,allow_pickle=True) as qfile:
                            self._logger.info("Resuming failed d/l: Found checkpoint on {}".format(property_name))
                            self.data = qfile['data']
                            self.data_counters = qfile['data_counters']
                            self.processed_q = list(qfile['processed_q'])
                            self.to_retry = list(qfile['to_retry'])
                        reached_chkpt = True
                    except:
                        # skip this property. All data/counters will be restored when we reach ckekpoint
                        self._logger.info("Resuming failed d/l: Expect {} to have completed in prior run".format(property_name))
                        continue
                else:
                    # will start this d/l from scratch
                    self.data_counters[:,self.prop_index[property_name]] = 0
                    self.processed_q = []
                    self.to_retry = []
                    # create "empty" (in terms of this property) checkpoint marking d/l start
                    np.savez_compressed(fn,
                                    data = self.data,
                                    data_counters = self.data_counters,
                                    processed_q = self.processed_q)
                print("phase I for ", property_name)
                self._load_property_for_regions(property_name, self.needed_regions)
                # Give one attempt to reload data we did not get
                if self.to_retry:
                    self._logger.info("Retrying {} regions".format(len(self.to_retry)))
                    self._load_property_for_regions(property_name, self.to_retry, track_na=False)
                    self.to_retry = []
                # fully done with property => delete its checkpoint
                os.remove(fn)
        if self.resume:
            assert reached_chkpt, "Attempted to resume prior d/l but did not find the chekpoint"
        
        # Phase II: Each missing region triggers update for needed properties
        # which are NOT in properties already downloaded
        # operates mostly during update_mode=update
        if missing_regions:
            regs = [self.region_index[r] for r in missing_regions]
            reg_idx = np.concatenate([np.r_[range(r*self.t_int_per_year,
                                                  r*self.t_int_per_year+self.t_int_per_year)] for r in regs])
            for property_name in set(self.needed_properties) - missing_properties:
                self.data_counters[reg_idx,self.prop_index[property_name]] = 0
                print("phase II for ", property_name)
                self._load_property_for_regions(property_name, missing_regions)

        # Unless data were read from cache (and therefore self.data is already a df)
        # Compute averages and convert to pandas df
        if update != 'no':
            """
            # counters are valid over a grid formed by missing_regions and missing_properties
            # no changes (division by counters) should be applied outside this grid
            # so just set counters to 1 outside the grid and divide through the entire array
            # Note - this looks pretty ugly, there might be a better way to do this
            regs = [self.region_index[r] for r in set(self.needed_regions) - missing_regions]
            reg_idx = [item for l in [list(range(r*12,r*12+12)) for r in regs] for item in l]
            prop_idx = [self.prop_index[p] for p in set(self.needed_properties) - missing_properties]
            self.data_counters[tuple(item[0] for item in itertools.product(reg_idx,prop_idx)),
                  tuple(item[1] for item in itertools.product(reg_idx,prop_idx))] = 1
            """
            # nan's coming from cache will remain nan's
            # if tried to d/l but got no data we will have zero conter value and zero data value
            # result will be 0/0 which is nan (and a warning will be generated, but that's ok)
            self.data = pd.DataFrame(self.data/self.data_counters,
                            index=pd.MultiIndex.from_product([self.needed_regions,range(1,self.t_int_per_year+1)],
                                                             names=['region','month']),
                            columns=self.needed_properties)

        if missing_regions or missing_properties:
            # Safe to simply overwrite entire cache with new self.data since on 'update'
            # we fully loaded previous cache and could have only added missing_regions/properties to it
            # Full cache overwrite is to be expected on 'reload'
            self.data.to_pickle(data_path,protocol=PICKLE_PROTOCOL)
            
        ########################################
        # At this point both self.data and local cache are fully up-to-date and in sync
        # Cache stores all nans in case we want to re-download the data later with update_mode='update'
        ########################################
        
        # DF in memory might be too large if we had regions/properties in cached data
        # which are not used by requestred metrics, so trim the dataframe
        # drop rather than re-index to save memory
        #to_drop = [c for c in self.data.columns if c not in self.needed_properties]
        to_drop = [c for c in self.data.columns if c not in self.metric_instance]
        if to_drop:
            self._logger.info("Will drop columns {} unused by metric".format(to_drop))
            self.data.drop(to_drop, axis=1, inplace=True)
        to_drop = [r for r in self.available_regions if r not in self.needed_regions]
        if to_drop:
            self._logger.info("Will drop {} not requested regons".format(len(to_drop)))
            self.data.drop(to_drop, level='region', inplace=True)

        # Subjective decision - what to do with missing data?
        # option #1 - drop any region with missing data
        # option #2 - fill in missing data with averages 
        # #2 is problematic since particular region can be VERY different from global average
        # and doing this more locally is rather complicated (have to use geographic proximity info)
        # Let's just drop all regions which have ANY missing values (i.e. missing soil moisture in Dec
        # is sufficient to be dropped). This is by far the simplest but possibly a bit extreme.
        # as it puts burden on the user to select well-populated variables for his metrics.
        # Might want to revisit later
        self._logger.info("Dropping regions with insufficient data ...")
        tmp = (self.data.groupby(level='region').count() != self.t_int_per_year).any(axis=1)
        self.data = self.data.loc[tmp[~tmp].index].sort_index()
        
        self._logger.info("Re-creating list of regions and indexes ...")
        # these should be sorted already, but just to be sure ...
        self.available_regions = sorted(list(self.data.index.get_level_values('region').unique()))
        self.num_regions = len(self.available_regions)
        
        # recreate maps since some regions/props might have been dropped
        self.region_index = dict(zip(self.available_regions,range(self.num_regions)))
        self.prop_index = dict(zip(self.needed_properties,range(len(self.needed_properties))))
        
        ###################################
        # Normalization/weighting - if provided with user weight/norm const for given property,
        # use these, otherwise take 1/data std respectively
        # This brings all data to the space over which we will compute distance
        
        # Note that us taking sqrt of user-provided weight here assumes user wants something like
        # dist^2 = \sum w_user_i*(x_i - y_i)^2 (non-squared w_user_i here)
        # Also, pit (point-in-time) properties are still replicated across all time points
        # but will have the same std as non-replicated set
        self._logger.info("Normalization/weighting ...")
        self.pit_properties = []
        self.ts_properties = []
        for c in self.data.columns:
            stdev = self.data[c].std()
            # always report true stds - might want to include them in properties.py as 'norm' on later runs 
            self._logger.info("Data standard deviation for {} is {}".format(c,stdev))
            self.data[c] *= np.sqrt(self.metric_instance[c]) / self.metric_properties[c]['properties'].get("norm",stdev)
                
            # will use to split dataset into time series and pit parts
            col_type = self.metric_properties[c]["properties"]["type"]
            if col_type == "pit":
                self.pit_properties.append(c)
            else:
                self.ts_properties.append(c)
                
        self.n_pit = len(self.pit_properties)
        self.n_ts = len(self.ts_properties)

        # Reformat data single into single row per region.
        # First n_prop columns are means (for pit it will be values themselves, for ts - yearly means),
        # followed by n_ts*n_ts giving covar matrix of time series properties
        # (matrix is symmetric, so wasting space but makes life easier)
        self._logger.info("Computing means/covars and reformatting ...")
        data_means = self.data.groupby(level='region').mean()
        #ts_means = self.data[self.ts_properties].groupby(level='region').mean()
        if self.n_ts > 0:
            covars = self.data[self.ts_properties].groupby(level='region').cov().unstack(level=1)
            self.data = np.concatenate([data_means.values,covars.values], axis=1)
        else:
            self.data = data_means.values
            
        ###################################
        # DistanceMetric allows only specific function signature (copy-pasted from docs):
        # Takes two one-dimensional numpy arrays, and returns a distance.
        # Note that in order to be used within the BallTree, the distance must be a true metric
        # i.e. it must satisfy the following properties
        # 1. Non-negativity: d(x, y) >= 0
        # 2. Identity: d(x, y) = 0 if and only if x == y
        # 3. Symmetry: d(x, y) = d(y, x)
        # 4. Triangle Inequality: d(x, y) + d(y, z) >= d(x, z)
        #
        # So define distance function here to have access to object members
        def dist_function(x,y):
            # means
            x_m = x[:self.n_pit+self.n_ts]
            y_m = y[:self.n_pit+self.n_ts]
            
            # Frechet (AKA 2-Wasserstein) distance between two distributions
            # first part is simply L2 between means, second is metric on the space of covar matrices
            # Cov matrices formally have zero col/rows corresponding to pit variables
            # these do not contribute to trace, but sqrtm might complain about singular matrices
            # so take only ts part
            # Note: this is inner loop, so maybe explore np.einsum()
            # but for now keep trace/dot/sum for better readability
            m_dist = np.sum((x_m-y_m)**2)
            s_dist = 0
            if self.n_ts > 0:
                # covar matrices (ts only, square n_ts x n_ts)
                x_cov = x[-self.n_ts*self.n_ts:].reshape(self.n_ts,-1)
                y_cov = y[-self.n_ts*self.n_ts:].reshape(self.n_ts,-1)                
                # can get negative due to numerical errors when x=y, so clamp to 0
                s_dist = max(0, np.trace( x_cov + y_cov - 2*sqrtm(x_cov.dot(y_cov)) ))
            return np.sqrt(m_dist + s_dist)
        
        # Finally construct ball tree with this distance
        self._logger.info("Constructing BallTrees...")
        self.metric_object = DistanceMetric.get_metric('pyfunc', **{'func':dist_function})
        self.ball = BallTree(self.data, metric=self.metric_object, leaf_size=2)
        self.balls_on_level = {}
        self.regions_on_level = {}
        # separate ball trees to process requests on givel level
        # shouldn't generally make separate data copies since region_id's are organized with countries < provinces < districts
        # so data for each level should be continuous arrays
        for level in [3,4,5]:
            self.regions_on_level[level] = [r for r in self.available_regions if self.region_info[r]['level']==level]
            level_data = self.data[[self.region_index[r] for r in self.regions_on_level[level]],:]
            self._logger.info(" level {}, {} regions".format(level, len(self.regions_on_level[level])))
            if level_data.size > 0:
                self.balls_on_level[level] = BallTree(level_data, metric=self.metric_object, leaf_size=2)
        self._logger.info("DONE")
        
    ##############################
    # Helper data loading method (single property, multiple regions)
    # regions in set of region_id's, prop_name is property name
    # to be used as a key for self.metric_properties
    def _load_property_for_regions(self, prop_name, regions, track_na=True):
        is_ts = self.metric_properties[prop_name]["properties"]["type"] == "timeseries"
        props = self.metric_properties[prop_name]
        query = props["api_data"]
        queries = []
        # list() to ensure the same sequence for np.array and for/in
        regions_list = list(regions) 
        #region_idx = np.array(regions_list)
        n_reg = len(regions_list)
        if n_reg == 0:
            return
        n_queries =  n_reg // REGIONS_PER_QUERY + (n_reg % REGIONS_PER_QUERY != 0)
        
        # deep copy d/l metric for each query.
        #for region in regions_list: 
        #    copy_of_metric = dict(query)
        #    copy_of_metric["region_id"] = region
        #    queries.append(copy_of_metric)
        qcounter = 0
        original_q = {}
        n_reg = 0 # will now re-count to actual number of regions to d/l
        for q in range(n_queries):
            # on "second chance" (track_na=False) just run everything
            if (not track_na) or (q not in self.processed_q):
                copy_of_metric = dict(query)
                # ok for last index to exeed list length min(n_reg, (q+1)*REGIONS_PER_QUERY) is used
                copy_of_metric["region_id"] = regions_list[q*REGIONS_PER_QUERY:(q+1)*REGIONS_PER_QUERY] 
                n_reg += len(copy_of_metric["region_id"])
                #print("requesting ", copy_of_metric["region_id"])
                queries.append(copy_of_metric)
                original_q[qcounter] = q
                qcounter += 1

        #********************
        # function to process API responce to given query
        # self.data should already have space allocated for all data
        def map_response(query_idx, _, response, *args):
            idx = original_q[query_idx] # true position in region_list as we might not be running full set of queries
            r_idx = regions_list[idx*REGIONS_PER_QUERY:(idx+1)*REGIONS_PER_QUERY]
            # if entire response is invalid, assume this query should probably be rerun
            # => don't add to processed list. Should pay attention to messages if None is legitimate (will repeat on resume)
            if (response is None) or (type(response) is BatchError) or (len(response) == 0):
                self._logger.info("Received None or BatchError as response to query {} for regions {} to {}".
                                  format(idx,r_idx[0],r_idx[-1]))
                if track_na:
                    # if we do NOT fail, these will be in to_retry, so will simply be retried once after main run is finished
                    # if we DO fail, these will be retried since corresponding query will not arrear in processed_q,
                    # and then again since they appear in to_retry list. Well, I guess it's ok
                    self.to_retry += r_idx
                    if is_ts:
                        np.savez_compressed(os.path.join(self.data_dir, prop_name+'.npz'),
                                    data = self.data,
                                    data_counters = self.data_counters,
                                    processed_q = self.processed_q,
                                    to_retry = self.to_retry)
                if type(response) is BatchError:
                    self._logger.info("received BatchError(response, retry_count, url, params): {}".format(response)) 
                return
            for r in r_idx:
                # try/exept to avoid crash on invalid data, just pass None to _fill_block to deal with it properly
                try:
                    resp = [{key:item[key] for key in ['start_date', 'end_date','value']} for item in response if item['region_id']==r]
                except:
                    resp = None
                self._fill_block(resp,prop_name,r,track_na) 
                load_bar.update()
                
            # finished processing of all regions in this query. Now save modified data, counts
            # and processed_q (after adding current query id) as a checkpoint (overwrites previous)
            # Note - writing checkpoints is expensive, so only do it for time series on every query
            # For pit data there will only be the first ("empty") checkpoint
            # Also, do not save anything during "second chance" run (track_na=False)
            if is_ts and track_na:
                self.processed_q.append(idx)
                np.savez_compressed(os.path.join(self.data_dir, prop_name+'.npz'),
                                    data = self.data,
                                    data_counters = self.data_counters,
                                    processed_q = self.processed_q,
                                    to_retry = self.to_retry)
            return

        #***********************

        self._logger.info("Getting data series for {} regions in {} queries for property {}".
                          format(n_reg, qcounter, prop_name))
        load_bar = tqdm(total=n_reg)
        # Sending out all queries    
        self.client.batch_async_get_data_points(queries, map_result=map_response)
        load_bar.close()
        return

    ###############################
    # fills corresponding block of self.data matrix from API response
    # returns True if actual data were received, False for empty/None response
    def _fill_block(self, response, prop_name, region_id, track_na=True):
        res = True
        if response is None or len(response) == 0 or (len(response) == 1 and response[0] == {}):
            # no data on this region/property. let's fill it with nan
            self._logger.info("Did not get any {} for region {}".format(prop_name,region_id))
            idx = self.region_index[region_id]*self.t_int_per_year
            self.data[idx:idx+self.t_int_per_year, self.prop_index[prop_name]] = np.nan
            if track_na:
                self.to_retry.append(region_id)
            res = False
        else:
            if self.metric_properties[prop_name]["properties"]["type"] == "timeseries":
                # compute monthly average from the response
                for datapoint in response:
                    # Dates are recieved as starting from YYYY-MM-DD
                    # (for example 'start_date': '2017-01-01T00:00:00.000Z')
                    # Let's "assign" the data point to the entire period
                    # (important for intervals longer than 365/t_int_per_year)
                    start_month = int(datapoint["start_date"][5:7])
                    end_month = int(datapoint["end_date"][5:7])
                    
                    # assignment is inclusive
                    v = datapoint["value"]
                    # nan's remain nan's, add to all others
                    #self.data.loc[(region_id,start_month):
                    #              (region_id,end_month), prop_name] += v
                    # if nan, this is first time there is a value - just fill it
                    #self.data.loc[(region_id,start_month):
                    #              (region_id,end_month), prop_name].fillna(v)
                    #self.data_counters.loc[(region_id,start_month), prop_name] += 1
                    
                    # No action on N/A
                    if v is not None:
                        idx = self.region_index[region_id]*self.t_int_per_year
                        prop_idx = self.prop_index[prop_name]
                        # ugly date conversion, but this is inner loop, strptime is too slow here
                        # TODO: python 3.7 has fromisoformat which is supposedly much faster than strptime
                        y = int(datapoint["start_date"][:4])
                        m = int(datapoint["start_date"][5:7])
                        d = int(datapoint["start_date"][8:10])
                        start_doy = date(y,m,d).timetuple()[-2]
                        #int(datetime.datetime.strptime(datapoint["start_date"][:10], '%Y-%m-%d').strftime('%j'))
                        y = int(datapoint["end_date"][:4])
                        m = int(datapoint["end_date"][5:7])
                        d = int(datapoint["end_date"][8:10])
                        end_doy = date(y,m,d).timetuple()[-2]
                        #int(datetime.datetime.strptime(datapoint["end_date"][:10], '%Y-%m-%d').strftime('%j'))
                        
                        # scale into [0,t_int_per_year] 
                        # intervals are INCLUSIVE of days stating their ends
                        # for 30.4-day interval, start_f=29/30.4 for day 30, 30/30.4 for day 31.
                        # but end_f = 30/30.4 for day 30. So single day 30 maps to [29,30]/30.4
                        # (fully inside interval 0) but 31 is partially split between intervals 0 and 1
                        # -1e-9 makes sure end boundary is strictly inside interval (also handles leap years)
                        start_f = (start_doy-1)/self.t_int_days
                        end_f = min(self.t_int_per_year-1e-9, end_doy/self.t_int_days)
                        (start_interval,start_fraction) = divmod(start_f,1)
                        (end_interval,end_fraction) = divmod(end_f,1)
                        start_interval = int(start_interval)
                        end_interval = int(end_interval)
                        start_fraction = 1-start_fraction
                        fractions = np.ones(end_interval-start_interval+1)
                        
                        if end_interval==start_interval:
                            # data point is fully inside an interval - only one interval affected
                            fractions[0]=start_fraction+end_fraction-1
                        elif end_interval>start_interval:
                            # end interval is later in the year than start (no crossing of year boundary)
                            fractions[0]=start_fraction
                            fractions[-1]=end_fraction
                        else:
                            # crossing year boundary - let's just ignore this point
                            continue
                        #print(region_id,v,start_interval, end_interval, fractions)
                        #self.data_counters[idx+start_interval, prop_idx] += start_fraction
                        #self.data_counters[idx+start_interval+1:idx+end_interval, prop_idx] += 1
                        self.data_counters[idx+start_interval:idx+end_interval+1, prop_idx] += fractions
                        self.data[idx+start_interval:idx+end_interval+1, prop_idx] += v*fractions
                        #self.data_counters[idx+end_interval, porp_idx] += end_fraction
                            
                            
                        """
                        if start_month==12 and end_month==1:
                            self.data[idx, prop_idx] +=v # Jan
                            self.data_counters[idx,prop_idx] +=1
                            self.data[idx+11, prop_idx] +=v # Dec
                            self.data_counters[idx+11,prop_idx] +=1
                        else: # normal case
                            # no -1 for end_month to ensure inclusive assignment
                            self.data[idx+start_month-1:idx+end_month, prop_idx] += v                    
                            self.data_counters[idx+start_month-1:idx+end_month, prop_idx] += 1
                        """
            elif self.metric_properties[prop_name]["properties"]["type"] == "pit":
                # for 'point in time' just add the same value across all months
                v =  response[0]["value"]
                # On None can assign np.nan immediately,
                # but let's keep uniformity with timeseries and take no action
                if v is None:
                    res = False
                else:
                    idx = self.region_index[region_id]*self.t_int_per_year
                    self.data[idx:idx+self.t_int_per_year, self.prop_index[prop_name]] = v
                    self.data_counters[idx:idx+self.t_int_per_year, self.prop_index[prop_name]] += 1
        return res
    
    def _regions_avail_for_selection(self, region_properties):
        regions = set()
        for props in region_properties.values():
            for available_series in self.client.list_available(props["api_data"]):
                regions.add(available_series["region_id"])
        self._logger.info("{} regions are available for comparison.".format(len(regions)))
        return list(regions)


    def _get_distances(self, idx1, idx2):
        """ Returns the distances in each "metric" for the two given rows
            Distances incorporate all aplied weighting
        """
        progress_idx = 0
        distances = []
        for properties in self.state.region_properties.values():
            num_features = properties["properties"]["num_features"]
            subspace_vec1 = self.state.data_standardized[idx1, progress_idx:progress_idx+num_features]
            subspace_vec2 = self.state.data_standardized[idx2, progress_idx:progress_idx+num_features]
            dist = euclidean_distances([subspace_vec1], [subspace_vec2])[0][0]
            distances.append(dist)
            progress_idx += num_features
        return distances

    def similar_to(self, region_id, number_of_regions=10, requested_level=None):
        """
        Attempt to look up the given name and find similar regions.
        :param region_id: a Gro region id representing the reference region you want to find similar regions to.
        :param number_of_regions: number of most similar matches to return
        :return: a generator of the most similar regions as a list in the form
        [{id: 123, name: "abc", distance: 1.23, parent_regions: []]
        """
        assert region_id in self.available_regions, "This region is not available in your configuration or it lacks coverage in the chosen region properties."
        
        # called when self.data is simple np.array
        # BallTree expects array of points but we always search neighbors of just one => reshape
        x = self.data[self.region_index[region_id]].reshape(1, -1)
        
        # distances and regions (as indexes into self.data)
        # Always use single lookup region - use [0] of the result
        if requested_level:
            ball = self.balls_on_level.get(requested_level)
            assert ball, "No region data on requested level {}".format(requested_level)
            idx_to_region = self.regions_on_level[requested_level]
        else:
            ball = self.ball
            idx_to_region = self.available_regions
        sim_dists, neighbour_idxs = ball.query(x, k = min(number_of_regions, self.num_regions))        
        sim_regions = [idx_to_region[i] for i in neighbour_idxs[0]]
        sim_dists = sim_dists[0]
        self._logger.info("Found {} regions most similar to '{}'.".format(len(sim_regions), region_id))
        
        for ranking, sr_id in enumerate(sim_regions):
            info = self.region_info[sr_id]
            
            # Choose parent one level up from this region
            parent_info = {"name": "", "id": ""}
            for r in info['belongsTo']:
                # in case there is no parent at correct level we will just take the last
                try:
                    parent_info = self.region_info[r] 
                    if parent_info['level'] == region_level-1:
                        break
                except:
                    continue
            
            # try to find grandparent in region info, just take the first id parent belongs to
            # this works ok for grandparents which are at least countries if parent on needed level was found
            try:
                gp_id = self.region_info[parent_info['id']]['belongsTo'][0]
                gp_info = self.region_info[gp_id]
            except:
                gp_info = {"name": "", "id": ""}
                    
            data_point = {"#": ranking,
                          "id": sr_id,
                          "name": info['name'],
                          "dist": sim_dists[ranking],
                          "parent": (parent_info["id"], parent_info["name"], gp_info["id"], gp_info["name"])}
            yield data_point
