try:
    # Python 3.3+
    from unittest.mock import patch, MagicMock
except ImportError:
    # Python 2.7
    from mock import patch, MagicMock
from datetime import date
import os
from unittest import TestCase

from groclient import GroClient
from groclient.utils import zip_selections
from groclient.mock_data import mock_entities, mock_data_series, mock_data_points

MOCK_HOST = "pytest.groclient.url"
MOCK_TOKEN = "pytest.groclient.token"


def mock_get_available(access_token, api_host, entity_type):
    return list(mock_entities[entity_type].values())


def mock_list_available(access_token, api_host, selected_entities):
    return [dict(data_series) for data_series in mock_data_series]


def mock_lookup(access_token, api_host, entity_type, entity_ids):
    try:
        entity_ids = list(entity_ids)
        return {
            str(entity_id): mock_entities[entity_type][entity_id]
            for entity_id in entity_ids
        }
    except TypeError:
        # Raises a KeyError if the requested entity hasn't been mocked:
        return mock_entities[entity_type][entity_ids]


def mock_get_allowed_units(access_token, api_host, metric_id, item_id):
    return [unit["id"] for unit in mock_entities["units"].values()]


def mock_get_data_series(access_token, api_host, **selection):
    return [dict(data_series) for data_series in mock_data_series]


def mock_search(access_token, api_host, entity_type, search_terms):
    return [
        {"id": entity["id"]}
        for entity in mock_entities[entity_type].values()
        if search_terms in entity["name"]
    ]


def mock_rank_series_by_source(access_token, api_host, selections_list):
    for data_series in mock_data_series:
        yield data_series


def mock_get_geo_centre(access_token, api_host, region_id):
    return [
         {"centre": [45.7228, -112.996], "regionId": 1215, "regionName": "United States"}
    ]


def mock_get_geojson(access_token, api_host, region_id, zoom_level):
    if zoom_level < 7:
        return {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "MultiPolygon", "coordinates": [[[[-38, -4]]]]}
            ],
        }
    else:
        return {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "MultiPolygon", "coordinates": [[[[-38.394, -4.225]]]]}
            ],
        }


def mock_get_geojsons(access_token, api_host, region_id, descendant_level, zoom_level):
    return [{'region_id': 13051, 'region_name': 'Alabama', 'centre': [32.7933, -86.8278],
             'geojson': {'type': 'MultiPolygon',
                         'coordinates': [[[[-88.201896667, 35.0088806150001], [-88.079490661, 35.006961823], [-87.987052917, 35.0075187690001], [-87.610366821, 35.0048713690001]]]]}},
            {'region_id': 13052, 'region_name': 'Alaska', 'centre': [64.2386, -152.279],
             'geojson': {'type': 'MultiPolygon',
                         'coordinates': [[[[-179.07043457, 51.2564086920001], [-179.094436645, 51.2270851140001], [-179.142776489, 51.2288894660001]]]]}}
    ]


def mock_get_descendant(
    access_token,
    api_host,
    entity_type,
    entity_id,
    distance,
    include_details,
):

    childs = [
            child
            for child in mock_entities[entity_type].values()
            if 119 in child["belongsTo"]
        ]
    if include_details:
        return childs
    else:
        return [{"id": child["id"]} for child in childs]


def mock_get_ancestor(
    access_token,
    api_host,
    entity_type,
    entity_id,
    distance,
    include_details,
):

    childs = [
            child
            for child in mock_entities[entity_type].values()
            if 12345 in child["contains"]
        ]
    if include_details:
        return childs
    else:
        return [{"id": child["id"]} for child in childs]


def mock_get_descendant_regions(
    access_token,
    api_host,
    region_id,
    descendant_level,
    include_historical,
    include_details,
):
    if descendant_level:
        regions = [
            region
            for region in mock_entities["regions"].values()
            if region["level"] == descendant_level
        ]
    else:
        regions = list(mock_entities["regions"].values())
    if not include_historical:
        regions = [region for region in regions if not region["historical"]]
    if include_details:
        return regions
    else:
        return [{"id": region["id"]} for region in regions]


def mock_get_available_timefrequency(access_token, api_host, **selection):
    return [
        {
            "start_date": "2000-02-18T00:00:00.000Z",
            "frequency_id": 3,
            "end_date": "2020-03-12T00:00:00.000Z",
            "name": "8-day",
        },
        {
            "start_date": "2019-09-02T00:00:00.000Z",
            "frequency_id": 1,
            "end_date": "2020-03-09T00:00:00.000Z",
            "name": "daily",
        },
    ]


def mock_get_top(access_token, api_host, entity_type, num_results, **selection):
    return [
        {
            "metricId": 860032,
            "itemId": 274,
            "regionId": 1215,
            "frequencyId": 9,
            "sourceId": 2,
            "value": 400,
            "unitId": 14,
        },
        {
            "metricId": 860032,
            "itemId": 274,
            "regionId": 1215,
            "frequencyId": 9,
            "sourceId": 2,
            "value": 395,
            "unitId": 14,
        },
        {
            "metricId": 860032,
            "itemId": 274,
            "regionId": 1215,
            "frequencyId": 9,
            "sourceId": 2,
            "value": 12,
            "unitId": 14,
        },
    ]


def mock_get_data_points(access_token, api_host, **selections):
    if isinstance(selections["region_id"], int):
        data_point = dict(mock_data_points[0])
        # set the data_point to use the selected region
        # other ids in mocked data points may not line up with selected ids
        data_point["region_id"] = selections["region_id"]
        return [data_point]
    elif isinstance(selections["region_id"], list):
        data_points = []
        for idx, region_id in enumerate(selections["region_id"]):
            # use mock_data_points[0] or mock_data_points[1] as a base depending if
            # index is even or odd
            data_point = dict(mock_data_points[idx % 2])
            data_point["region_id"] = region_id
            data_points.append(data_point)
        return data_points


@patch("groclient.lib.get_available", MagicMock(side_effect=mock_get_available))
@patch("groclient.lib.list_available", MagicMock(side_effect=mock_list_available))
@patch("groclient.lib.lookup", MagicMock(side_effect=mock_lookup))
@patch(
    "groclient.lib.get_allowed_units", MagicMock(side_effect=mock_get_allowed_units)
)
@patch("groclient.lib.get_data_series", MagicMock(side_effect=mock_get_data_series))
@patch("groclient.lib.search", MagicMock(side_effect=mock_search))
@patch(
    "groclient.lib.rank_series_by_source",
    MagicMock(side_effect=mock_rank_series_by_source),
)
@patch("groclient.lib.get_geo_centre", MagicMock(side_effect=mock_get_geo_centre))
@patch("groclient.lib.get_geojsons", MagicMock(side_effect=mock_get_geojsons))
@patch("groclient.lib.get_geojson", MagicMock(side_effect=mock_get_geojson))
@patch("groclient.lib.get_ancestor", MagicMock(side_effect=mock_get_ancestor))
@patch("groclient.lib.get_descendant", MagicMock(side_effect=mock_get_descendant))
@patch(
    "groclient.lib.get_descendant_regions",
    MagicMock(side_effect=mock_get_descendant_regions),
)
@patch(
    "groclient.lib.get_available_timefrequency",
    MagicMock(side_effect=mock_get_available_timefrequency),
)
@patch("groclient.lib.get_top", MagicMock(side_effect=mock_get_top))
@patch("groclient.lib.get_data_points", MagicMock(side_effect=mock_get_data_points))
class GroClientTests(TestCase):
    def setUp(self):
        self.client = GroClient(MOCK_HOST, MOCK_TOKEN)
        self.client._async_http_client = None  # Force tests to use synchronous http
        self.assertTrue(isinstance(self.client, GroClient))

    def test_get_logger(self):
        # should NOT raise any exception if get_logger correctly returns a logger object:
        self.client.get_logger().debug("Test output")

    def test_get_available(self):
        self.assertTrue("name" in self.client.get_available("units")[0])

    def test_list_available(self):
        self.assertTrue("metric_id" in self.client.list_available({})[0])

    def test_lookup(self):
        self.assertEqual(self.client.lookup("units", 10)["name"], "kilogram")

    def test_lookup_unit_abbreviation(self):
        self.assertEqual(self.client.lookup_unit_abbreviation(10), "kg")

    def test_get_allowed_units(self):
        self.assertTrue(isinstance(self.client.get_allowed_units(1, 1)[0], int))

    def test_get_data_series(self):
        self.assertTrue("metric_id" in self.client.get_data_series()[0])

    def test_search(self):
        self.assertTrue(isinstance(self.client.search("regions", "United")[0], dict))
        self.assertTrue("id" in self.client.search("regions", "United")[0])

    def test_search_and_lookup(self):
        region = next(self.client.search_and_lookup("regions", "United"))
        self.assertTrue(isinstance(region, dict))
        self.assertTrue("id" in region)
        self.assertEqual(region["name"], "United States")

    def test_lookup_belongs(self):
        self.assertEqual(
            next(self.client.lookup_belongs("regions", 1215))["name"], "World"
        )

    def test_rank_series_by_source(self):
        series = next(self.client.rank_series_by_source([]))
        self.assertTrue("metric_id" in series)
        self.assertTrue("source_id" in series)

    def test_get_geo_centre(self):
        centre = self.client.get_geo_centre(1215)
        self.assertTrue(len(centre) == 1)
        self.assertTrue("centre" in centre[0])
        self.assertTrue("regionName" in centre[0])

    def test_get_geojsons(self):
        geojsons = self.client.get_geojsons(1215, 4)
        self.assertTrue(len(geojsons) == 2)
        self.assertTrue("region_id" in geojsons[0])
        self.assertTrue("region_name" in geojsons[0])
        self.assertTrue("centre" in geojsons[0])
        self.assertTrue("geojson" in geojsons[0])
        self.assertTrue("type" in geojsons[0]["geojson"])
        self.assertTrue("coordinates" in geojsons[0]["geojson"])

    def test_get_geojson(self):
        geojson = self.client.get_geojson(1215)
        self.assertTrue("type" in geojson)
        self.assertTrue("type" in geojson["geometries"][0])
        self.assertTrue("coordinates" in geojson["geometries"][0])
        self.assertTrue(geojson["geometries"][0]['coordinates'][0][0][0] == [-38.394, -4.225])
        geojson = self.client.get_geojson(1215, 1)
        self.assertTrue("type" in geojson)
        self.assertTrue("type" in geojson["geometries"][0])
        self.assertTrue("coordinates" in geojson["geometries"][0])
        self.assertTrue(geojson["geometries"][0]['coordinates'][0][0][0] == [-38, -4])

    def test_get_ancestor(self):
        self.assertTrue("name" in self.client.get_descendant('metrics', 119)[0])
        self.assertTrue(
            "name"
            not in self.client.get_ancestor('regions', 12345, include_details=False)[0]
        )

    def test_get_descendant(self):
        self.assertTrue("name" in self.client.get_descendant('metrics', 119)[0])
        self.assertTrue(
            "name"
            not in self.client.get_descendant('metrics', 119, include_details=False)[0]
        )

    def test_get_descendant_regions(self):
        self.assertTrue("name" in self.client.get_descendant_regions(1215)[0])
        self.assertTrue(
            "name"
            not in self.client.get_descendant_regions(1215, include_details=False)[0]
        )

    def test_get_available_timefrequency(self):
        self.assertEqual(
            self.client.get_available_timefrequency()[0]["frequency_id"], 3
        )

    def test_get_top(self):
        self.assertEqual(
            self.client.get_top(
                "regions", metric_id=860032, item_id=274, frequency_id=9, source_id=2
            )[0]["regionId"],
            1215,
        )

    def test_get_df(self):
        self.client.add_single_data_series(mock_data_series[0])
        df = self.client.get_df()
        self.assertEqual(df.iloc[0]["start_date"].date(), date(2017, 1, 1))
        self.client.add_single_data_series(mock_data_series[0])
        df = self.client.get_df(show_revisions=True)
        self.assertEqual(df.iloc[0]["start_date"].date(), date(2017, 1, 1))
        indexed_df = self.client.get_df(index_by_series=True)
        self.assertEqual(indexed_df.iloc[0]["start_date"].date(), date(2017, 1, 1))
        series = zip_selections(indexed_df.iloc[0].name)
        self.assertEqual(series, mock_data_series[0])

    def test_get_df_show_revisions(self):
        self.client.add_single_data_series(mock_data_series[0])
        df = self.client.get_df(show_revisions=True)
        self.assertEqual(df.iloc[0]["start_date"].date(), date(2017, 1, 1))

    def test_get_df_show_available_date(self):
        self.client.add_single_data_series(mock_data_series[0])
        df = self.client.get_df(show_available_date=True)
        self.assertEqual(df.iloc[0]["available_date"].date(), date(2017, 12, 31))

    def test_add_points_to_df(self):
        self.client.add_points_to_df(None, mock_data_series[0], [])
        self.assertTrue(self.client.get_df().empty)
        self.assertTrue(self.client.get_df(show_revisions=True).empty)
        self.assertTrue(self.client.get_df(index_by_series=True).empty)

        data_points = self.client.get_data_points(**mock_data_series[0])
        self.client.add_points_to_df(None, mock_data_series[0], data_points)
        self.assertEqual(
            self.client.get_df().iloc[0]["start_date"].date(), date(2017, 1, 1)
        )
        self.assertEqual(
            self.client.get_df().iloc[0]["source_id"], 2
        )

    def test_get_data_points(self):
        # Gives the point's default unit if unit's not specified:
        data_points = self.client.get_data_points(**mock_data_series[0])
        self.assertEqual(data_points[0]["unit_id"], 14)
        self.assertEqual(data_points[0]["value"], 40891)

        # Converts to the given unit:
        selections = dict(
            mock_data_series[0]
        )  # make a copy so we don't modify the original
        selections["unit_id"] = 10
        data_points = self.client.get_data_points(**selections)
        self.assertEqual(data_points[0]["unit_id"], 10)
        self.assertEqual(data_points[0]["value"], 40891000)

    def test_GDH(self):
        df = self.client.GDH("860032-274-1215-0-9-2")
        self.assertEqual(df.iloc[0]["start_date"].date(), date(2017, 1, 1))
        # if you request a series with no data, an empty dataframe should be returned:
        # Extra options can be given, but value in the GDH key itself (metric_id/item_id/etc.)
        # should be ignored.
        df = self.client.GDH("860032-274-1215-0-2-9", insert_nulls=True, metric_id=1)
        self.assertEqual(len(df), 0)

    def test_add_single_data_series_adds_copy(self):
        selections = dict(mock_data_series[0])  # don't modify test data. Make a copy
        for region_id in [
            mock_data_series[0]["region_id"],
            mock_data_series[1]["region_id"],
        ]:
            # modify the original selections object
            selections["region_id"] = region_id
            # if add_single_data_series isn't making a copy of the selections passed in,
            # then this test should fail since the original reference has been modified.
            self.client.add_single_data_series(selections)
        self.assertEqual(
            len(self.client.get_df().drop_duplicates().region_id.unique()), 2
        )

    def test_add_single_data_series_allows_metadata(self):
        selections = dict(mock_data_series[0])
        selections['metadata'] = {'includes_historical_region': True}
        self.client.add_single_data_series(selections)
        self.assertEqual(len(self.client.get_df().item_id), 1)

    def test_get_data_series_list(self):
        self.client.add_single_data_series(mock_data_series[0])
        for key, value in self.client.get_data_series_list()[0].items():
            self.assertEqual(value, mock_data_series[0][key])

    def test_find_data_series(self):
        # TODO: when duplicates are removed, this should equal 2:
        self.assertEqual(
            len(
                list(
                    self.client.find_data_series(
                        metric="Production",
                        region="United",
                        start_date="2000-01-01",
                        end_date="2005-12-31",
                    )
                )
            ),
            8,
        )

        # TODO: when duplicates are removed, this should equal 2:
        def only_accept_production_quantity(search_result):
            return "metric_id" not in search_result or search_result["metric_id"] == 860032
        self.assertEqual(
            len(
                list(
                    self.client.find_data_series(
                        metric="Production",
                        result_filter=only_accept_production_quantity
                    )
                )
            ),
            8,
        )

    def test_add_data_series(self):
        # TODO: when duplicates are removed, this should equal 2:
        data_series = self.client.add_data_series(metric="Production", region="United")
        self.assertEqual(data_series, mock_data_series[0])
        for key, value in self.client.get_data_series_list()[0].items():
            self.assertEqual(value, mock_data_series[0][key])

    def test_search_for_entity(self):
        self.assertEqual(self.client.search_for_entity("metrics", "Production"), 860032)

    def test_get_provinces(self):
        self.assertEqual(
            self.client.get_provinces("United")[0], mock_entities["regions"][12345]
        )

    def test_get_names_for_selection(self):
        selection = {"metric_id": 860032, "region_id": 0}
        self.assertEqual(
            self.client.get_names_for_selection(selection),
            [("metric", "Production Quantity"), ("region", "World")],
        )

    def test_convert_unit(self):
        self.assertEqual(
            self.client.convert_unit({"value": 1, "unit_id": 10}, 10),
            {"value": 1, "unit_id": 10},
        )
        self.assertEqual(
            self.client.convert_unit({"value": 1, "unit_id": 10}, 14),
            {"value": 0.001, "unit_id": 14},
        )
        self.assertEqual(
            self.client.convert_unit({"value": 3, "unit_id": 36}, 37),
            {"value": 42, "unit_id": 37},
        )
        self.assertEqual(
            self.client.convert_unit({"value": 1, "unit_id": 37}, 36),
            {"value": -17.5, "unit_id": 36},
        )
        self.assertEqual(
            self.client.convert_unit({"value": 20, "unit_id": 10, "metadata": {"conf_interval": 2}}, 14),
            {"value": 0.02, "metadata": {"conf_interval": 0.002}, "unit_id": 14},
        )
        self.assertEqual(
            self.client.convert_unit({"value": 20, "unit_id": 10, "metadata": {}}, 14),
            {"value": 0.02, "metadata": {}, "unit_id": 14},
        )

        self.assertEqual(self.client.convert_unit({}, 36), {})

        with self.assertRaises(Exception):
            self.client.convert_unit({"value": 1, "unit_id": 10}, 43)

        self.assertEqual(
            self.client.convert_unit({"value": None, "unit_id": 37}, 36),
            {"value": None, "unit_id": 36},
        )

        with self.assertRaises(Exception):
            self.client.convert_unit({"value": None, "unit_id": 10}, 43)

class GroClientConstructorTests(TestCase):
    PROD_API_HOST = "api.gro-intelligence.com"

    # The most convenient method.
    @patch.dict(os.environ, {'GROAPI_TOKEN': MOCK_TOKEN})
    def test_no_host_and_env_token(self):
        client = GroClient()
        with patch("groclient.lib.get_available") as get_available:
            _ = client.get_available("items")
            get_available.assert_called_once_with(MOCK_TOKEN, self.PROD_API_HOST, "items")

    # A common use case: user passes an API token but no API host.
    def test_no_host_and_kwarg_token(self):
        client = GroClient(access_token=MOCK_TOKEN)
        with patch("groclient.lib.get_available") as get_available:
            _ = client.get_available("items")
            get_available.assert_called_once_with(MOCK_TOKEN, self.PROD_API_HOST, "items")

    def test_explicit_host_and_token(_self):
        client = GroClient(MOCK_HOST, MOCK_TOKEN)
        with patch("groclient.lib.get_available") as get_available:
            _ = client.get_available("items")
            get_available.assert_called_once_with(MOCK_TOKEN, MOCK_HOST, "items")

    def test_missing_token(self):
        # Explicitly unset GROAPI_TOKEN if it's set (eg, its set in our Shippable config).
        env_without_token = {k: v for k, v in os.environ.items() if k != "GROAPI_TOKEN"}
        with patch.dict(os.environ, env_without_token, clear=True):
            with self.assertRaisesRegex(RuntimeError, "environment variable must be set"):
                _ = GroClient(MOCK_HOST)
            with self.assertRaisesRegex(RuntimeError, "environment variable must be set"):
                _ = GroClient()
