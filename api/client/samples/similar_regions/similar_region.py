import numpy as np
import os
from sklearn.neighbors import BallTree
from api.client.batch_client import BatchClient
from api.client.lib import get_default_logger
from similar_region_state import SimilarRegionState

""" API Config """
API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

class SimilarRegion(BatchClient):

    def __init__(self, region_properties, regions_to_compare=None):
        """
        :param region_properties: A dict containing the properties of regions to use when doing the similarity
        computation. This is by default defined in region_properties.py, but can be adjusted.
        :param regions_to_compare: Default is None. This is a list of region IDs against which we want to do the
        similarity computation. If none specified, do this for all regions where we have _any_ data.
        """

        super(SimilarRegion, self).__init__(API_HOST, ACCESS_TOKEN)
        self._logger = get_default_logger()#"SimilarRegion"

        if not regions_to_compare:
            regions_to_compare = self._regions_avail_for_selection(region_properties)

        self.state = SimilarRegionState(region_properties, regions_to_compare)
        return

    def _regions_avail_for_selection(self, region_properties):
        regions = set()
        for props in region_properties.values():
            for available_series in self.list_available(props["selected_entities"]):
                regions.add(available_series["region_id"])
        self._logger.info("{} regions are available for comparison.".format(len(regions)))
        return list(regions)

    def _format_results(self, neighbours, requested_level, dists):

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

            self._logger.info("{}, {}, {}".format(district_name, province["name"], country["name"]))
            data_point = {"id": district_id, "name": district_name, "dist": dists[ranking],
                          "parent": (province["id"], province["name"], country["id"], country["name"])}

            yield data_point

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

        for output in self._format_results(region_id, neighbours, requested_level, csv_output, dists):
            yield output
