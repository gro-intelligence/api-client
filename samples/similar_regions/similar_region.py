import csv
import math
import numpy as np
import os
from datetime import time, datetime
import dateparser
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

class SimilarRegion(BatchClient):

    def __init__(self, region_properties, regions_to_compare=None):
        """
        :param region_properties: A dict containing the properties of regions to use when doing the similarity
        computation. This is by default defined in region_properties.py, but can be adjusted.
        :param regions_to_compare: Default is None. This is a list of region IDs against which we want to do the
        similarity computation. If none specified, do this for all regions where we have _any_ data.
        """

        super(SimilarRegion, self).__init__(API_HOST, ACCESS_TOKEN)
        self._logger = get_default_logger("SimilarRegion")

        if regions_to_compare is None:
            regions_to_compare = self._regions_avail_for_selection(region_properties)

        self.state = SimilarRegionState(region_properties, regions_to_compare)
        self._generate_weight_vector(region_properties)

        return

    def _regions_avail_for_selection(self, region_properties):
        regions = set()
        for props in region_properties.values():
            regions |= set([item["region_id"] for item in self.list_available(props["query"])])
        self._logger.info("{} regions are available for comparison.".format(len(regions)))
        return list(regions)

    def _generate_weight_vector(self, region_properties):
        # generate weight vector (with decreasing weights if enabled)
        # iterating over the dictionary is fine as we don't allow it to be modified during runtime.
        progress_idx = 0

        for properties in region_properties.values():
            num_features = properties["properties"]["num_features"]
            slope_vector = np.arange(1.0,
                                     LOWEST_PERCENTAGE_WEIGHT_FEATURE,
                                     -(1.0 - LOWEST_PERCENTAGE_WEIGHT_FEATURE) / float(num_features))
            slope_vector *= properties["properties"]["weight"]
            self.state.weight_vector[progress_idx:progress_idx+num_features] = slope_vector
            progress_idx += num_features

    def _format_results(self, region_id, neighbours, requested_level, csv_output, dists):

        if csv_output:
            level_suffix = "" if requested_level is None else "_level_" + str(requested_level)
            f = open("output/" + str(region_id) + level_suffix + ".csv", 'wb')
            csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        similar_to_return = []

        for ranking, neighbour_id in enumerate(neighbours):

            district_id = self.state.inverse_mapping[neighbour_id]

            if np.ma.is_masked(self.state.data_nonstruc[neighbour_id]):
                self._logger.info("possible neighbour was masked")

            neighbour_region = self.lookup("regions", district_id)

            district_name = self.lookup("regions", district_id)["name"]

            if requested_level is not None and neighbour_region["level"] != requested_level:
                self._logger.info("not level %s %s" % (requested_level, district_name))
                continue

            district_name = self.lookup("regions", district_id)["name"]

            province = next(self.lookup_belongs("regions", district_id), {"name": ""})

            if "id" in province and province["id"] != 0:
                country = next(self.lookup_belongs("regions", province["id"]), {"name": "", "id": ""})
            else:
                country = {"name": "", "id": ""}

            output = [district_name, province["name"], country["name"]]
            output = [unicode(s).encode("utf-8") for s in output]

            self._logger.info("{}, {}, {}".format(district_name, province["name"], country["name"]))
            data_point = {"id": district_id, "name": district_name, "dist": dists[ranking],
                          "parent": (province["id"], province["name"], country["id"], country["name"])}

            similar_to_return.append(data_point)

            if csv_output:
                csv_writer.writerow(output)

        return similar_to_return

    def _similar_to(self, region_id, number_of_regions):
        """
        This gives us the regions that are most similar to the either the given region in the case on region is give, or
        similar to the "collective mean" of the regions as given.
        :param region_ids:
        :return: regions that are most similar to the given region id(s)
        """

        assert region_id in self.state.mapping, "This region is not available in your configuration."

        # list as an index to preserve dimensionality of returned data
        x = self.state.data_standardized[self.state.mapping[region_id], :]
        x = x.reshape(1, -1)
        neighbour_dists, neighbour_idxs = self.state.ball.query(x, k=number_of_regions)

        return neighbour_idxs[0], neighbour_dists[0]

    def _compute_similarity_matrix(self):
        """
        Compute and cache the similarity matrix/ball tree from the standardized data.
        :return: None. Modifies property "sim_matrix"
        """

        # Ensure we are standardized
        self._standardize()

        # Compute a ball tree (this is quicker than expected)
        self._logger.info("BallTree: computing")
        self.state.ball = BallTree(self.state.data_standardized, leaf_size=2)
        self._logger.info("BallTree: done")

        self.state.recompute = False

        return

    def _standardize(self):

        self._logger.info("standardizing data matrix")

        # make a view, then copy from that view...
        np.copyto(self.state.data_standardized, self.state.data_nonstruc)

        mean = np.ma.average(self.state.data_standardized, axis=0)
        std = np.ma.std(self.state.data_standardized, axis=0)

        self._logger.debug("(mean, std) of data across regions axis are ({}, {})".format(mean, std))

        self.state.data_standardized -= mean
        self.state.data_standardized /= std

        self.state.data_standardized *= self.state.weight_vector

        # As it turns out we should place all our masked values at the mean points for that column !!!
        # this ensures they are treated fairly despite missing a portion of the data.

        # # from https://stackoverflow.com/questions/5564098/repeat-numpy-array-without-replicating-data
        # view_of_data_means = np.lib.stride_tricks.as_strided(self.state.data_mean,
        #                                                      (1000, self.state.data_mean.size),
        #                                                      (0, self.state.data_mean.itemsize))
        #
        # += view_of_data_means[self.state.data.mask]

        # Center all of these I suppose is the most straightforward solution for now.
        # TODO: handle missing data properly.
        #https://math.stackexchange.com/questions/195245/average-distance-between-random-points-on-a-line-segment

        self.state.data_standardized[self.state.data_mask_nonstruc] = 100000.0

        self._logger.info("done standardizing data matrix")

        return

    def _cache_regions(self):
        """
        Saves the request metrics for all regions to memory (and possibly to disk). I can't see a better way to
        achieve this than downloading the required data on all the 5000 regions ...
        :return:
        """

        for name, props in self.state.region_properties.items():

            query = props["query"]

            self._logger.info("about to download dataseries for metric {}".format(name))

            # Let's ask the server what times we have available and use those in post-processing.
            data_series = self.get_data_series(**query)[0]
            start_date = dateparser.parse(data_series["start_date"])
            start_datetime = datetime.combine(start_date, time())
            period_length_days = self.lookup('frequencies', query["frequency_id"])['periodLength']['days']
            end_date = dateparser.parse(data_series["end_date"])
            no_of_points = (end_date - start_date).days / period_length_days
            self._logger.info("length of data series is {} days".format(no_of_points))
            longest_period_feature_period = props["properties"]["longest_period_feature_period"]
            start_idx = math.floor(no_of_points / float(longest_period_feature_period))
            self._logger.info("first coef index will be {}".format(start_idx))
            num_features = props["properties"]["num_features"]

            # deep copy the metric for each query.
            queries = []
            map_query_to_data_table = []

            for region in self.state.inverse_mapping[self.state.missing[name]]:
                copy_of_metric = dict(query)
                copy_of_metric["region_id"] = region
                queries.append(copy_of_metric)
                map_query_to_data_table.append(self.state.mapping[region])

            def map_response(idx, _, response):
                data_table_idx = map_query_to_data_table[idx]
                save_counter = when_to_save_counter

                if response is None or len(response) == 0 or (len(response) == 1 and response[0] == {}):
                    # no data on this region. let's fill it with zeros for the odd cases and mark it for masking.
                    self.state.data[name][data_table_idx] = 0.0
                    # flag this as invalid.
                    self.state.data[name][data_table_idx] = np.ma.masked
                else:
                    # TODO: remove start_datetime stuff here once we have "addNulls" on the server
                    result, coverage = transform.post_process_timeseries(no_of_points, start_datetime, response,
                                                                          start_idx, num_features,
                                                                          period_length_days=period_length_days)

                    # if there are less points than there are in our lowest period event, let's discard this...
                    if coverage < 1/float(start_idx):
                        self.state.data[name][data_table_idx] = 0.0
                        # flag this as invalid.
                        self.state.data[name][data_table_idx] = np.ma.masked
                    else:
                        self.state.data[name][data_table_idx] = result

                # Mark this as downloaded.
                self.state.missing[name][data_table_idx] = False
                save_counter[0] += 1

                # Save this every 10,000 items downloaded.
                if save_counter[0] % 10000 == 0:
                    self._logger.info("Saving data downloaded so far.")
                    self.state.save()

            when_to_save_counter = [0]

            self.batch_async_get_data_points(queries, map_result=map_response)

        self.state.downloaded = True

        self.state.save()

        return

    def similar_to(self, region_id, number_of_regions=10, requested_level=None, csv_output=False, search_regions=None):
        """
        Attempt to look up the given name and find similar regions.
        :param region_id: name of a region.
        :param number_of_regions: number of similar regions to return in the ranked list.
        :param search_regions: the regions to look for neighbours in. specified as a plaintext name
        :return: the closest neighbours as a list in the form
        [{id: 123, name: "abc", distance: 1.23, parent_regions: [{"abc"456, 789]
        """

        if np.any(self.state.missing_nonstruc):
            self._cache_regions()

        assert not np.any(self.state.missing_nonstruc)

        if self.state.recompute:
            self._logger.info("similarities not computed (or reloaded from disk and not saved), computing.")
            self._compute_similarity_matrix()

        # if search_regions:
        #     # TODO: fix search regions
        #     search_regions = []
        #
        # Check if search region is contained in available regions
        # if set(search_regions) not in self.state.known_regions:
        #     raise Exception("Requested region(s) are not downloaded. Please call cache_regions()")

        neighbours, dists = self._similar_to(region_id, number_of_regions)

        self._logger.info("nearest regions to '{}' are: {}".format(region_id, neighbours))

        return self._format_results(region_id, neighbours, requested_level, csv_output, dists)
