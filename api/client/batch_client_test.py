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

from api.client.batch_client import BatchClient, BatchError

MOCK_HOST = 'pytest.groclient.url'
MOCK_TOKEN = 'pytest.groclient.token'

mock_list_of_series_points = [
    {
        'series': {
            'metricId': 860032, 'itemId': 274, 'regionId': 1215,
            'partnerRegionId': 0, 'frequencyId': 9, 'sourceId': 2,
            'unitId': 14,
            'belongsTo': {
                'metricId': 860032,
                'itemId': 274,
                'regionId': 1215,
                'frequencyId': 9,
                'sourceId': 2
            }
        }, 'data': [
            ['2017-01-01T00:00:00.000Z', '2017-12-31T00:00:00.000Z', 40891, None, 14, {}],
            ['2018-01-01T00:00:00.000Z', '2018-12-31T00:00:00.000Z', 56789, '2019-03-14T00:00:00.000Z', 10, {}],
        ]
    }
]

mock_data_series = [
    {
        'metric_id': 860032,  # TODO: add names
        'item_id': 274,
        'region_id': 1215,
        'partner_region_id': 0,
        'frequency_id': 9,
        'source_id': 2
    }, {
        'metric_id': 860032,  # TODO: add names
        'item_id': 274,
        'region_id': 1216,
        'partner_region_id': 0,
        'frequency_id': 9,
        'source_id': 2
    }
]

ERROR_SELECTION = {
    'metric_id': 1,
    'item_id': -15,
    'region_id': 3,
    'frequency_id': 4,
    'source_id': 5
}

def mock_rank_series_by_source(access_token, api_host, selections_list):
    for data_series in mock_data_series:
        yield data_series


def mock_tornado_fetch(request):
    future = Future()
    error_url = ('https://{}/v2/data?metricId={metric_id}'
                 '&itemId={item_id}'
                 '&regionId={region_id}'
                 '&frequencyId={frequency_id}'
                 '&sourceId={source_id}'
                 '&responseType=list_of_series'.format(MOCK_HOST, **ERROR_SELECTION))
    if request.url == error_url:
        raise HTTPError(400, 'Negative item ids are not allowed', request)
    else:
        response = HTTPResponse(request, 200, buffer=StringIO(json.dumps(mock_list_of_series_points)))
    future.set_result(response)
    return future


@patch('api.client.lib.rank_series_by_source', MagicMock(side_effect=mock_rank_series_by_source))
@patch('tornado.httpclient.AsyncHTTPClient.fetch', MagicMock(side_effect=mock_tornado_fetch))
class GroClientTests(TestCase):
    def setUp(self):
        self.client = BatchClient(MOCK_HOST, MOCK_TOKEN)
        self.assertTrue(isinstance(self.client, BatchClient))

    def test_batch_async_get_data_points(self):
        data_points = self.client.batch_async_get_data_points([
            {
                'metric_id': 1,
                'item_id': 2,
                'region_id': 3,
                'frequency_id': 4,
                'source_id': 5
            }, {
                'metric_id': 6,
                'item_id': 7,
                'region_id': 8,
                'frequency_id': 9,
                'source_id': 10,
                'insert_nulls': True
            }
        ])
        self.assertEquals(data_points[0][0]['start_date'], '2017-01-01T00:00:00.000Z')
        self.assertEquals(data_points[0][0]['end_date'], '2017-12-31T00:00:00.000Z')
        self.assertEquals(data_points[0][0]['value'], 40891)
        self.assertEquals(data_points[0][0]['unit_id'], 14)
        self.assertEquals(data_points[0][0]['reporting_date'], None)
        self.assertEquals(data_points[0][1]['start_date'], '2018-01-01T00:00:00.000Z')
        self.assertEquals(data_points[0][1]['end_date'], '2018-12-31T00:00:00.000Z')
        self.assertEquals(data_points[0][1]['value'], 56789)
        self.assertEquals(data_points[0][1]['unit_id'], 14)
        self.assertEquals(data_points[0][1]['reporting_date'], '2019-03-14T00:00:00.000Z')

    def test_batch_async_get_data_points_map_function(self):

        def sum_results(inputIndex, inputObject, response, summation):
            for point in response:
                summation += point['value']
            return summation

        summation = self.client.batch_async_get_data_points(
            [{'metric_id': 1, 'item_id': 2, 'region_id': 3, 'frequency_id': 4, 'source_id': 5}],
            output_list=0,
            map_result=sum_results
        )

        self.assertEquals(summation, 97680)

    def test_batch_async_get_data_points_bad_request_error(self):
        responses = self.client.batch_async_get_data_points([ERROR_SELECTION])
        self.assertTrue(isinstance(responses[0], BatchError))

    def test_get_df(self):
        client = BatchClient(MOCK_HOST, MOCK_TOKEN)
        client.add_single_data_series({
            'metric_id': 1,
            'item_id': 2,
            'region_id': 3,
            'frequency_id': 4,
            'source_id': 5
        })
        df = client.get_df()
        self.assertEqual(df.iloc[0]['start_date'].date(), date(2017, 1, 1))
        self.assertEqual(df.iloc[0]['end_date'].date(), date(2017, 12, 31))
        self.assertEqual(df.iloc[0]['value'], 40891)


    def test_batch_async_rank_series_by_source(self):
        list_of_ranked_series_lists = self.client.batch_async_rank_series_by_source(
            [mock_data_series, mock_data_series]
        )
        # There were two inputs, so there should be two outputs:
        self.assertEquals(len(list_of_ranked_series_lists), 2)
        for series_list in list_of_ranked_series_lists:
            # Not necessarily true, but true given the mock_rank_series_by_source() function:
            self.assertEquals(len(series_list), len(mock_data_series))
            for series in series_list:
                self.assertTrue('metric_id' in series)
                self.assertTrue('source_id' in series)