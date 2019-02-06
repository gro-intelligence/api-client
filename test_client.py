import unittest

from api.client import Client
from api.client.batch_client import BatchClient


class MyTestCase(unittest.TestCase):
    api_client = None  # type: client

    def setUp(self):
        self.api_client = Client("api.gro-intelligence.com",
                                            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImV5dmluZC5uaWtsYXNzb25A"
                                            "Z3JvLWludGVsbGlnZW5jZS5jb20iLCJ1c2VySWQiOjQxMDUsInR5cGUiOiJsb2dpbiIsImlhd"
                                            "CI6MTUzODY2MDM0NX0.M4L22oukM_Ghb8c8CpHqXDGNEBMMcRqqa7HKXF_lweE")
        self.batch_api_client = BatchClient("api.gro-intelligence.com",
                                            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImV5dmluZC5uaWtsYXNzb25A"
                                            "Z3JvLWludGVsbGlnZW5jZS5jb20iLCJ1c2VySWQiOjQxMDUsInR5cGUiOiJsb2dpbiIsImlhd"
                                            "CI6MTUzODY2MDM0NX0.M4L22oukM_Ghb8c8CpHqXDGNEBMMcRqqa7HKXF_lweE")


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
        })[500]

        # This may change in the future but hopefully not...
        reference_value = {u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2001-07-14T00:00:00.000Z',
                           u'input_unit_id': 2, u'frequency_name': u'daily', u'value': 0, u'frequency_id': 1,
                           u'available_date': u'2018-05-30T00:00:00.000Z', u'item_id': 2039, u'start_date':
                               u'2001-07-14T00:00:00.000Z', u'metric_id': 2100031}

        self.assertItemsEqual(queried_value, reference_value)

        return

    def test_lookup(self):

        result = self.batch_api_client.batch_async_lookup([["regions", 131072]])
        print(result)
        self.assertItemsEqual(result, [{u'name': u'Verkhneketskiy rayon', u'level': 5, u'contains':
            [1000115937, 1000114964, 1000111695, 1000039835], u'longitude': None,
                                       u'rankingScore': 0.7639320225, u'latitude': None, u'id': 131072}])

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

    def test_batch_lookup(self):

        # This checks that the new Async interface returns the same results as doing the same thing with the
        # sequential API calls.
        regions = [("regions", 131072), ("regions", 131073), ("regions", 131074)]

        results_classic = []

        for region in regions:
            results_classic.append(self.api_client.lookup(*region))

        result_async = [0] * 3

        self.batch_api_client.batch_async_lookup(regions, result_async)

        self.assertItemsEqual(results_classic, result_async)

        return


if __name__ == '__main__':
    unittest.main()
