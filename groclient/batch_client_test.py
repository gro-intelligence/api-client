try:
    # Python 3.3+
    from unittest.mock import patch, MagicMock
    from io import StringIO
except ImportError:
    # Python 2.7
    from mock import patch, MagicMock
    from StringIO import StringIO
from unittest import TestCase
import json
from datetime import date

from tornado.httpclient import HTTPResponse, HTTPError
from tornado.concurrent import Future
from tornado.ioloop import IOLoop

from groclient import GroClient
from groclient.client import BatchError
from groclient.utils import str_camel_to_snake
from groclient.mock_data import (
    mock_list_of_series_points,
    mock_data_series,
    mock_error_selection,
)

MOCK_HOST = "pytest.groclient.url"
MOCK_TOKEN = "pytest.groclient.token"


def mock_rank_series_by_source(access_token, api_host, selections_list):
    for data_series in mock_data_series:
        yield data_series


def mock_tornado_fetch(request):
    future = Future()
    query_params = {
        str_camel_to_snake(key): value
        for key, value in [
            query_param.split("=")
            for query_param in request.url.split("?")[1].split("&")
        ]
    }
    if int(query_params.get("item_id", 0)) < 0:
        raise HTTPError(400, "Negative item ids are not allowed", request)
    else:
        response = HTTPResponse(
            request, 200, buffer=StringIO(json.dumps(mock_list_of_series_points))
        )
    future.set_result(response)
    return future


@patch(
    "groclient.lib.rank_series_by_source",
    MagicMock(side_effect=mock_rank_series_by_source),
)
@patch(
    "tornado.httpclient.AsyncHTTPClient.fetch",
    MagicMock(side_effect=mock_tornado_fetch),
)
class BatchTests(TestCase):
    def setUp(self):
        self.client = GroClient(MOCK_HOST, MOCK_TOKEN)
        self.assertTrue(isinstance(self.client, GroClient))

    def tearDown(self):
        IOLoop.clear_current()

    def test_batch_async_get_data_points(self):
        data_points = self.client.batch_async_get_data_points(
            [
                {
                    "metric_id": 1,
                    "item_id": 2,
                    "region_id": 3,
                    "frequency_id": 4,
                    "source_id": 5,
                },
                {
                    "metric_id": 6,
                    "item_id": 7,
                    "region_id": 8,
                    "frequency_id": 9,
                    "source_id": 10,
                    "insert_nulls": True,
                },
            ]
        )
        self.assertEqual(data_points[0][0]["start_date"], "2017-01-01T00:00:00.000Z")
        self.assertEqual(data_points[0][0]["end_date"], "2017-12-31T00:00:00.000Z")
        self.assertEqual(data_points[0][0]["value"], 40891)
        self.assertEqual(data_points[0][0]["unit_id"], 14)
        self.assertEqual(data_points[0][0]["reporting_date"], None)
        self.assertEqual(data_points[0][1]["start_date"], "2018-01-01T00:00:00.000Z")
        self.assertEqual(data_points[0][1]["end_date"], "2018-12-31T00:00:00.000Z")
        self.assertEqual(data_points[0][1]["value"], 56789)
        self.assertEqual(data_points[0][1]["unit_id"], 10)
        self.assertEqual(
            data_points[0][1]["reporting_date"], "2019-03-14T00:00:00.000Z"
        )

    def test_batch_async_get_data_points_map_function(self):
        def sum_results(inputIndex, inputObject, response, summation):
            for point in response:
                summation += point["value"]
            return summation

        summation = self.client.batch_async_get_data_points(
            [
                {
                    "metric_id": 1,
                    "item_id": 2,
                    "region_id": 3,
                    "frequency_id": 4,
                    "source_id": 5,
                }
            ],
            output_list=0,
            map_result=sum_results,
        )

        self.assertEqual(summation, 97680)

    # Test that multiple GroClients each have their own AsyncHTTPClient. Note:
    # this tests the fix for the `fetch called on closed AsyncHTTPClient`
    # error. We can't test for that directly since the `fetch` call is mocked,
    # so instead we just ensure that all GroClients have their own
    # AsyncHTTPClient.
    def test_batch_async_get_data_points_multiple_clients(self):
        client = GroClient(MOCK_HOST, MOCK_TOKEN)
        ahc_id1 = id(client._async_http_client)
        client = GroClient(MOCK_HOST, MOCK_TOKEN)
        ahc_id2 = id(client._async_http_client)
        self.assertNotEqual(ahc_id1, ahc_id2)

    def test_batch_async_get_data_points_bad_request_error(self):
        responses = self.client.batch_async_get_data_points([mock_error_selection])
        self.assertTrue(isinstance(responses[0], BatchError))

    def test_batch_async_get_data_points_map_errors(self):
        def raise_exception(idx, query, response, accumulator):
            if isinstance(response, Exception):
                raise response
            accumulator[idx] = response
            return accumulator

        with self.assertRaises(Exception):
            self.client.batch_async_get_data_points(
                [mock_error_selection], map_result=raise_exception
            )

    def test_async_get_df(self):
        self.client.add_single_data_series(
            {
                "metric_id": 1,
                "item_id": 2,
                "region_id": 3,
                "frequency_id": 4,
                "source_id": 5,
            }
        )
        df = self.client.async_get_df()
        self.assertEqual(df.iloc[0]["start_date"].date(), date(2017, 1, 1))
        self.assertEqual(df.iloc[0]["end_date"].date(), date(2017, 12, 31))
        self.assertEqual(df.iloc[0]["value"], 40891)

    def test_batch_async_rank_series_by_source(self):
        list_of_ranked_series_lists = self.client.batch_async_rank_series_by_source(
            [mock_data_series, mock_data_series]
        )
        # There were two inputs, so there should be two outputs:
        self.assertEqual(len(list_of_ranked_series_lists), 2)
        for series_list in list_of_ranked_series_lists:
            # Not necessarily true, but true given the mock_rank_series_by_source() function:
            self.assertEqual(len(series_list), len(mock_data_series))
            for series in series_list:
                self.assertTrue("metric_id" in series)
                self.assertTrue("source_id" in series)
