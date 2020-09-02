import numpy as np
import os
from sklearn.neighbors import BallTree
from groclient import GroClient
from groclient.lib import get_default_logger
from api.client.samples.similar_regions.similar_region_state import SimilarRegionState
from sklearn.metrics.pairwise import euclidean_distances

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
        self.client = GroClient(API_HOST, ACCESS_TOKEN)
        self._logger = get_default_logger()
        if not regions_to_compare:
            regions_to_compare = self._regions_avail_for_selection(region_properties)
        self._logger.info("SimilarRegionState: loading...")
        self.state = SimilarRegionState(region_properties, regions_to_compare, self.client, data_dir=data_dir, 
                no_download=no_download)
        self._logger.info("SimilarRegionState: done.")
        self._logger.info("BallTree: computing...")
        # Featues are weighted at this point, so this is equivalent to using
        # sklearn.neighbors.DistanceMetric.get_metric('wminkowski', **{'p':2,'w':self.state.weight_vector})
        # but with unweighted features
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

    def _format_results(self, sim_regions, requested_region_level, dists, metric_dists):
        for ranking, sim_region_region_id in enumerate(sim_regions):
            region_info = self.client.lookup("regions", sim_region_region_id)
            region_level = region_info["level"]
            sim_region_name = region_info["name"]
            
            if requested_region_level is not None and region_level != requested_region_level:
                self._logger.info("not level %s %s" % (requested_region_level, sim_region_name))
                continue
                
            # Choose parent one level up from this region
            parent = {"name": ""}
            for r in self.client.lookup_belongs("regions", sim_region_region_id):
                parent = r # in case there is no parent at correct level we will just take the last
                if r['level'] == region_level-1:
                    break

            if parent.get('id', None):
                grandparent = next(self.client.lookup_belongs("regions", parent["id"]), {"name": "", "id": ""})
            else:
                grandparent = {"name": "", "id": ""}
            self._logger.info(u"{}, {}, {}".format(sim_region_name, parent["name"], grandparent["name"]))
            metric_dists_dict = {prop_name: distance for (prop_name, distance) in zip(self.state.region_properties.keys(), metric_dists[ranking])}
            data_point = {"id": sim_region_region_id, "name": sim_region_name, "dist": dists[ranking],
                    "parent": (parent["id"], parent["name"], grandparent["id"], grandparent["name"]), "metric_dist": metric_dists_dict}
            yield data_point

    def _similar_to(self, region_id, number_of_regions):
        """
        This gives us the regions that are most similar to the either the given region in the case on region is give, or
        similar to the "collective mean" of the regions as given.
        :param region_id: a Gro region id representing the reference region you want to find similar regions to.
        :param number_of_regions: number of most similar matches to return
        :return: regions that are most similar to the given region id, the distances to each of these, and the 
                    individual distances for each property (in the order of properties as iterated on the properties
                    dictionary). 
        """
        assert region_id in self.state.mapping, "This region is not available in your configuration or " \
                                                "it lacks coverage in the chosen region properties."
        # list as an index to preserve dimensionality of returned data
        x = self.state.data_standardized[self.state.mapping[region_id], :]
        x = x.reshape(1, -1)
        neighbour_dists, neighbour_idxs = self.ball.query(x, k = min(number_of_regions, self.state.num_regions))

        # get the individual distances 
        metric_distances = [self._get_distances(self.state.mapping[region_id], idx2) for idx2 in neighbour_idxs[0]]

        return self.state.inverse_mapping[neighbour_idxs[0]], neighbour_dists[0], metric_distances

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
        sim_regions, dists, metric_dists = self._similar_to(region_id, number_of_regions)
        self._logger.info("Found {} regions most similar to '{}'.".format(len(sim_regions), region_id))
        for output in self._format_results(sim_regions, requested_level, dists, metric_dists):
            yield output
