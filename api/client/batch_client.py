import time
import json

# Python3 support
try:
    # Python3
    from urllib.parse import urlencode
except ImportError:
    # Python2
    from urllib import urlencode

from tornado import gen
from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from api.client import cfg, lib
from api.client.gro_client import GroClient

class BatchClient(GroClient):
    """API client with support for batch asynchronous queries."""

    _logger = None
    _http_client = None

    def __init__(self, api_host, access_token):
        super(BatchClient, self).__init__(api_host, access_token)
        self._logger = lib.get_default_logger()
        self._http_client = AsyncHTTPClient()

    @gen.coroutine
    def get_data(self, url, headers, params=None):
        """General 'make api request' function.

        Assigns headers and builds in retries and logging.
        """
        base_log_record = dict(route=url, params=params)
        retry_count = 0
        self._logger.debug(url)

        # append version info
        headers.update(lib.get_version_info())

        while retry_count < cfg.MAX_RETRIES:
            start_time = time.time()
            http_request = HTTPRequest('{url}?{params}'.format(url=url, params=urlencode(params)),
                                       method="GET",
                                       headers=headers,
                                       request_timeout=cfg.TIMEOUT,
                                       connect_timeout=cfg.TIMEOUT)
            try:
                data = yield self._http_client.fetch(http_request)
                elapsed_time = time.time() - start_time
                log_record = dict(base_log_record)
                log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
                log_record['retry_count'] = retry_count
                log_record['status_code'] = data.code
                self._logger.debug('OK', extra=log_record)
                raise gen.Return(data.body)
            except HTTPError as e:
                elapsed_time = time.time() - start_time
                log_record = dict(base_log_record)
                log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
                log_record['retry_count'] = retry_count
                log_record['status_code'] = e.code
                if retry_count < cfg.MAX_RETRIES:
                    if hasattr(e, 'response') and hasattr(e.response, 'error'):
                        self._logger.warning(e.response.error, extra=log_record)
                    else:
                        self._logger.warning(e, extra=log_record)
                    retry_count += 1
                    if e.code in [429, 503, 504]:
                        time.sleep(2 ** retry_count)  # Exponential backoff
                    elif e.code == 301:
                        new_params = lib.redirect(
                            params,
                            json.loads(e.response.body.decode("utf-8"))['data'][0])
                        self._logger.warning(
                            'Redirecting {} to {}'.format(params, new_params),
                            extra=log_record)
                        params = new_params
                else:
                    self._logger.error(e.response.error, extra=log_record)
                    raise Exception('Giving up on {} after {} tries. \
                        Error is: {}.'.format(
                        url, retry_count, e.response.error))


    @gen.coroutine
    def get_data_points(self, **selection):
        """Get all the data points for a given selection, which is some or all
        of: item_id, metric_id, region_id, frequency_id, source_id,
        partner_region_id. Additional arguments are allowed and ignored.
        """
        data_points = super(BatchClient, self).get_data_points(**selection)
        raise gen.Return(data_points)

    def get_df(self, show_revisions=True):
        if show_revisions:
            for data_series in self._data_series_queue:
                data_series['show_revisions'] = True
        return self.batch_async_queue(self.get_data_points, self._data_series_queue,
                                      self._data_frame, self.add_points_to_df)

    # TODO: deprecate  the following  two methods, standardize  on one
    # approach with get_data_points and get_df
    @gen.coroutine
    def get_data_points_generator(self, **selection):
        headers = {'authorization': 'Bearer ' + self.access_token}
        url = '/'.join(['https:', '', self.api_host, 'v2/data'])
        params = lib.get_data_call_params(**selection)
        resp = yield self.get_data(url, headers, params)
        list_of_series_points = json_decode(resp)
        include_historical = selection.get('include_historical', True)
        points = lib.list_of_series_to_single_series(list_of_series_points, False,
                                                     include_historical)
        raise gen.Return(points)

    def batch_async_get_data_points(self, batched_args, output_list=None,
                                    map_result=None):
        """Make many :meth:`~get_data_points` requests asynchronously.

        Parameters
        ----------
        batched_args : list of dicts
            Each dict should be a `selections` object like would be passed to
            :meth:`~get_data_points`.

            Example::

                input_list = [
                    {'metric_id': 860032, 'item_id': 274, 'region_id': 1215, 'frequency_id': 9, 'source_id': 2},
                    {'metric_id': 860032, 'item_id': 270, 'region_id': 1215, 'frequency_id': 9, 'source_id': 2}
                ]

        output_list : any, optional
            A custom accumulator to use in map_result. For example: may pass in a non-empty list
            to append results to it, or may pass in a pandas dataframe, etc. By default, is a list
            of n 0s, where n is the length of batched_args.
        map_result : function, optional
            Function to apply changes to individual requests' responses before returning.
            Takes 4 params:
            1. the index in batched_args
            2. the element from batched_args
            3. the result from that input
            4. `output_list`. The accumulator of all results

            Example::

                output_list = []

                # Merge all responses into a single list
                def map_response(inputIndex, inputObject, response, output_list):
                    output_list += response
                    return output_list

                batch_output = client.batch_async_get_data_points(input_list,
                                                                  output_list=output_list,
                                                                  map_result=map_response)

        Returns
        -------
        any
            By default, returns a list of lists of data points. Likely either objects or lists of
            dictionaries. If using a custom map_result function, can return any type.

            Example of the default output format::

                [
                    [
                        {'metric_id': 1, 'item_id': 2, 'start_date': 2000-01-01, 'value': 41, ...},
                        {'metric_id': 1, 'item_id': 2, 'start_date': 2001-01-01, 'value': 39, ...},
                        {'metric_id': 1, 'item_id': 2, 'start_date': 2002-01-01, 'value': 50, ...},
                    ],
                    [
                        {'metric_id': 1, 'item_id': 6, 'start_date': 2000-01-01, 'value': 12, ...},
                        {'metric_id': 1, 'item_id': 6, 'start_date': 2001-01-01, 'value': 13, ...},
                        {'metric_id': 1, 'item_id': 6, 'start_date': 2002-01-01, 'value': 4, ...},
                    ],
                ]

        """
        return self.batch_async_queue(self.get_data_points_generator, batched_args, output_list,
                                      map_result)

    @gen.coroutine
    def async_rank_series_by_source(self, *selections_list):
        """Get all sources, in ranked order, for a given selection."""
        response = super(BatchClient, self).rank_series_by_source(selections_list)
        raise gen.Return(list(response))

    def batch_async_rank_series_by_source(self, batched_args,
                                          output_list=None, map_result=None):
        """Perform multiple rank_series_by_source requests asynchronously.

        Parameters
        ----------
        batched_args : list of lists of dicts
            See :meth:`~.rank_series_by_source` `selections_list`. A list of those lists.

        """
        return self.batch_async_queue(self.async_rank_series_by_source, batched_args,
                                      output_list, map_result)

    def batch_async_queue(self, func, batched_args, output_list, map_result):
        """Asynchronously call func.

        Parameters
        ----------
        func : function
            The function to be batched. Typically a Client method.
        batched_args : list of dicts
            Inputs
        output_list : any, optional
            A custom accumulator to use in map_result. For example: may pass in a non-empty list
            to append results to it, or may pass in a pandas dataframe, etc. By default, is a list
            of n 0s, where n is the length of batched_args.
        map_result : function, optional
            Function to apply changes to individual requests' responses before returning. Must
            return an accumulator, like a map() function.
            Takes 4 params:
            1. the index in batched_args
            2. the element from batched_args
            3. the result from that input
            4. `output_list`. The accumulator of all results

        """
        assert type(batched_args) is list, \
            "Only argument to a batch async decorated function should be a \
            list of a list of the individual non-keyword arguments being \
            passed to the original function."

        # Wrap output_list in an object so it can be modified within inner functions' scope
        # In Python 3, can accomplish the same thing with `nonlocal` keyword.
        output_data = {}
        if output_list is None:
            output_data['result'] = [0] * len(batched_args)
        else:
            output_data['result'] = output_list

        if not map_result:
            # Default map_result function separates output by index of the query. For example:
            # batched_args: [exports of corn, exports of soybeans]
            # accumulator: [[corn datapoint, corn datapoint],
            #               [soybean data point, soybean data point]]
            def map_result(idx, query, response, accumulator):
                accumulator[idx] = response
                return accumulator

        q = Queue()

        @gen.coroutine
        def consumer():
            """Execute func on all items in queue asynchronously."""
            while q.qsize():
                idx, item = q.get().result()
                self._logger.debug('Doing work on {}'.format(idx))
                if type(item) is dict:
                    # Assume that dict types should be unpacked as kwargs
                    result = yield func(**item)
                elif type(item) is list:
                    # Assume that list types should be unpacked as positional args
                    result = yield func(*item)
                else:
                    result = yield func(item)
                output_data['result'] = map_result(idx, item, result, output_data['result'])
                self._logger.debug('Done with {}'.format(idx))
                q.task_done()

        def producer():
            """Immediately enqueue the whole batch of requests."""
            lasttime = time.time()
            for idx, item in enumerate(batched_args):
                q.put((idx, item))
            elapsed = time.time() - lasttime
            self._logger.info("Queued {} requests in {}".format(q.qsize(), elapsed))

        @gen.coroutine
        def main():
            # Start consumer without waiting (since it never finishes).
            for i in range(cfg.MAX_QUERIES_PER_SECOND):
                IOLoop.current().spawn_callback(consumer)
            producer()  # Wait for producer to put all tasks.
            yield q.join()  # Wait for consumer to finish all tasks.

        IOLoop.current().run_sync(main)

        return output_data['result']
