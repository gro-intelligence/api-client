import unittest
import mock

from api.client import Client

# TODO: Test individual functions in lib.py.
# TODO: Handle cases like the crop-calendar logic.

class ClientTestCase(unittest.TestCase):
    def setUp(self):
        # Initialize the API with some client credentials.

        self.client = Client("pytest.groclient.url", "pytest.groclient.token")
        self.entity_types_names = ["metricId", "item_id", "region_id"]
        self.entity_types_names_camel = ["metricId", "itemId", "regionId"]

    @mock.patch('requests.get')
    def test_get_available(self, mock_requests_get):
        # Set up mock return values
        mock_data = ["obj1", "obj2", "obj3"]
        mock_requests_get.return_value.json.return_value = {"data": mock_data}
        mock_requests_get.return_value.status_code = 200

        # Test data
        entity_types = ["items", "metrics", "regions"]

        for ent_type in entity_types:
            self.assertEqual(self.client.get_available(ent_type), mock_data)
            # Make sure that call now exists in the mock call stack
            mock_requests_get.assert_has_calls([mock.call('https://pytest.groclient.url/v2/' + ent_type,
                      headers={'authorization': 'Bearer pytest.groclient.token'},
                      params=None,
                      timeout=None)])

    @mock.patch('requests.get')
    def test_list_available(self, mock_requests_get):
        # Set up mock return values
        mock_data = ["obj1", "obj2", "obj3"]
        mock_requests_get.return_value.json.return_value = {"data": mock_data}
        mock_requests_get.return_value.status_code = 200

        for ent_type_name, ent_type_name_camel in zip(self.entity_types_names, self.entity_types_names_camel):
            self.assertEqual(self.client.list_available({ent_type_name: "123"}), mock_data)

            # Make sure that call now exists in the mock call stack
            mock_requests_get.assert_has_calls(
                [mock.call('https://pytest.groclient.url/v2/entities/list',
                    headers={'authorization': 'Bearer pytest.groclient.token'},
                    params={ent_type_name_camel: '123'},
                    timeout=None)]
            )

    @mock.patch('requests.get')
    def test_lookup(self, mock_requests_get):
        # Set up mock return values
        mock_data = ["obj1", "obj2", "obj3"]
        mock_requests_get.return_value.json.return_value = {"data": mock_data}
        mock_requests_get.return_value.status_code = 200

        # test data
        entity_types = ["items", "metrics", "regions", "units", "sources"]

        for ent_type in entity_types:
            self.assertEqual(self.client.lookup(ent_type, 12345), mock_data)

            # Make sure that call now exists in the mock call stack
            mock_requests_get.assert_has_calls(
                [mock.call('https://pytest.groclient.url/v2/' + ent_type + '/12345',
                           headers={'authorization': 'Bearer pytest.groclient.token'},
                           params=None,
                           timeout=None)]
            )

    @mock.patch('api.client.Client.lookup')
    def test_lookup_unit_abbreviation(self, lookup_mocked):

        lookup_mocked.return_value = {"abbreviation": "test123"}
        self.assertEqual(self.client.lookup_unit_abbreviation("kg"), "test123")
        self.assertEqual(self.client.lookup_unit_abbreviation("kg"), "test123")
        self.assertEqual(self.client.lookup_unit_abbreviation("kg"), "test123")
        self.assertEqual(self.client.lookup_unit_abbreviation("mg"), "test123")

        # Make sure it caches properly
        self.assertListEqual(lookup_mocked.call_args_list, [mock.call('units', 'kg'), mock.call('units', 'mg')])

    @mock.patch('requests.get')
    def test_get_data_series(self, mock_requests_get):
        # Set up mock return values
        mock_data = ["obj1", "obj2", "obj3"]
        mock_requests_get.return_value.json.return_value = {"data": mock_data}
        mock_requests_get.return_value.status_code = 200

        # Test data
        # TODO: Currently source and freq id are not supported, so they should not show up in the request. UPDATE
        # TODO: this testcase when they are implemented.
        selection_dict = {"item_id": 123, "metric_id": 456, "region_id": 789,
                          "frequency_id": 101112, "source_id": 131415, "partner_region_id": 161718}

        self.assertEqual(self.client.get_data_series(**selection_dict), mock_data)

        # Make sure that call now exists in the mock call stack
        self.assertEqual([mock.call('https://pytest.groclient.url/v2/data_series/list',
                                    headers={'authorization': 'Bearer pytest.groclient.token'},
                                    params={'itemId': 123, 'metricId': 456, 'regionId': 789, 'partnerRegionId': 161718},
                                    timeout=None)],
                         mock_requests_get.call_args_list)

    @mock.patch('requests.get')
    def test_get_data_points(self, mock_requests_get):
        # Set up
        # mock return values
        mock_data = ["obj1", "obj2", "obj3"]
        mock_requests_get.return_value.json.return_value = mock_data
        mock_requests_get.return_value.status_code = 200

        # Test data
        selection_dict = {"item_id": 123, "metric_id": 456, "region_id": 789,
                          "frequency_id": 101112, "source_id": 131415, "partner_region_id": 161718}

        self.assertEqual(self.client.get_data_points(**selection_dict), mock_data)

        # Make sure that call now exists in the mock call stack
        self.assertEqual([mock.call('https://pytest.groclient.url/v2/data',
                                    headers={'authorization': 'Bearer pytest.groclient.token'},
                                    params={'itemId': 123, 'regionId': 789, 'partnerRegionId': 161718,
                                            'sourceId': 131415, 'metricId': 456, 'frequencyId': 101112},
                                    timeout=None)],
                         mock_requests_get.call_args_list)

    @mock.patch('requests.get')
    def test_search(self, mock_requests_get):
        # Set up
        # mock return values
        mock_data = ["obj1", "obj2", "obj3"]
        mock_requests_get.return_value.json.return_value = mock_data
        mock_requests_get.return_value.status_code = 200

        self.assertEqual(self.client.search("items", "test123"), mock_data)

        self.assertEqual([mock.call('https://pytest.groclient.url/v2/search/items',
                                    headers={'authorization': 'Bearer pytest.groclient.token'},
                                    params={'q': 'test123'},
                                    timeout=None)],
                         mock_requests_get.call_args_list)

    @mock.patch('api.client.lib.lookup')
    @mock.patch('api.client.lib.search')
    def test_search_and_lookup(self, search_mocked, lookup_mocked):
        # Set up
        # mock return values
        search_mocked.return_value = [{"id": "test1"}, {"id": "test2"}]
        mock_data = ["obj1", "obj2"]
        lookup_mocked.return_value = mock_data
        search_and_lookup_result = list(self.client.search_and_lookup("items", "test123"))

        self.assertEqual(search_and_lookup_result, [mock_data]*2)

        self.assertEqual([mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 'test123')],
                         search_mocked.mock_calls)
        self.assertEqual([mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 'test1'),
                          mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 'test2')],
                         lookup_mocked.mock_calls)

    @mock.patch('api.client.lib.lookup')
    @mock.patch('requests.get')
    def test_lookup_belongs(self, mock_requests_get, lookup_mocked):
        # Set up
        # mock return values
        mock_data = ["obj1", "obj2"]
        mock_requests_get.return_value.json.return_value = {"data": {"test_entity": [1,2,3]}}
        mock_requests_get.return_value.status_code = 200
        lookup_mocked.return_value = mock_data

        lookup_belongs_result = list(self.client.lookup_belongs("items", "test_entity"))

        self.assertEqual([mock_data]*3, lookup_belongs_result)

        self.assertEqual([mock.call('https://pytest.groclient.url/v2/items/belongs-to',
                                    headers={'authorization': 'Bearer pytest.groclient.token'},
                                    params={'ids': 'test_entity'},
                                    timeout=None)],
                         mock_requests_get.call_args_list)

        self.assertEqual([mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 1),
                         mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 2),
                         mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 3)],
                         lookup_mocked.mock_calls)

    @mock.patch('requests.get')
    def test_rank_series_by_source(self, mock_requests_get):

        mock_return = ["data1", "data2", "data3"]
        mock_requests_get.return_value.json.return_value = mock_return
        mock_requests_get.return_value.status_code = 200

        # Ordering of the dict should not matter
        a = {"region_id": 13474, "abc": 123, "def": 123, "ghe": 123, "fij": 123, "item_id": 3457, "metric_id": 2540047, "source_id": 26}
        a.pop("abc")
        a.pop("def")
        a.pop("ghe")
        a.pop("fij")

        b = {"item_id": 3457, "region_id": 13474, "metric_id": 2540047, "source_id": 26}

        c = list(self.client.rank_series_by_source([a,b]))
        assert(len(c) == 3)

        self.assertEqual(mock_return, [x["source_id"] for x in c])

if __name__ == '__main__':
    unittest.main()
