import os
import sys
import api.client.lib
import unittest

from api.client import Client
from api.client.batch_client import BatchClient


class MyTestCase(unittest.TestCase):
    api_client = None  # type: client

    def setUp(self):
        self.api_client = Client("api.gro-intelligence.com", os.environ['GROAPI_TOKEN'])
        self.batch_api_client = BatchClient("api.gro-intelligence.com", os.environ['GROAPI_TOKEN'])

    def test_connection_and_lookup(self):
        result = next(self.api_client.search_and_lookup("regions", "paris"))
        self.assertEqual(result["id"], 115105)
        return

    def test_get_datapoints(self):
        queried_value = self.api_client.get_data_points(**{
            'metric_id': 2100031,
            'item_id': 2039,
            'region_id': 136969,
            'source_id': 35,
            'frequency_id': 1
        })[0]
        # This may change in the future but hopefully not...
        reference_value =  {u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2000-03-01T00:00:00.000Z', u'input_unit_id': 2, u'frequency_name': u'daily', u'value': 0, u'frequency_id': 1, u'item_id': 2039, u'start_date': u'2000-03-01T00:00:00.000Z', u'metric_id': 2100031}
        self.assertItemsEqual(queried_value, reference_value)

        return

    def test_lookup(self):
        result = self.api_client.lookup("regions", 131072)
        self.assertItemsEqual(result, {u'name': u'Verkhneketskiy rayon', u'level': 5, u'contains':
                                       [1000115937, 1000114964, 1000111695, 1000039835], u'longitude': None,
                                       u'rankingScore': 0.7639320225, u'latitude': None, u'id': 131072})

    def test_batch_get_datapoints(self):

        # This checks that the new Async interface returns the same results as doing the same thing with the
        # sequential API calls.
        regions = [136969, 136970, 136971]
        queries = []

        results_classic = []

        for region_id in regions:
            queries.append({
                'metric_id': 2100031,
                'item_id': 2039,
                'region_id': region_id,
                'source_id': 35,
                'frequency_id': 1
            })

        for query in queries:
            results_classic.append(self.api_client.get_data_points(**query))

        result_async = [0] * 3
        self.batch_api_client.batch_async_get_data_points(queries, output_list=result_async)
        self.assertItemsEqual(results_classic, result_async)
        return


if __name__ == '__main__':
    unittest.main()
