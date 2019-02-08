import numpy as np
import os
from sklearn.neighbors import BallTree
from api.client.batch_client import BatchClient
from api.client.lib import get_default_logger
from similar_region_state import SimilarRegionState

""" API Config """
API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

class SimilarRegion(object):

    def __init__(self, region_properties, regions_to_compare=None):
        """
        :param region_properties: A dict containing the properties of regions to use when doing the similarity
        computation. This is by default defined in region_properties.py, but can be adjusted.
        :param regions_to_compare: Default is None. This is a list of region IDs against which we want to do the
        similarity computation. If none specified, do this for all regions where we have _any_ data.
        """
        self.client = BatchClient(API_HOST, ACCESS_TOKEN)
        self._logger = get_default_logger()
        if not regions_to_compare:
            regions_to_compare = self._regions_avail_for_selection(region_properties)
        self.state = SimilarRegionState(region_properties, regions_to_compare, self.client)
        return

    def _regions_avail_for_selection(self, region_properties):
        regions = set()
        for props in region_properties.values():
            for available_series in self.list_available(props["selected_entities"]):
                regions.add(available_series["region_id"])
        self._logger.info("{} regions are available for comparison.".format(len(regions)))
        return list(regions)

    def _format_results(self, neighbours, region_level_id, dists):
        for ranking, idx in enumerate(neighbours):
            neighbour_region_id = self.state.inverse_mapping[idx]
            if np.ma.is_masked(self.state.data_nonstruc[idx]):
                self._logger.info("possible neighbour was masked")
            neighbour_region = self.client.lookup("regions", neighbour_region_id)
            neighbour_name = self.client.lookup("regions", neighbour_region_id)["name"]
            if region_level_id is not None and neighbour_region["level"] != region_level_id:
                self._logger.info("not level %s %s" % (region_level_id, neighbour_name))
                continue
            neighbour_name = self.client.lookup("regions", neighbour_region_id)["name"]
            province = next(self.client.lookup_belongs("regions", neighbour_region_id), {"name": ""})

            if province.get('id', None):
                country = next(self.client.lookup_belongs("regions", province["id"]), {"name": "", "id": ""})
            else:
                country = {"name": "", "id": ""}
            self._logger.info("{}, {}, {}".format(neighbour_name, province["name"], country["name"]))
            data_point = {"id": neighbour_region_id, "name": neighbour_name, "dist": dists[ranking],
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
        # Compute a ball tree (this is quicker than expected)
        self._logger.info("BallTree: computing")
        self.state.ball = BallTree(self.state.data_standardized, leaf_size=2)
        self._logger.info("BallTree: done")
        return

    def similar_to(self, region_id, number_of_regions=10, requested_level=None):
        """
        Attempt to look up the given name and find similar regions.
        :param region_id: name of a region.
        :param number_of_regions: number of similar regions to return in the ranked list.
        :return: a generator of the closest neighbours as a list in the form
        [{id: 123, name: "abc", distance: 1.23, parent_regions: [{"abc"456, 789]
        """
        self._compute_similarity_matrix()
        neighbours, dists = self._similar_to(region_id, number_of_regions)
        self._logger.info("nearest regions to '{}' are: {}".format(region_id, neighbours))
        for output in self._format_results(neighbours, requested_level, dists):
            yield output
