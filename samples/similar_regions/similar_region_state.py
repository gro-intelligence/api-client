import numpy as np
import os
import api.client.lib
from functools import reduce

CACHE_PATH = ".cache/"

class SimilarRegionState(object):
    """
    Holds and initializes parameters and provide ssaving/loading logic for a similar_region search.
    """

    def __init__(self, region_properties, regions_to_compare):

        # Some logging... of course.
        self._logger = api.client.lib.get_default_logger()

        # Some useful metadata
        self.region_properties = region_properties
        self.num_regions = len(regions_to_compare)
        self.num_properties = len(region_properties)
        self.tot_num_features = reduce(lambda acc, prop: acc + prop["properties"]["num_features"],
                                       region_properties.values(),
                                       0)

        # Mapping to and from our internal numpy idxs
        self.mapping = {region_idx:idx for (idx,region_idx) in enumerate(regions_to_compare)}
        self.inverse_mapping = np.array(regions_to_compare)

        # Data stores
        structure = [(name, 'd', p["properties"]["num_features"]) for name, p in
                     region_properties.items()]
        structure_bool = [(name, bool) for name, p in
                     region_properties.items()]
        self.data = np.ma.zeros(self.num_regions, dtype=structure)
        self.data[:] = np.ma.masked

        self._logger.debug("structure of data array entries is {}".format(structure))
        self._logger.debug("structure of missing array entries is {}".format(structure_bool))

        # Boolean array representing any data we haven't yet downloaded.
        # True if data for that (metric, region) has been fetched into the data array.
        self.missing = np.full(self.num_regions, True, dtype=structure_bool)
        self.missing_nonstruc = self.missing.view(
            dtype=[('missing', bool, (self.num_regions, self.num_properties))], type=np.ndarray
        )[0][0]

        # Standardized (0-mean,1-std) version of data in a 2d array (without structure/masking nonsense)
        self.data_standardized = np.zeros((self.num_regions, self.tot_num_features), dtype='d')
        self.recompute = True

        # Weights of each metric
        self.weight_vector = np.ones(self.tot_num_features, dtype='d')

        # The ball tree
        self.ball = None

    def save(self):
        """
        Cache the current state to disk.
        :return: True if succeeded.
        """

        self._logger.info("starting caching of downloaded data.")

        # Loop through the metric views...
        for name in self.region_properties:
            with open(os.path.join(CACHE_PATH, "{}.nbz".format(name)), 'wb') as f:
                np.savez(f,
                         data=self.data[name].data,
                         mask=self.data[name].mask,
                         missing=self.missing[name],
                         mapping=self.mapping,
                         inverse_mapping=self.inverse_mapping)

        self._logger.info("done caching of downloaded data.")

        return

    def load(self):
        """
        Attempt to load any cached information and merge it into our current data situation.
        """

        self._logger.info("checking if cached data available.")

        # Loop through the metric views...
        for name in self.data.names:
            path = os.path.join(CACHE_PATH, "{}.nbz".format(name))
            if os.path.isfile(path):
                self._logger.info("found cached data for {}, loading...".format(name))
                with open(path, 'rb') as f:
                    variables = np.load(f)
                    mutual_regions = set(variables["inverse_mapping"]) & set(self.inverse_mapping)
                    mutual_regions_mapping = self.mapping[mutual_regions]
                    mutual_regions_old_mapping = variables["mapping"][mutual_regions]
                    self.data[name][mutual_regions_mapping] = variables["data"][mutual_regions_old_mapping]
                    mutual_regions_masked = variables["mask"][mutual_regions_old_mapping]
                    self.data[name][mutual_regions_mapping][mutual_regions_masked] = np.ma.masked
                    mutual_regions_missing = variables["missing"][mutual_regions_old_mapping]
                    self.missing[name][mutual_regions_mapping][mutual_regions_missing] = True

        self._logger.info("done checking for cached data")

        return

