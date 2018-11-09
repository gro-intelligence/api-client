import numpy as np
import os
import cPickle as pickle
import api.client.lib

SAVED_STATE_PATH = "saved_states/"

class SimilarRegionState(object):
    """
    An object containing all the pickle-able parameters for the state of this SimilarRegion search.
    """

    def __init__(self):

        # List of names of metrics we are using in this comparison. *Must exist in known_metrics*
        self.metrics_to_use = []

        # List of integers of region ids we are fetching or have data for.
        self.known_regions = set()
        # If we don't care, just download everything we can for the given metrics.
        self.all_regions = False

        # Data stores::
        # Float array of all processed data for each (metric, region).
        self.data = np.zeros((0, 0), dtype=float)
        # Boolean array. True if data for that (metric, region) has been fetched into the data array.
        self.not_fetched_yet = np.full((0, 0), False, dtype=bool)

        # Standardized versions of this
        self.data_standardized = np.zeros((0, 0), dtype=float)
        self.recompute = True

        # Mapping to and from our internal numpy idxs
        self.district_to_row_idx = {}
        self.row_idx_to_district = []
        self.metric_to_col_idx = {}
        self.metric_data = {}

        # Weights of each metric
        self.metric_weights = {}

        # The ball tree
        self.ball = None

        # Some logging... of course.
        self._logger = api.client.lib.get_default_logger()

    def save(self):
        """
        Save state to disk.
        :return: True if succeeded.
        """
        mod_time = 0

        if os.path.isfile(SAVED_STATE_PATH + "state.pickle"):
            # Let's not delete anything, but rather move it.
            mod_time = os.path.getmtime(SAVED_STATE_PATH + "state.pickle")
            os.rename(SAVED_STATE_PATH + "state.pickle", SAVED_STATE_PATH + "state_%i.pickle" % mod_time)

        if os.path.isfile(SAVED_STATE_PATH + "state_data.npy"):
            mod_time = mod_time if mod_time != 0 else os.path.getmtime(SAVED_STATE_PATH + "state_data.npy")
            os.rename(SAVED_STATE_PATH + "state_data.npy", SAVED_STATE_PATH + "state_data_%i.npy" % mod_time)

        if os.path.isfile(SAVED_STATE_PATH + "state_data_mask.npy"):
            mod_time = mod_time if mod_time != 0 else os.path.getmtime(SAVED_STATE_PATH + "state_data_mask.npy")
            os.rename(SAVED_STATE_PATH + "state_data_mask.npy", SAVED_STATE_PATH + "state_data_mask_%i.npy" % mod_time)

        self._logger.info("Saving state to pickle and npy.")


        del self._logger

        # put the data folder into an npy
        with open(SAVED_STATE_PATH + "state_data.npy", 'wb') as f:
            np.save(f, self.data.data)

        with open(SAVED_STATE_PATH + "state_data_mask.npy", 'wb') as f:
            np.save(f, self.data.mask)

        del self.data_standardized
        del self.data
        del self.ball
        del self.metric_data
        self.recompute = True

        with open(SAVED_STATE_PATH + "state.pickle", 'wb') as f:
            pickle.dump(self.__dict__, f)

        self._logger = api.client.lib.get_default_logger()

        self.data_standardized = np.zeros((0, 0), dtype=float)
        self.ball = None

        self.load()

        self._logger.info("Saved state to state.pickle.")

        return True

    def load(self, path_to_pickle=SAVED_STATE_PATH + "state.pickle"):
        """
        Load state from disk.
        :return: True if succeeded.
        """
        if not os.path.isfile(path_to_pickle):
            raise Exception("Can't find saved state.")

        self._logger.info("Loading state from pickle.")

        with open(path_to_pickle, 'rb') as f:
            tmp_dict = pickle.load(f)

        self.__dict__.update(tmp_dict)

        with open(SAVED_STATE_PATH + "state_data.npy", 'rb') as f:
            data_temp = np.load(f)

        with open(SAVED_STATE_PATH + "state_data_mask.npy", 'rb') as f:
            data_mask_temp = np.load(f)

        self.data = np.ma.array(data_temp)
        self.data[data_mask_temp] = np.ma.masked

        self._construct_metric_data_views()

        self._logger.info("Done loading state from %s" % path_to_pickle)

        return True

    def _construct_metric_data_views(self):

        self.metric_data = {}

        for idx, metric_name in enumerate(self.metrics_to_use):
            start_idx = self.metric_to_col_idx[metric_name]
            if idx + 1 < len(self.metrics_to_use):
                end_idx = self.metric_to_col_idx[self.metrics_to_use[idx + 1]]
                self.metric_data[metric_name] = self.data[:, start_idx:end_idx]
            else:
                self.metric_data[metric_name] = self.data[:, start_idx:]
