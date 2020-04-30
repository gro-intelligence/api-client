try:
    # Python 3.3+
    from unittest.mock import patch, MagicMock
except ImportError:
    # Python 2.7
    from mock import patch, MagicMock
from unittest import TestCase

from api.client.gro_client import GroClient

MOCK_HOST = 'pytest.groclient.url'
MOCK_TOKEN = 'pytest.groclient.token'

mock_entities = {
    'metrics': {},
    'items': {},
    'regions': {},
    'frequencies': {},
    'sources': {},
    'units': {
        10: {'id': 10, 'abbreviation': 'kg', 'name': 'kilogram', 'baseConvFactor': {'factor': 1}, 'convType': 0},
        14: {'id': 14, 'name': 'tonne', 'baseConvFactor': {'factor': 1000}, 'convType': 0},
        36: {'id': 36, 'name': 'Celsius', 'baseConvFactor': {'factor': 1, 'offset': 273}, 'convType': 1},
        37: {'id': 37, 'name': 'Fahrenheit', 'baseConvFactor': {'factor': 0.5, 'offset': 255}, 'convType': 1},
        43: {'id': 43, 'name': 'US Dollar (constant 2010)', 'baseConvFactor': {'factor': None}, 'convType': 0}
    }
}

mock_data_series = [
    {
        'metric_id': 1, # TODO: add names
        'item_id': 1,
        'region_id': 1,
        'partner_region_id': 1,
        'frequency_id': 1,
        'source_id': 1
    }
]

mock_data_points = [
    {'start_date': '2000-01-01', 'end_date': '2000-12-31', 'value': 10, 'unit_id': 14, 'reporting_date': None}
]


def mock_get_available(access_token, api_host, entity_type):
    return list(mock_entities[entity_type].values())


def mock_list_available(access_token, api_host, selected_entities):
    return mock_data_series


def mock_lookup(access_token, api_host, entity_type, entity_ids):
    if isinstance(entity_ids, int):
        # Raises a KeyError if the requested entity hasn't been mocked:
        return mock_entities[entity_type][entity_ids]
    else:
        return [mock_entities[entity_type][entity_id] for entity_id in entity_ids]


def mock_get_allowed_units(access_token, api_host, metric_id, item_id):
    return [unit['id'] for unit in mock_entities['units'].values()]


def mock_get_data_series(access_token, api_host, **selection):
    return mock_data_series


def mock_search(access_token, api_host, entity_type, search_terms):
    return [{'id': entity['id']} for entity in mock_entities[entity_type]
            if search_terms in entity['name']]


def mock_rank_series_by_source(access_token, api_host, selectoions_list):
    pass


def mock_get_geo_centre(access_token, api_host, region_id):
    pass


def mock_get_geojson(access_token, api_host, region_id):
    pass


def mock_get_descendant_regions(access_token, api_host, descendant_level, include_historical, include_details):
    pass


def mock_get_available_timefrequency(access_token, api_host, **selection):
    pass


def mock_get_top(access_token, api_host, entity_type, num_results, **selection):
    pass


def mock_get_data_points(access_token, api_host, **selections):
    pass


@patch('api.client.lib.get_available', MagicMock(side_effect=mock_get_available))
@patch('api.client.lib.list_available', MagicMock(side_effect=mock_list_available))
@patch('api.client.lib.lookup', MagicMock(side_effect=mock_lookup))
@patch('api.client.lib.get_allowed_units', MagicMock(side_effect=mock_get_allowed_units))
@patch('api.client.lib.get_data_series', MagicMock(side_effect=mock_get_data_series))
@patch('api.client.lib.rank_series_by_source', MagicMock(side_effect=mock_rank_series_by_source))
@patch('api.client.lib.get_geo_centre', MagicMock(side_effect=mock_get_geo_centre))
@patch('api.client.lib.get_geojson', MagicMock(side_effect=mock_get_geojson))
@patch('api.client.lib.get_descendant_regions', MagicMock(side_effect=mock_get_descendant_regions))
@patch('api.client.lib.get_available_timefrequency', MagicMock(side_effect=mock_get_available_timefrequency))
@patch('api.client.lib.get_top', MagicMock(side_effect=mock_get_top))
@patch('api.client.lib.get_data_points', MagicMock(side_effect=mock_get_data_points))
class GroClientTests(TestCase):
    def setUp(self):
        self.client = GroClient(MOCK_HOST, MOCK_TOKEN)
        self.assertTrue(isinstance(self.client, GroClient))

    def test_get_logger(self):
        # should NOT raise any exception if get_logger correctly returns a logger object:
        self.client.get_logger().debug('Test output')

    def test_get_available(self):
        self.assertTrue('name' in self.client.get_available('units')[0])

    def test_list_available(self):
        self.assertTrue('metric_id' in self.client.list_available({})[0])

    def test_lookup(self):
        self.assertEqual(self.client.lookup('units', 10)['name'], 'kilogram')

    def test_lookup_unit_abbreviation(self):
        self.assertEqual(self.client.lookup_unit_abbreviation(10), 'kg')

    def test_get_allowed_units(self):
        self.assertTrue(isinstance(self.client.get_allowed_units(1, 1)[0], int))

    def test_get_data_series(self):
        self.assertTrue(True)

    def test_search(self):
        self.assertTrue(True)

    def test_search_and_lookup(self):
        self.assertTrue(True)

    def test_lookup_belongs(self):
        self.assertTrue(True)

    def test_rank_series_by_source(self):
        self.assertTrue(True)

    def test_get_geo_centre(self):
        self.assertTrue(True)

    def test_get_geojson(self):
        self.assertTrue(True)

    def test_get_descendant_regions(self):
        self.assertTrue(True)

    def test_get_available_timefrequency(self):
        self.assertTrue(True)

    def test_get_top(self):
        self.assertTrue(True)

    def test_get_df(self):
        self.assertTrue(True)

    def test_add_points_to_df(self):
        self.assertTrue(True)

    def test_get_data_points(self):
        self.assertTrue(True)

    def test_GDH(self):
        self.assertTrue(True)

    def test_get_data_series_list(self):
        self.assertTrue(True)

    def test_add_single_data_series(self):
        self.assertTrue(True)

    def test_find_data_series(self):
        self.assertTrue(True)

    def test_add_data_series(self):
        self.assertTrue(True)

    def test_search_for_entity(self):
        self.assertTrue(True)

    def test_get_provinces(self):
        self.assertTrue(True)

    def test_get_names_for_selection(self):
        self.assertTrue(True)

    def test_pick_random_entities(self):
        self.assertTrue(True)

    def test_pick_random_data_series(self):
        self.assertTrue(True)

    def test_print_one_data_series(self):
        self.assertTrue(True)

    def test_convert_unit(self):
        self.assertEqual(
            self.client.convert_unit({'value': 1, 'unit_id': 10}, 10),
            {'value': 1, 'unit_id': 10}
        )
        self.assertEqual(
            self.client.convert_unit({'value': 1, 'unit_id': 10}, 14),
            {'value': 0.001, 'unit_id': 14}
        )
        self.assertEqual(
            self.client.convert_unit({'value': 3, 'unit_id': 36}, 37),
            {'value': 42, 'unit_id': 37}
        )
        self.assertEqual(
            self.client.convert_unit({'value': 1, 'unit_id': 37}, 36),
            {'value': -17.5, 'unit_id': 36}
        )

        self.assertEqual(self.client.convert_unit({}, 36), {})

        with self.assertRaises(Exception):
            self.client.convert_unit({'value': 1, 'unit_id': 10}, 43)

        self.assertEqual(
            self.client.convert_unit({'value': None, 'unit_id': 37}, 36),
            {'value': None, 'unit_id': 36}
        )

        with self.assertRaises(Exception):
            self.client.convert_unit({'value': None, 'unit_id': 10}, 43)
