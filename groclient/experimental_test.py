try:
    # Python 3.3+
    from unittest.mock import patch
except ImportError:
    # Python 2.7
    from mock import patch

from datetime import date
from unittest import TestCase

import pandas as pd

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

        self.assertEqual(df.iloc[0]["start_timestamp"], date(2023, 5, 1))
        self.assertEqual(df.iloc[0]["end_timestamp"], date(2023, 5, 2))
        self.assertEqual(df.iloc[0]["metric_id"], 2540047)
        self.assertEqual(df.iloc[0]["region_id"], 12344)
        self.assertEqual(df.iloc[1]["region_id"], 12345)

        self.assertEqual(df.shape[0], 2)
        self.assertEqual(df.shape[1], 10)
