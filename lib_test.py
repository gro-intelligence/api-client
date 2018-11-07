import pytest
import mock

from api.client import lib

MOCK_HOST = "pytest.groclient.url"
MOCK_TOKEN = "pytest.groclient.token"

# TODO: Handle cases like the crop-calendar logic.

def initialize_requests_mocker_and_get_mock_data(mock_requests_get, mock_data={"data": ["obj1", "obj2", "obj3"]}):
    mock_requests_get.return_value.json.return_value = mock_data
    mock_requests_get.return_value.status_code = 200
    return mock_data

@mock.patch('requests.get')
def test_get_available(mock_requests_get):
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    # Test data
    entity_types = ["items", "metrics", "regions"]

    for ent_type in entity_types:
        assert lib.get_available(MOCK_TOKEN, MOCK_HOST, ent_type) == mock_data["data"]
        # Make sure that call now exists in the mock call stack
        mock_requests_get.assert_has_calls([mock.call('https://pytest.groclient.url/v2/' + ent_type,
                  headers={'authorization': 'Bearer pytest.groclient.token'},
                  params=None,
                  timeout=None)])

@mock.patch('requests.get')
def test_list_available(mock_requests_get):
    # Tests the base functionality
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    entities = {'metricId': '123', 'itemId': '456', 'regionId': '789'}

    assert lib.list_available(MOCK_TOKEN, MOCK_HOST, entities) == mock_data["data"]

    # Make sure that call now exists in the mock call stack
    mock_requests_get.assert_has_calls(
        [mock.call('https://pytest.groclient.url/v2/entities/list',
            headers={'authorization': 'Bearer pytest.groclient.token'},
            params=entities,
            timeout=None)]
    )

@mock.patch('requests.get')
def test_list_available_snake_to_camel(mock_requests_get):
    #Tests that the camel-ing fix is working properly.
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    entities = {'metric_id': '123', 'item_id': '456', 'regionId': '789'}
    entities_camel = {'metricId': '123', 'itemId': '456', 'regionId': '789'}

    assert lib.list_available(MOCK_TOKEN, MOCK_HOST, entities) == mock_data["data"]

    # Make sure that call now exists in the mock call stack
    mock_requests_get.assert_has_calls(
        [mock.call('https://pytest.groclient.url/v2/entities/list',
                   headers={'authorization': 'Bearer pytest.groclient.token'},
                   params=entities_camel,
                   timeout=None)]
    )

@mock.patch('requests.get')
def test_lookup(mock_requests_get):
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    # test data
    entity_types = ["items", "metrics", "regions", "units", "sources"]

    for ent_type in entity_types:
        assert lib.lookup(MOCK_TOKEN, MOCK_HOST, ent_type, 12345) == mock_data["data"]

        # Make sure that call now exists in the mock call stack
        mock_requests_get.assert_has_calls(
            [mock.call('https://pytest.groclient.url/v2/' + ent_type + '/12345',
                       headers={'authorization': 'Bearer pytest.groclient.token'},
                       params=None,
                       timeout=None)]
        )

# TODO: Add test case for logic in __init.py__. Below will be in that test case:
# @mock.patch('api.client.Client.lookup')
# def test_lookup_unit_abbreviation(lookup_mocked):
#
#     lookup_mocked.return_value = {"abbreviation": "test123"}
#     assert lib.lookup_unit_abbreviation(MOCK_TOKEN, MOCK_HOST, "kg") ==  "test123"
#     assert lib.lookup_unit_abbreviation(MOCK_TOKEN, MOCK_HOST, "kg") ==  "test123"
#     assert lib.lookup_unit_abbreviation(MOCK_TOKEN, MOCK_HOST, "kg") ==  "test123"
#     assert lib.lookup_unit_abbreviation(MOCK_TOKEN, MOCK_HOST, "mg") == "test123"
#
#     # Make sure it caches properly
#     assert lookup_mocked.call_args_list == [mock.call('units', 'kg'), mock.call('units', 'mg')]

@mock.patch('requests.get')
def test_get_data_series(mock_requests_get):
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get)

    # Test data
    # TODO: Currently source and freq id are not supported, so they should not show up in the request. UPDATE
    # TODO: this testcase when they are implemented.
    selection_dict = {"item_id": 123, "metric_id": 456, "region_id": 789,
                      "frequency_id": 101112, "source_id": 131415, "partner_region_id": 161718}

    assert lib.get_data_series(MOCK_TOKEN, MOCK_HOST, **selection_dict) == mock_data["data"]

    # Make sure that call now exists in the mock call stack
    assert [mock.call('https://pytest.groclient.url/v2/data_series/list',
                                headers={'authorization': 'Bearer pytest.groclient.token'},
                                params={'itemId': 123, 'metricId': 456, 'regionId': 789, 'partnerRegionId': 161718},
                                timeout=None)] == mock_requests_get.call_args_list

@mock.patch('requests.get')
def test_get_data_points(mock_requests_get):
    mock_data = ["obj1", "obj2", "obj3"]
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get, mock_data=mock_data)

    # Test data
    selection_dict = {"item_id": 123, "metric_id": 456, "region_id": 789,
                      "frequency_id": 101112, "source_id": 131415, "partner_region_id": 161718}

    assert lib.get_data_points(MOCK_TOKEN, MOCK_HOST, **selection_dict) == mock_data

    # Make sure that call now exists in the mock call stack
    assert [mock.call('https://pytest.groclient.url/v2/data',
                                headers={'authorization': 'Bearer pytest.groclient.token'},
                                params={'itemId': 123, 'regionId': 789, 'partnerRegionId': 161718,
                                        'sourceId': 131415, 'metricId': 456, 'frequencyId': 101112},
                                timeout=None)] == mock_requests_get.call_args_list

@mock.patch('requests.get')
def test_search(mock_requests_get):
    mock_data = ["obj1", "obj2", "obj3"]
    mock_data = initialize_requests_mocker_and_get_mock_data(mock_requests_get, mock_data=mock_data)

    assert lib.search(MOCK_TOKEN, MOCK_HOST, "items", "test123") == mock_data

    assert [mock.call('https://pytest.groclient.url/v2/search/items',
                                headers={'authorization': 'Bearer pytest.groclient.token'},
                                params={'q': 'test123'},
                                timeout=None)] == mock_requests_get.call_args_list

@mock.patch('api.client.lib.lookup')
@mock.patch('api.client.lib.search')
def test_search_and_lookup(search_mocked, lookup_mocked):
    # Set up
    # mock return values
    search_mocked.return_value = [{"id": "test1"}, {"id": "test2"}]
    mock_data = ["obj1", "obj2"]
    lookup_mocked.return_value = mock_data
    search_and_lookup_result = list(lib.search_and_lookup(MOCK_TOKEN, MOCK_HOST, "items", "test123"))

    assert search_and_lookup_result == [mock_data]*2

    assert [mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 'test123')] == search_mocked.mock_calls
    assert [mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 'test1'),
            mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 'test2')] == lookup_mocked.mock_calls

@mock.patch('api.client.lib.lookup')
@mock.patch('requests.get')
def test_lookup_belongs(mock_requests_get, lookup_mocked):
    # Set up
    # mock return values
    mock_data = ["obj1", "obj2"]
    mock_requests_get.return_value.json.return_value = {"data": {"test_entity": [1,2,3]}}
    mock_requests_get.return_value.status_code = 200
    lookup_mocked.return_value = mock_data

    lookup_belongs_result = list(lib.lookup_belongs(MOCK_TOKEN, MOCK_HOST, "items", "test_entity"))

    assert [mock_data]*3 == lookup_belongs_result

    assert [mock.call('https://pytest.groclient.url/v2/items/belongs-to',
                                headers={'authorization': 'Bearer pytest.groclient.token'},
                                params={'ids': 'test_entity'},
                                timeout=None)] == mock_requests_get.call_args_list

    assert [mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 1),
                     mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 2),
                     mock.call('pytest.groclient.token', 'pytest.groclient.url', 'items', 3)] \
           == lookup_mocked.mock_calls

@mock.patch('requests.get')
def test_rank_series_by_source(mock_requests_get):
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

    c = list(lib.rank_series_by_source(MOCK_TOKEN, MOCK_HOST, [a,b]))
    assert(len(c) == 3)

    assert mock_return == [x["source_id"] for x in c]
