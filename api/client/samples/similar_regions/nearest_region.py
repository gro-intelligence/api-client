import csv
import math
from Queue import Queue
import numpy as np
import os
from datetime import time, datetime
import dateparser
import cPickle as pickle
from sklearn.neighbors import BallTree
import transform
from api.client import BatchClient
from api.client.lib import get_default_logger
from similar_region_state import SimilarRegionState

""" API Config """
API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

# How much to weight the lowest weight feature.
# The features (coefficients for FFT) per metric will be weighted from 1.0 to LOWEST_PERCENTAGE_WEIGHT_FEATURE
LOWEST_PERCENTAGE_WEIGHT_FEATURE = 0.6

# Frequencies are hardcoded for the time being as a function days.
frequencies = {
    1: 1,
    2: 7
}

class SimilarRegion(BatchClient):

    def __init__(self, metrics_to_use, precache_regions="ALL", weights=None, time_frame=None):
        """
        Metr
        :param metrics_to_use: A dictionary of {"metric_name": {"query": ...}, ...}
        :param weights: A ndictionary of the weights to associate with each metric/itemID pair. For instance, if soil
        weight is extremely important. NOTE: weights will be normalized with a softmax! TODO:done
        :param time_frame: How long to average these values over. For instance weather conditions. TODO
        """

        super(SimilarRegion, self).__init__(API_HOST, ACCESS_TOKEN)
        self._logger = get_default_logger()
        self.state = SimilarRegionState()

        # Metrics we have implemented
        # item metric pair
        self.available_metrics = {
            "soil_moisture": {
                "query": {
                    'metric_id': 15531082,
                    'item_id': 7382,
                    'frequency_id': 1,
                    'source_id': 43
                },
                "properties": {
                    "num_features": 150,
                    "longest_period_feature_period": 365
                }
            },
            "land_surface_temperature": {
                "query": {
                    'metric_id': 2540047,
                    'item_id': 3457,
                    'frequency_id': 1,
                    'source_id': 26
                },
                "properties": {
                    "num_features": 150,
                    "longest_period_feature_period": 365
                }
            },
            "rainfall": {
                "query": {
                    'metric_id': 2100031,
                    'item_id': 2039,
                    'frequency_id': 1,
                    'source_id': 35
                },
                "properties": {
                    "num_features": 150,
                    "longest_period_feature_period": 365
                }
            }
        }

        # See which regions we wan't to compute over.
        if precache_regions == "ALL":
            # Upper limit on number of districts as we are working on district level. We will mask unused ones.
            num_regions = 50000
            self.state.known_regions = set()
            self.state.all_regions = True
        else:
            num_regions = len(precache_regions)
            self.state.known_regions = set(precache_regions)
            for region in precache_regions:
                self.state.row_idx_to_district.append(region)
                self.state.district_to_row_idx[region] = len(self.state.row_idx_to_district) - 1

        # Our data store. let's set this to be the correct size, then make corresponding views for each subarray.
        self.state.data = np.ma.masked_array(np.zeros((num_regions, 0)))
        self.state.not_fetched_yet = np.full((num_regions, 0), True)

        for metric_name in metrics_to_use:
            self._add_metric(metric_name)

        return

    def similar_to(self, name, number_of_regions=10, requested_level=None, csv_output=False, search_regions=None):
        """
        Attempt to look up the given name and find similar regions.
        :param name: name of a region.
        :param number_of_regions: number of similar regions to return in the ranked list.
        :param search_regions: the regions to look for neighbours in. specified as a plaintext name
        :return: the closest neighbours as a list in the form
        [{id: 123, name: "abc", distance: 1.23, parent_regions: [{"abc"456, 789]
        """

        # Check if we are ready
        # if not self.state.downloaded:
        #     raise Exception("Region data not available. Please call cache_regions()")

        if self.state.recompute:
            self._logger.info("Similarities not computed (or reloaded from disk and not saved), computing.")
            self._compute_similarity_matrix()

        # if search_regions:
        #     # TODO: fix search regions
        #     search_regions = []
        #
        # # Check if search region is contained in available regions
        # if set(search_regions) not in self.state.known_regions:
        #     raise Exception("Requested region(s) are not downloaded. Please call cache_regions()")
        if type(name) == int:
            possible_region = {}
            possible_region["id"] = name
        else:
            possible_region = next(self.search_and_lookup("regions", name), False)

            while possible_region and possible_region["level"] != 5:
                possible_region = next(self.search_and_lookup("regions", name), False)

            if not possible_region:
                print("NearestRegionsApp: Region '%s' not found in Gro database." % name)
                return

            print(possible_region)

        if csv_output:
            level_suffix = "" if not requested_level else "_level_" + str(requested_level)
            f = open("output/" + str(possible_region["id"]) + level_suffix + ".csv", 'wb')
            csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        neighbours, dists = self._similar_to(possible_region["id"], number_of_regions)

        print("NearestRegionsApp: Nearest regions to '%s' are:" % name)
        print(neighbours)

        similar_to_return = []

        for ranking, neighbour_id in enumerate(neighbours):
            print(neighbour_id)
            # try:
            district_id = self.state.row_idx_to_district[neighbour_id]

            if np.ma.is_masked(self.state.data[neighbour_id]):
                self._logger.info("possible neighbour was masked")

            neighbour_region = self.lookup("regions", district_id)
            print(1)

            district_name = self.lookup("regions", district_id)["name"]

            if neighbour_region["level"] != requested_level:
               self._logger.info("not level %s %s" % (requested_level, district_name))
               continue
            print(2)
            district_name = self.lookup("regions", district_id)["name"]
            print(3)
            province = next(self.lookup_belongs("regions", district_id), {"name": ""})
            print(4)
            if "id" in province and province["id"] != 0:
                country = next(self.lookup_belongs("regions", province["id"]), {"name": "", "id": ""})
            else:
                country = {"name": "", "id" : ""}

            output = [district_name, province["name"], country["name"]]
            output = [unicode(s).encode("utf-8") for s in output]

            print("%s, %s, %s" % (district_name, province["name"], country["name"]))
            data_point = {"id": district_id, "name": district_name, "dist": dists[ranking],
                          "parent": (province["id"], province["name"], country["id"], country["name"])}

            similar_to_return.append(data_point)

            if csv_output:
                csv_writer.writerow(output)

        return similar_to_return
        # except Exception as e:
        #     print(e)
        #     print("something broke ?")

    def _similar_to(self, region_id, number_of_regions):
        """
        This gives us the regions that are most similar to the either the given region in the case on region is give, or
        similar to the "collective mean" of the regions as given.
        :param region_ids:
        :return: regions that are most similar to the given region id(s)
        """

        if region_id not in self.state.known_regions:
            raise Exception("Not trained on this region. Please add it.")
            return

        # list as an index to preserve dimensionality of returned data
        x = self.state.data_standardized[self.state.district_to_row_idx[region_id], :]
        x = x.reshape(1, -1)
        print(x)
        print(self.state.district_to_row_idx[region_id])
        neighbour_dists, neighbour_idxs = self.state.ball.query(x, k=number_of_regions)
        #
        # # see that these are actually districts. get their names.
        # for neighbour_idxs:

        return neighbour_idxs[0], neighbour_dists[0]

    def _compute_similarity_matrix(self):
        """
        Cache and compute the similarity matrix from the cached region metrics
        :return: None. Modifies property "sim_matrix"
        """

        # Ensure we are standardized
        self._standardize()

        # Compute a ball tree (this is quick)
        self._logger.info("BallTree: computing")
        self.state.ball = BallTree(self.state.data_standardized, leaf_size=2)
        self._logger.info("BallTree: done")

        self.state.recompute = False

        return

    def _standardize(self):

        if self.state.recompute:
            self._logger.info("Standardizing data matrix")

            self.state.data_standardized = np.ma.array(self.state.data, copy=True)

            mean = np.ma.average(self.state.data_standardized, axis=0)
            std = np.ma.std(self.state.data_standardized, axis=0)
            self.state.data_standardized = (self.state.data_standardized - mean) / std

            for metric_name in self.state.metrics_to_use:
                starting_col = self.state.metric_to_col_idx[metric_name]
                ending_col = starting_col + self.available_metrics[metric_name]["properties"]["num_features"]
                self.state.data_standardized[:, starting_col:ending_col] *= self.state.metric_weights[metric_name]
                # weight higher frequency information less!
                num_features = self.available_metrics[metric_name]["properties"]["num_features"]
                weight_vector = np.arange(1.0,
                                          LOWEST_PERCENTAGE_WEIGHT_FEATURE,
                                          -(1.0-LOWEST_PERCENTAGE_WEIGHT_FEATURE)/float(num_features))
                self.state.data_standardized[:, starting_col:ending_col] *= weight_vector

            # As it turns out we should place all our masked values at the mean points for that column !!!
            # this ensures they are treated fairly despite missing a portion of the data.

            # # from https://stackoverflow.com/questions/5564098/repeat-numpy-array-without-replicating-data
            # view_of_data_means = np.lib.stride_tricks.as_strided(self.state.data_mean,
            #                                                      (1000, self.state.data_mean.size),
            #                                                      (0, self.state.data_mean.itemsize))
            #
            # += view_of_data_means[self.state.data.mask]

            # Center all of these I suppose is the most straightforward solution...
            self.state.data_standardized[self.state.data.mask] = 100000.0

            self._logger.info("Standardized data matrix")
        else:
            self._logger.info("Already standardized. Not doing it again.")

        return

    def _add_regions(self, regions_to_add):

        self.state.recompute = True

        new_regions = regions_to_add - self.state.known_regions

        for region in new_regions:
            self.state.row_idx_to_district.append(region)
            self.state.district_to_row_idx[region] = len(self.state.row_idx_to_district) - 1

        self.state.known_regions |= new_regions

    def add_metric(self, metric_name, weight=1.0):
        """
        Public interface for internal function.
        :param metric_name:
        :return:
        """
        self._add_metric(metric_name)

    def _add_metric(self, metric_name, weight=1.0):
        """
        Add a metric! This is inherently expensive because we to in-memory-copy the array.
        :param metric_name:
        :return:
        """

        self._logger.info("Adding metric %s" % metric_name)

        self.state.recompute = True

        if type(metric_name) != list:
            metrics = [metric_name]
        else:
            metrics = metric_name

        if type(weight) != list:
            weights = [weight] * len(metrics)
        else:
            assert(len(weight) == len(metrics))
            weights = weight

        for idx, metric_name in enumerate(metrics):
            if metric_name not in self.available_metrics:
                raise Exception("Metric %s not found. Please provide a valid metric." % metric_name)
                continue

            if metric_name in self.state.metrics_to_use:
                self._logger.info("Metric %s already added. Not adding again. Call _cache_regions() "
                                  "to finish downloading data." % metric_name)
                continue

            num_features = self.available_metrics[metric_name]["properties"]["num_features"]
            start_idx = self.state.data.shape[1]
            self.state.metric_to_col_idx[metric_name] = start_idx
            end_idx = start_idx + num_features

            #reshape data matrix
            old_data_array = self.state.data
            self.state.data = np.ma.zeros((self.state.data.shape[0], self.state.data.shape[1] + num_features))
            self.state.data[:, 0:old_data_array.shape[1]] = old_data_array
            self.state.data[:, start_idx:end_idx] = np.ma.masked

            #add it to metrics to use
            self.state.metrics_to_use.append(metric_name)

            #reshape the download status matrix
            old_state_array = self.state.not_fetched_yet
            self.state.not_fetched_yet = np.full((self.state.data.shape[0], self.state.not_fetched_yet.shape[1] + 1), True)
            self.state.not_fetched_yet[:, 0:old_state_array.shape[1]] = old_state_array
            self.state.not_fetched_yet[:, -1:] = True

            self._set_metric_weight(metric_name, weights[idx])

            self._logger.info("Added metric %s" % metric_name)

        # re-add those metrics
        self.state._construct_metric_data_views()

        return True

    def _set_metric_weight(self, metric_name, weight):

        assert 0.0 <= weight <= 1.0
        self.state.metric_weights[metric_name] = weight

    def _cache_regions(self):
        """
        Saves the request metrics for all regions to memory (and possibly to disk). I can't see a better way to
        achieve this than downloading the required data on all the 5000 regions ...
        :return:
        """

        for metric_idx, metric_name in enumerate(self.state.metrics_to_use):

            metric = self.available_metrics[metric_name]["query"]

            # let's see which data series are available with region being the free variable
            available_series_and_regions = self.list_available({"itemId": metric["item_id"], "metricId": metric["metric_id"]})

            available_regions_for_metric = set([row["region_id"] for row in available_series_and_regions])

            if self.state.all_regions:
                self._add_regions(available_regions_for_metric)

            idxs_to_download = np.argwhere(self.state.not_fetched_yet[:, metric_idx] == True)[:, 0]
            to_download_regions = set(self.state.row_idx_to_district[idx] for idx in idxs_to_download if
                                      idx < len(self.state.row_idx_to_district))

            search_regions = self.state.known_regions & available_regions_for_metric & to_download_regions

            if len(search_regions) == 0:
                self._logger.info("Already downloaded metric %s for all requested regions" % metric_name)
                continue

            self._logger.info("About to download dataseries for %i regions for metric %s" %
                              (len(search_regions), metric_name))

            # Let's ask the server what times we have available and use those in post-processing.
            data_series = self.get_data_series(**metric)[0]
            start_date = dateparser.parse(data_series["start_date"])
            start_datetime = datetime.combine(start_date, time())
            period_length_days = frequencies[metric["frequency_id"]]
            end_date = dateparser.parse(data_series["end_date"])
            no_of_points = (end_date - start_date).days / period_length_days
            self._logger.info("Length of data series is %i days" % no_of_points)
            longest_period_feature_period = self.available_metrics[metric_name]["properties"]["longest_period_feature_period"]
            start_idx = math.floor(no_of_points / float(longest_period_feature_period))
            self._logger.info("First coef index will be %i" % start_idx)
            num_features = self.available_metrics[metric_name]["properties"]["num_features"]

            # deep copy the metric for each query.
            queries = []
            map_query_to_data_table = []
            for region in search_regions:
                copy_of_metric = dict(metric)
                copy_of_metric["region_id"] = region
                queries.append(copy_of_metric)
                map_query_to_data_table.append(self.state.district_to_row_idx[region])

            #TO DO: REMOVE THIS
            #queries = queries[0:100]

            def map_response(idx, query, response):
                data_table_idx = map_query_to_data_table[idx]
                data = self.state.metric_data[metric_name]
                needs_to_be_downloaded_state = self.state.not_fetched_yet
                save_counter = when_to_save_counter
                save_func = self.state.save

                if response is None or len(response) == 0 or (len(response) == 1 and response[0] == {}):
                    # no data on this region. let's fill it with zeros for the odd cases and mark it for masking.
                    data[data_table_idx] = [0] * data.shape[1]
                    # flag this as invalid.
                    data[data_table_idx, :] = np.ma.masked
                else:
                    # TODO remove out_scope start_datetime here once we have "addNulls" on the server
                    result, coverage = transform._post_process_timeseries(no_of_points, start_datetime, response,
                                                                          start_idx, num_features,
                                                                          period_length_days=period_length_days)
                    # if there are less points than there are in our lowest period event, let's discard this...
                    if coverage < 1/float(start_idx):
                        data[data_table_idx] = [0] * data.shape[1]
                        # flag this as invalid.
                        data[data_table_idx, :] = np.ma.masked
                    else:
                        data[data_table_idx] = result

                # Mark this as downloaded.
                needs_to_be_downloaded_state[data_table_idx, metric_idx] = False
                save_counter[0] += 1

                # Save this every 10,000 items downloaded.
                if save_counter[0] % 10000 == 0:
                    self._logger.info("Saving data downloaded so far.")
                    save_func()

            when_to_save_counter = [0]

            self.batch_async_get_data_points(queries, map_result=map_response)

        self.state.downloaded = True

        self.state.save()

        return

    def _get_districts(self, canonical_name):
        """
        Given a canonical region name (e.g. "russia"), returns all districts in this area or an empty list if an
        invalid name is passed or a sub-district level name is passed.
        :param canonical_name: Name of region whose districts we want.
        :return:
        """
        districts = []

        if type(canonical_name) != list:
            canonical_name = [canonical_name]

        for canonical_name in canonical_name:
            requested_region = next(self.search_and_lookup("regions", canonical_name), None)

            if not requested_region:
                return []

            # Do this as a breadth first search to make use of our nice async library.
            queue = []

            for region_id in requested_region["contains"]:
                queue.append(region_id)

            while len(queue) != 0:

                # Let's get all of these at once :)
                results = [0]*len(queue)
                entities = [(idx, ("regions", entity_id)) for (idx, entity_id) in enumerate(queue)]

                self.batch_async_lookup(entities, output_list=results)

                queue = []

                for region in results:
                    if region["level"] == 5:
                        districts.append(region["id"])
                    else:
                        queue += region["contains"]

        return districts

    def main(self):
        pass

if __name__ == "__main__":

    # If you're running the first time, run these three lines. Alternatively download the pre-computed version from
    # here:
    testCase = SimilarRegion(["rainfall", "soil_moisture", "land_surface_temperature"])

    #testCase.state.load()
    testCase._cache_regions()
    #
    # # Otherwise, comment the three lines above and uncomment this line
    #
    # # If you want to modify weights, uncomment below
    testCase.state.metric_weights = {
        "soil_moisture": 1.0,
        "rainfall": 1.0,
        "land_surface_temperature": 1.0
    }
    # #
    print(testCase.state.data[0:100])
    #testCase.similar_to(13172, number_of_regions=150, requested_level=5, csv_output=True)
