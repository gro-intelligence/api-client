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
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
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
            except HTTPClientError as e:
                elapsed_time = time.time() - start_time
                log_record = dict(base_log_record)
                log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
                log_record['retry_count'] = retry_count
                log_record['status_code'] = e.code
                if retry_count < cfg.MAX_RETRIES:
                    self._logger.warning(e.response.error, extra=log_record)
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
        headers = {'authorization': 'Bearer ' + self.access_token}
        url = '/'.join(['https:', '', self.api_host, 'v2/data'])
        params = lib.get_data_call_params(**selection)
        resp = yield lib.list_of_series_to_single_series(self.get_data(url, headers, params))
        raise gen.Return(json_decode(resp))

    def batch_async_get_data_points(self, batched_args, output_list=None,
                                    map_result=None):
        return self.batch_async_queue(self.get_data_points, batched_args,
                                      output_list, map_result)

    @gen.coroutine
    def async_rank_series_by_source(self, **selection):
        """Get all sources, in ranked order, for a given selection."""
        response = super(BatchClient, self).rank_series_by_source(**selection)
        raise gen.Return([r for r in response])

    def batch_async_rank_series_by_source(self, batched_args,
                                       output_list=None, map_result=None):
        return self.batch_async_queue(self.async_rank_series_by_source, batched_args,
                                      output_list, map_result)

    def batch_async_queue(self, func, batched_args, output_list, map_result):
        """Asynchronously call func.

        :param func: function to be called on each member of batched_args
        :param batched_args: list of keyword arguments dictionaries, one for
        each call to func
        :param output_list:
        :param map_result:
        :return:

        """
        assert type(batched_args) is list, \
            "Only argument to a batch async decorated function should be a \
            list of a list of the individual non-keyword arguments being \
            passed to the original function."

        # Default is identity mapping into results list.
        if not map_result:
            if output_list is None:
                output_list = [0] * len(batched_args)

            def map_result(idx, query, response):
                output_list[idx] = response

        q = Queue()

        @gen.coroutine
        def consumer():
            """Execute func on all items in queue asynchronously."""
            while q.qsize():
                idx, item = q.get().result()
                self._logger.debug('Doing work on {}'.format(idx))
                if type(item) is dict:
                    result = yield func(**item)
                else:
                    result = yield func(*item)
                map_result(idx, item, result)
                self._logger.debug('Done with {}'.format(idx))
                q.task_done()

        def producer():
            """Immediately enqueue the whole batch of requests."""
            lasttime = time.time()
            for idx, item in enumerate(batched_args):
                q.put((idx, item))
            elapsed = time.time() - lasttime
            self._logger.info("Queued {} requests in {}".format(q.qsize(),
                                                                elapsed))

        @gen.coroutine
        def main():
            # Start consumer without waiting (since it never finishes).
            for i in range(cfg.MAX_QUERIES_PER_SECOND):
                IOLoop.current().spawn_callback(consumer)
            producer()  # Wait for producer to put all tasks.
            yield q.join()  # Wait for consumer to finish all tasks.

        IOLoop.current().run_sync(main)

        return output_list
