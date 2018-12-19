from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue

from api.client import lib
import cfg

class Client(object):

    """API client with stateful authentication for lib functions. """

    __unit_names = {}

    def __init__(self, api_host, access_token):
        self.api_host = api_host
        self.access_token = access_token

    def get_available(self, entity_type):
        return lib.get_available(self.access_token, self.api_host, entity_type)

    def list_available(self, selected_entities):
        return lib.list_available(self.access_token, self.api_host, selected_entities)

    def lookup(self, entity_type, entity_id):
        return lib.lookup(self.access_token, self.api_host, entity_type, entity_id)

    def lookup_unit_abbreviation(self, unit_id):
        """Wrapper to lookup unit names, with local cache to avoid repeated lookups."""
        if unit_id not in self.__unit_names:
            self.__unit_names[unit_id] = self.lookup('units', unit_id)['abbreviation']
        return self.__unit_names[unit_id]

    def get_data_series(self, **selection):
        return lib.get_data_series(self.access_token, self.api_host, **selection)

    def get_data_points(self, **selection):
        return lib.get_data_points(self.access_token, self.api_host, **selection)

    def search(self, entity_type, search_terms):
        return lib.search(self.access_token, self.api_host,
                          entity_type, search_terms)

    def search_and_lookup(self, entity_type, search_terms):
        return lib.search_and_lookup(self.access_token, self.api_host,
                                     entity_type, search_terms)

    def lookup_belongs(self, entity_type, entity_id):
        return lib.lookup_belongs(self.access_token, self.api_host,
                                  entity_type, entity_id)

    def rank_series_by_source(self, series_list):
        return lib.rank_series_by_source(self.access_token, self.api_host,
                                         series_list)

    def get_geo_centre(self, region_id):
        return lib.get_geo_centre(self.access_token, self.api_host, region_id)

class BatchClient(Client):

    """API client with stateful authentication for lib functions. """

    def __init__(self, api_host, access_token):
        super(BatchClient, self).__init__(api_host, access_token)

    def batch_async_get_available(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.get_available, batched_args, output_list, map_result)

    def batch_async_list_available(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.list_available, batched_args, output_list, map_result)

    def batch_async_lookup(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.lookup, batched_args, output_list, map_result)

    def batch_async_get_data_series(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.get_data_series, batched_args, output_list, map_result)

    def batch_async_get_data_points(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.get_data_points, batched_args, output_list, map_result)

    def batch_async_search(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.search, batched_args, output_list, map_result)

    def batch_async_get_geo_centre(self, batched_args, output_list=None, map_result=None):
        return self.batch_async_queue(lib.get_geo_centre, batched_args, output_list, map_result)

    def batch_async_queue(self, func, batched_args, output_list, map_result):
        """
        Asynchronous version of get_data operating on multiple queries simultaneously.
        :param func:
        :param batched_args:
        :param output_list:
        :param map_result:
        :return:
        """

        # enter "batch mode" in lib.py
        cfg.ASYNC = True

        logger = lib.get_default_logger("batch_async")

        assert type(batched_args) is list, \
            "Only argument to a batch async decorated function should be a list of a list of the individual " \
            "non-keyword arguments being passed to the original function." \

        if output_list is None:
            output_list = [0] * len(batched_args)

        # Default is identity mapping into results list.
        if not map_result:
            def map_result(idx, query, response):
                output_list[idx] = response

        # Queue holds at most 1 second of queries as to not overload the server if it's "stuck"
        q = Queue(maxsize=cfg.MAX_QUERIES_PER_SECOND)

        @gen.coroutine
        def consumer():
            while True:
                idx, item = yield q.get()
                try:
                    logger.debug('Doing work on %s',str(idx))
                    if type(item) is dict:
                        result = yield func(self.access_token, self.api_host, **item)
                    else:
                        result = yield func(self.access_token, self.api_host, *item)
                    map_result(idx, item, result)
                except Exception as e:
                    # if it fails this many times... let it go.
                    print("ENCOUNTERED ERROR", e)
                    yield map_result(idx, item, None)
                finally:
                    q.task_done()

        @gen.coroutine
        def producer():
            """ Uses the interleaving pattern from https://www.tornadoweb.org/en/stable/guide/coroutines.html
            to place items in the queue at a fixed rate.
            """
            for idx, item in enumerate(batched_args):
                timer = gen.sleep(1.0 / float(cfg.MAX_QUERIES_PER_SECOND))  # Start the clock.
                yield q.put((idx, item))
                logger.debug('Put %i ' % idx)
                logger.debug("length of queue: %i " % q.qsize())
                yield timer
                logger.debug('Ready to put next')

        @gen.coroutine
        def main():
            # Start consumer without waiting (since it never finishes).
            for i in range(cfg.MAX_QUERIES_PER_SECOND):
                IOLoop.current().spawn_callback(consumer)
            yield producer()  # Wait for producer to put all tasks.
            yield q.join()  # Wait for consumer to finish all tasks.

        IOLoop.current().run_sync(main)

        # exit "batch mode" in lib.py
        cfg.ASYNC = False

        return output_list



