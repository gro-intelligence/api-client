import math
from datetime import datetime
from functools import reduce
import tempfile
import numpy as np
import os
from tqdm import tqdm

import groclient.lib
from api.client.samples.similar_regions import transform

CACHE_PATH = "similar_region_state_cache"
# How much to weight the lowest weight feature.
# The features (coefficients for FFT) per metric will be weighted from 1.0 to LOWEST_PERCENTAGE_WEIGHT_FEATURE
LOWEST_PERCENTAGE_WEIGHT_FEATURE = 0.6

class SimilarRegionState(object):
    """
    Holds and initializes parameters and provide ssaving/loading logic for a similar_region search.
    """

    def __init__(self, region_properties, regions_to_compare, client, data_dir=None, no_download=False):
        self.client = client
        self._logger = groclient.lib.get_default_logger()

        # Figure out temporary directory
        if data_dir:
            self.data_dir = data_dir
        elif os.path.isdir(CACHE_PATH) and os.access(CACHE_PATH, os.W_OK):
            self.data_dir = CACHE_PATH
        else:
            self.data_dir = tempfile.gettempdir()

        self.region_properties = region_properties
        self.num_regions = len(regions_to_compare)
        self.num_properties = len(region_properties)
        self.tot_num_features = reduce(lambda acc, prop: acc + prop["properties"]["num_features"],
                                       region_properties.values(),
                                       0)

        # Mapping to and from our internal numpy idxs
        self.mapping = {region_idx:idx for (idx,region_idx) in enumerate(regions_to_compare)}
        self.inverse_mapping = np.array(regions_to_compare)

        # Data stores and views of this data
        structure = [(name, 'd', p["properties"]["num_features"]) for name, p in
                     region_properties.items()]
        
        # Numpy gives "future deprecation" warning about structured type specs of the form
        # (name,'d',1), i.e. where type is really just a single integer
        # Change such cases into (name,'d')
        structure = [item if item[2] != 1 else (item[0], item[1]) for item in structure]
        
        structure_bool = [(name, bool) for name, p in
                     region_properties.items()]
        self.data = np.ma.zeros(self.num_regions, dtype=structure)
        self.data[:] = np.ma.masked

        self._logger.debug("structure of data array entries is {}".format(structure))
        self._logger.debug("structure of missing array entries is {}".format(structure_bool))

        # Boolean array representing any data we haven't yet downloaded.
        # True if data for that (metric, region) has NOT been fetched into the data array.
        self.missing = np.full(self.num_regions, True, dtype=structure_bool)

        self._create_views()

        # Standardized (0-mean,1-std) version of data in a 2d array (without structure/masking nonsense)
        self.data_standardized = np.zeros((self.num_regions, self.tot_num_features), dtype='d')

        # Weights of each metric
        self.weight_vector = np.ones(self.tot_num_features, dtype='d')
        self._generate_weight_vector()

        self.load(no_download)
        # No modification to the cache if we did not even try to download anything
        if not no_download:
            self.save()

    def _create_views(self):
        self.data_nonstruc = self.data.view(
            dtype=[('data', 'd', (self.num_regions, self.tot_num_features))], type=np.ndarray
        )[0][0]
        self.data_mask_nonstruc = self.data.mask.view(dtype=(bool, self.tot_num_features))

    def save(self):
        """
        Cache the current state to disk.
        This is called AFTER _standardize which means
        all missing data already squeezed out of self.data, self.missing, and self.inverse_mapping
        Safe to simply augment cache with these if not already present
        :return: True if succeeded.
        """
        self._logger.info("Starting caching of downloaded data.")
        
        for name in self.region_properties:
            path = os.path.join(self.data_dir, "{}.nbz".format(name))
            if os.path.isfile(path):
                # we already have a cache => add new regions to it
                with open(path, 'rb') as f:
                    variables = np.load(f)
                    uncached_regions = set(self.inverse_mapping) - set(variables["inverse_mapping"])
                    if uncached_regions:
                        uncached_regions_idx = np.array([self.mapping[idx] for idx in uncached_regions])
                        full_data = np.append(variables["data"], self.data[name][uncached_regions_idx].data, axis=0)
                        full_mask = np.append(variables["mask"], self.data[name][uncached_regions_idx].mask, axis=0)
                        full_missing = np.append(variables["missing"], self.missing[name][uncached_regions_idx], axis=0)
                        full_inverse_mapping = np.append(variables["inverse_mapping"], self.inverse_mapping[uncached_regions_idx], axis=0)
                    else:
                        # no modifications to chache needed
                        continue
            else:
                # just cache entire (newly downloaded) dataset ...
                full_data = self.data[name].data
                full_mask = self.data[name].mask
                full_missing = self.missing[name]
                full_inverse_mapping = self.inverse_mapping
                
            with open(path, 'wb') as f:
                np.savez(f,
                         data=full_data, #self.data[name].data,
                         mask=full_mask, #self.data[name].mask,
                         missing=full_missing, #self.missing[name],
                         inverse_mapping=full_inverse_mapping) #self.inverse_mapping)
        self._logger.info("Done caching of downloaded data.")
        return

    def load(self, no_download):
        """
        Attempt to load any cached information and merge it into our current data situation.
        """
        self._logger.info("Loading data")
        # Loop through the metric views...
        for name in self.region_properties:
            path = os.path.join(self.data_dir, "{}.nbz".format(name))
            assert (not no_download) or os.path.isfile(path), "--no_download requires cached properties to be available" 
            if os.path.isfile(path):
                self._logger.info("Found cached data for {}, loading...".format(name))
                with open(path, 'rb') as f:
                    variables = np.load(f)
                    mutual_regions = set(variables["inverse_mapping"]) & set(self.inverse_mapping)
                    if mutual_regions:
                        # indexes of cached regions of interest in current data 
                        mutual_regions_mapping = np.array([self.mapping[idx] for idx in mutual_regions])
                        old_mapping = {region_idx:idx
                                       for (idx,region_idx) in enumerate(variables["inverse_mapping"])}
                        # indexes of cached regions of interest in cached data
                        mutual_regions_old_mapping = [old_mapping[idx] for idx in mutual_regions]
                        # copy from cached data to new data
                        self.data[name][mutual_regions_mapping] = variables["data"][mutual_regions_old_mapping]
                    
                        mutual_regions_masked = variables["mask"][mutual_regions_old_mapping]
                        self.data[name][mutual_regions_mapping][mutual_regions_masked] = np.ma.masked
                    
                        # cached regions of interest have data (missing=False) UNLESS
                        # they are marked as True in 'missing'
                        self.missing[name][mutual_regions_mapping] = False
                        mutual_regions_missing = variables["missing"][mutual_regions_old_mapping]
                        self.missing[name][mutual_regions_mapping[mutual_regions_missing]] = True
                self._logger.info("Loaded {} cached regions for property {}".format(len(mutual_regions), name))
            # Fill in the missing data if any e.g. in case the cache
            # was created with a subset of current regions_to_compare
            if not no_download:
                self._get_data(name)
        self._standardize()
        self._logger.info("Done loading.")
        return

    def _generate_weight_vector(self):
        # generate weight vector (with decreasing weights if enabled)
        # iterating over the dictionary is fine as we don't allow it
        # to be modified during runtime.  Distance between points is
        # p=2 weighted Minkowski distance, i.e. dist(x,y) = sqrt(\sum
        # [w_i(x_i - y_i)]^2) so sqrt of user-provided weight is taken
        # BEFORE individual property is scaled by its weight as it is
        # assumed user wants dist^2 = \sum w_user_i*(x_i - y_i)^2
        # (note user weight is NOT squared)
        #
        # Alternatively - do not rescale properties, just specify
        # 'wminkowski' metrics for BallTree constructor
        progress_idx = 0
        for properties in self.region_properties.values():
            num_features = properties["properties"]["num_features"]
            # User-provided weight is uniformly spread over
            # num_features (sum will be less for F-transformed
            # properties if weight_slope is requested
            weight_per_feature = (float(properties["properties"]["weight"])/num_features)**0.5
            if properties["properties"]["type"] == "timeseries_fourier" and properties["properties"]["weight_slope"]:
                slope_vector = np.arange(1.0, LOWEST_PERCENTAGE_WEIGHT_FEATURE,
                                         -(1.0 - LOWEST_PERCENTAGE_WEIGHT_FEATURE) / float(num_features))
                slope_vector *= weight_per_feature
                self.weight_vector[progress_idx:progress_idx+num_features] = slope_vector
            else:
                self.weight_vector[progress_idx:progress_idx + num_features] *= weight_per_feature
            progress_idx += num_features

    def _standardize(self):
        self._logger.info("Standardizing data matrix...")

        rows_to_keep = ~np.any(self.data_mask_nonstruc, axis=1)
        # Remove any rows that are missing....
        self.data = self.data[rows_to_keep]
        self.missing = self.missing[rows_to_keep]
        self.data_standardized = self.data_standardized[rows_to_keep]
        # Remove this from the region mapping
        self.inverse_mapping = self.inverse_mapping[rows_to_keep]
        # Recreate the mapping in other direction
        self.mapping.clear()
        for idx, region_idx in enumerate(self.inverse_mapping):
            self.mapping[region_idx] = idx
        # update the number of regions
        self.num_regions = len(self.inverse_mapping)

        # update nonstruc from data array
        self._create_views()

        # copy in from the nonstruc view
        np.copyto(self.data_standardized, self.data_nonstruc)
        mean = np.ma.average(self.data_nonstruc, axis=0)
        std = np.ma.std(self.data_nonstruc, axis=0)

        self._logger.debug("(mean, std) of data across regions axis are ({}, {})".format(mean, std))

        self.data_standardized -= mean
        self.data_standardized /= std
        self.data_standardized *= self.weight_vector

        # TODO: handle missing data properly.
        #https://math.stackexchange.com/questions/195245/average-distance-between-random-points-on-a-line-segment

        self._logger.info("Done standardizing data matrix.")
        return

    def _get_data(self, property_name):
        """Gets data for all regions for the given property and saves it to
        memory (and local cache on disk).
        """
        props = self.region_properties[property_name]
        query = props["selected_entities"]
        # Let's ask the server what times we have available and use those in post-processing.
        series_list = self.client.get_data_series(**query)
        assert len(series_list) > 0, "No data series found for selection {}".format(query)
        data_series = series_list[0]
        if props["properties"]["type"] == "timeseries_fourier":
            start_date = datetime.strptime(data_series["start_date"], '%Y-%m-%dT%H:%M:%S.%fZ')
            period_length_days = self.client.lookup('frequencies', query["frequency_id"])['periodLength']['days']
            end_date = datetime.strptime(data_series["end_date"], '%Y-%m-%dT%H:%M:%S.%fZ')
            num_of_points = (end_date - start_date).days / period_length_days
            self._logger.info("length of data series is {} periodLengths (per frequency_id)".format(num_of_points))
            longest_period_feature_period = props["properties"]["longest_period_feature_period"]
            start_idx = math.floor(num_of_points / float(longest_period_feature_period))
            self._logger.info("first coef index will be {}".format(start_idx))
        num_features = props["properties"]["num_features"]
        # deep copy the metric for each query.
        queries = []
        map_query_to_data_table = []
        for region in self.inverse_mapping[self.missing[property_name]]:
            copy_of_metric = dict(query)
            copy_of_metric["region_id"] = region
            queries.append(copy_of_metric)
            map_query_to_data_table.append(self.mapping[region])

        load_bar = tqdm(total=len(queries))

        def map_response(idx, _, response, *args):
            data_table_idx = map_query_to_data_table[idx]
            if response is None or len(response) == 0 or (len(response) == 1 and response[0] == {}):
                # no data on this region. let's fill it with zeros for the odd cases and mark it for masking.
                self.data[property_name][data_table_idx] = 0.0
                # flag this as invalid.
                self.data[property_name][data_table_idx] = np.ma.masked
            else:
                if props["properties"]["type"] == "timeseries_fourier":
                    # TODO: remove start_datetime stuff here once we have "addNulls" available in api
                    result, coverage = transform.post_process_timeseries(num_of_points, start_date, response,
                                                                         start_idx, num_features,
                                                                         period_length_days=period_length_days)
                    # if there are less points than there are in our lowest period event, let's discard this...
                    if coverage < 1/float(start_idx):
                        self.data[property_name][data_table_idx] = 0.0
                        # flag this as invalid.
                        self.data[property_name][data_table_idx] = np.ma.masked
                    else:
                        self.data[property_name][data_table_idx] = result
                elif props["properties"]["type"] == "pit":
                    # for point in time just add the value
                    if response[0]["value"] is None or np.isnan(response[0]["value"]):
                        self.data[property_name][data_table_idx] = np.ma.masked
                    else:
                        self.data[property_name][data_table_idx] = response[0]["value"]
            # Mark this as downloaded.
            self.missing[property_name][data_table_idx] = False
            load_bar.update()

        self._logger.info("Getting data series for {} regions for property {}".format(len(queries), property_name))
        self.client.batch_async_get_data_points(queries, map_result=map_response)
        load_bar.close()
        return


