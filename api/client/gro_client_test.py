try:
    # Python 3.3+
    from unittest.mock import patch, MagicMock
except ImportError:
    # Python 2.7
    from mock import patch, MagicMock
from unittest import TestCase
from datetime import date

from api.client.gro_client import GroClient

MOCK_HOST = 'pytest.groclient.url'
MOCK_TOKEN = 'pytest.groclient.token'

mock_entities = {
    'metrics': {},
    'items': {},
    'regions': {
        0: {'id': 0, 'name': 'World', 'contains': [1215], 'belongsTo': []},
        1215: {'id': 1215, 'name': 'United States', 'contains': [12345], 'belongsTo': [0]},
        12345: {'id': 12345, 'name': 'Minnesota', 'contains': [], 'belongsTo': [1215]}
    },
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
        'metric_id': 1,  # TODO: add names
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
        return {str(entity_id): mock_entities[entity_type][entity_id] for entity_id in entity_ids}


def mock_get_allowed_units(access_token, api_host, metric_id, item_id):
    return [unit['id'] for unit in mock_entities['units'].values()]


def mock_get_data_series(access_token, api_host, **selection):
    return mock_data_series


def mock_search(access_token, api_host, entity_type, search_terms):
    return [{'id': entity['id']} for entity in mock_entities[entity_type].values()
            if search_terms in entity['name']]


def mock_rank_series_by_source(access_token, api_host, selectoions_list):
    for data_series in mock_data_series:
        yield data_series


def mock_get_geo_centre(access_token, api_host, region_id):
    return [{'centre': [45.7228, -112.996], 'regionId': 1215, 'regionName': 'United States'}]


def mock_get_geojson(access_token, api_host, region_id):
    return {'type': 'GeometryCollection',
            'geometries': [{'type': 'MultiPolygon',
                            'coordinates': [[[[-38.394, -4.225]]]]}]}


def mock_get_descendant_regions(access_token, api_host, region_id, descendant_level, include_historical, include_details):
    regions = list(mock_entities['regions'].values())
    if not include_historical:
        regions = [region for region in regions if not region['historical']]
    if include_details:
        return regions
    else:
        return [{'id': region['id']} for region in regions]


def mock_get_available_timefrequency(access_token, api_host, **selection):
    return [{
        'startDate': '2000-02-18T00:00:00.000Z',
        'frequencyId': 3,
        'endDate': '2020-03-12T00:00:00.000Z',
        'name': '8-day'
    }, {
        'startDate': '2019-09-02T00:00:00.000Z',
        'frequencyId': 1,
        'endDate': '2020-03-09T00:00:00.000Z',
        'name': 'daily'
    }]


def mock_get_top(access_token, api_host, entity_type, num_results, **selection):
    return [
        {'metricId': 860032, 'itemId': 274, 'regionId': 1215, 'frequencyId': 9,
         'sourceId': 2, 'value': 400, 'unitId': 14},
        {'metricId': 860032, 'itemId': 274, 'regionId': 1215, 'frequencyId': 9,
         'sourceId': 2, 'value': 395, 'unitId': 14},
        {'metricId': 860032, 'itemId': 274, 'regionId': 1215, 'frequencyId': 9,
         'sourceId': 2, 'value': 12, 'unitId': 14},
    ]


def mock_get_data_points(access_token, api_host, **selections):
    if isinstance(selections['region_id'], int):
        return [{
            'start_date': '2017-01-01T00:00:00.000Z',
            'end_date': '2017-12-31T00:00:00.000Z',
            'value': 408913833.8019222, 'unit_id': 15,
            'reporting_date': None,
            'metric_id': 860032, 'item_id': 274, 'region_id': 1215,
            'partner_region_id': 0, 'frequency_id': 9, 'source_id': 2,
            'belongs_to': {
                'metric_id': 860032,
                'item_id': 274,
                'region_id': 1215,
                'frequency_id': 9,
                'source_id': 2
            }
        }]
    elif isinstance(selections['region_id'], list):
        return [{
            'start_date': '2017-01-01T00:00:00.000Z',
            'end_date': '2017-12-31T00:00:00.000Z',
            'value': 408913833.8019222, 'unit_id': 15,
            'reporting_date': None,
            'metric_id': 860032, 'item_id': 274, 'region_id': 1215,
            'partner_region_id': 0, 'frequency_id': 9, 'source_id': 2,
            'belongs_to': {
                'metric_id': 860032,
                'item_id': 274,
                'region_id': 1215,
                'frequency_id': 9,
                'source_id': 2
            }
        }, {
            'start_date': '2017-01-01T00:00:00.000Z',
            'end_date': '2017-12-31T00:00:00.000Z',
            'value': 340614.19507563586, 'unit_id': 15,
            'reporting_date': None,
            'metric_id': 860032, 'item_id': 274, 'region_id': 1216,
            'partner_region_id': 0, 'frequency_id': 9, 'source_id': 2,
            'belongs_to': {
                'metric_id': 860032,
                'item_id': 274,
                'region_id': 1216,
                'frequency_id': 9,
                'source_id': 2
            }
        }]


@patch('api.client.lib.get_available', MagicMock(side_effect=mock_get_available))
@patch('api.client.lib.list_available', MagicMock(side_effect=mock_list_available))
@patch('api.client.lib.lookup', MagicMock(side_effect=mock_lookup))
@patch('api.client.lib.get_allowed_units', MagicMock(side_effect=mock_get_allowed_units))
@patch('api.client.lib.get_data_series', MagicMock(side_effect=mock_get_data_series))
@patch('api.client.lib.search', MagicMock(side_effect=mock_search))
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
        self.assertTrue('metric_id' in self.client.get_data_series()[0])

    def test_search(self):
        self.assertTrue(isinstance(self.client.search('regions', 'United')[0], dict))
        self.assertTrue('id' in self.client.search('regions', 'United')[0])

    def test_search_and_lookup(self):
        region = next(self.client.search_and_lookup('regions', 'United'))
        self.assertTrue(isinstance(region, dict))
        self.assertTrue('id' in region)
        self.assertEqual(region['name'], 'United States')

    def test_lookup_belongs(self):
        self.assertEqual(next(self.client.lookup_belongs('regions', 1215))['name'], 'World')

    def test_rank_series_by_source(self):
        series = next(self.client.rank_series_by_source([]))
        self.assertTrue('metric_id' in series)
        self.assertTrue('source_id' in series)

    def test_get_geo_centre(self):
        centre = self.client.get_geo_centre(1215)
        self.assertTrue(len(centre) == 1)
        self.assertTrue('centre' in centre[0])
        self.assertTrue('regionName' in centre[0])

    def test_get_geojson(self):
        geojson = self.client.get_geojson(1215)
        self.assertTrue('type' in geojson)
        self.assertTrue('type' in geojson['geometries'][0])
        self.assertTrue('coordinates' in geojson['geometries'][0])

    def test_get_descendant_regions(self):
        self.assertTrue('name' in self.client.get_descendant_regions(1215)[0])
        self.assertTrue('name' not in self.client.get_descendant_regions(1215, include_details=False)[0])

    def test_get_available_timefrequency(self):
        self.assertEqual(self.client.get_available_timefrequency()[0]['frequencyId'], 3)

    def test_get_top(self):
        self.assertEqual(self.client.get_top('regions',
                                             metric_id=860032,
                                             item_id=274,
                                             frequency_id=9,
                                             source_id=2)[0]['regionId'], 1215)

    def test_get_df(self):
        self.client.add_single_data_series({
            'metric_id': 860032,
            'item_id': 274,
            'region_id': 1215,
            'frequency_id': 9,
            'source_id': 2
        })
        df = self.client.get_df()
        self.assertEqual(df.iloc[0]['start_date'].date(), date(2017, 1, 1))
        self.client.add_single_data_series({
            'metric_id': 860032,
            'item_id': 274,
            'region_id': 1215,
            'frequency_id': 9,
            'source_id': 2
        })
        df = self.client.get_df(show_revisions=True)
        self.assertEqual(df.iloc[0]['start_date'].date(), date(2017, 1, 1))
        df = self.client.get_df(index_by_series=True)
        self.assertEqual(df.iloc[0]['start_date'].date(), date(2017, 1, 1))
        series = dict(zip(df.index.names, df.iloc[0].name))
        self.assertEqual(series, {
            'metric_id': 860032,
            'item_id': 274,
            'region_id': 1215,
            'partner_region_id': 0,
            'frequency_id': 9,
            'source_id': 2
        })

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
