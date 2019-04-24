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

    def __init__(self, region_properties, regions_to_compare=None, data_dir=None, no_download=False):
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
        self._logger.info("SimilarRegionState: loading...")
        self.state = SimilarRegionState(region_properties, regions_to_compare, self.client, data_dir=data_dir, 
                no_download=no_download)
        self._logger.info("SimilarRegionState: done.")
        self._logger.info("BallTree: computing...")
        self.ball = BallTree(self.state.data_standardized, leaf_size=2)
        self._logger.info("BallTree: done.")
        return

    def _regions_avail_for_selection(self, region_properties):
        regions = set()
        for props in region_properties.values():
            for available_series in self.client.list_available(props["selected_entities"]):
                regions.add(available_series["region_id"])
        self._logger.info("{} regions are available for comparison.".format(len(regions)))
        return list(regions)

    def _format_results(self, sim_regions, region_level_id, dists):
        for ranking, idx in enumerate(sim_regions):
            sim_region_region_id = self.state.inverse_mapping[idx]
            if np.ma.is_masked(self.state.data_nonstruc[idx]):
                self._logger.info("possible sim_region was masked")
            sim_region_region = self.client.lookup("regions", sim_region_region_id)
            sim_region_name = self.client.lookup("regions", sim_region_region_id)["name"]
            if region_level_id is not None and sim_region_region["level"] != region_level_id:
                self._logger.info("not level %s %s" % (region_level_id, sim_region_name))
                continue
            sim_region_name = self.client.lookup("regions", sim_region_region_id)["name"]
            parent = next(self.client.lookup_belongs("regions", sim_region_region_id), {"name": ""})

            if parent.get('id', None):
                grandparent = next(self.client.lookup_belongs("regions", parent["id"]), {"name": "", "id": ""})
            else:
                grandparent = {"name": "", "id": ""}
            self._logger.info(u"{}, {}, {}".format(sim_region_name, parent["name"], grandparent["name"]))
            data_point = {"id": sim_region_region_id, "name": sim_region_name, "dist": dists[ranking],
                          "parent": (parent["id"], parent["name"], grandparent["id"], grandparent["name"])}
            yield data_point

    def _similar_to(self, region_id, number_of_regions):
        """
        This gives us the regions that are most similar to the either the given region in the case on region is give, or
        similar to the "collective mean" of the regions as given.
        :param region_id: a Gro region id representing the reference region you want to find similar regions to.
        :param number_of_regions: number of most similar matches to return
        :return: regions that are most similar to the given region id
        """
        assert region_id in self.state.mapping, "This region is not available in your configuration or " \
                                                "it lacks coverage in the chosen region properties."
        # list as an index to preserve dimensionality of returned data
        x = self.state.data_standardized[self.state.mapping[region_id], :]
        x = x.reshape(1, -1)
        assert number_of_regions < self.state.num_regions, "number_of_regions must be smaller than or equal to total " \
                                                            "number of regions in the comparison"
        neighbour_dists, neighbour_idxs = self.ball.query(x, k=number_of_regions)
        return neighbour_idxs[0], neighbour_dists[0]

    def similar_to(self, region_id, number_of_regions=10, requested_level=None):
        """
        Attempt to look up the given name and find similar regions.
        :param region_id: a Gro region id representing the reference region you want to find similar regions to.
        :param number_of_regions: number of most similar matches to return
        :return: a generator of the most similar regions as a list in the form
        [{id: 123, name: "abc", distance: 1.23, parent_regions: []]
        """
        sim_regions, dists = self._similar_to(region_id, number_of_regions)
        self._logger.info("Found {} regions most similar to '{}'.".format(len(sim_regions), region_id))
        for output in self._format_results(sim_regions, requested_level, dists):
            yield output
