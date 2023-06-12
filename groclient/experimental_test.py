try:
    # Python 3.3+
    from unittest.mock import patch
except ImportError:
    # Python 2.7
    from mock import patch

import numpy as np
import pandas as pd

from pandas.testing import assert_frame_equal
from unittest import TestCase

from groclient import Experimental
from groclient.mock_data import mock_v2_prime_data_request, mock_v2_prime_data_response

MOCK_HOST = "pytest.groclient.url"
MOCK_TOKEN = "pytest.groclient.token"

class ExperimentalTests(TestCase):
    def setUp(self):
        self.client = Experimental(MOCK_HOST, MOCK_TOKEN)
        self.assertTrue(isinstance(self.client, Experimental))

    @patch("groclient.lib.get_data_points_v2_prime")
    def test_get_data_points(self, mock_get_data_points):
        mock_get_data_points.return_value = mock_v2_prime_data_response.copy()

        res = self.client.get_data_points(**mock_v2_prime_data_request)

        self.assertEqual(len(res), len(mock_v2_prime_data_response))
        self.assertIn('data_points', res[0])
        self.assertIn('series_description', res[0])
        point = res[0]['data_points'][0]
        self.assertTrue(isinstance(point["start_timestamp"], int))
        self.assertTrue(isinstance(point["end_timestamp"], int))

    @patch("groclient.lib.get_data_points_v2_prime")
    def test_get_data_points_df(self, mock_get_data_points):
        mock_get_data_points.return_value = mock_v2_prime_data_response.copy()
        df = self.client.get_data_points_df(**mock_v2_prime_data_request)

        expected_df = pd.DataFrame({
            "value": [33.20, 32.73],
            "start_timestamp":['2023-05-01', '2023-05-01'],
            "end_timestamp": ['2023-05-02', '2023-05-02'],
            "metric_id": [2540047, 2540047],
            "item_id": [3457, 3457],
            "region_id": [12344, 12345],
            "partner_region_id": [np.nan, np.nan],
            "frequency_id": [1,1],
            "source_id": [26, 26],
            "unit_id": [36, 36]
        }).astype({
            'start_timestamp': 'datetime64',
            'end_timestamp': 'datetime64'
        })

        print(df.dtypes)

        assert_frame_equal(df, expected_df)


    @patch("groclient.lib.get_data_points_v2_prime")
    def test_get_data_points_df_no_data(self, mock_get_data_points):
        mock_get_data_points.return_value = []
        df = self.client.get_data_points_df(**mock_v2_prime_data_request)

        self.assertTrue(df.empty)
