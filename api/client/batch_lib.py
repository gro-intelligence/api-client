import Queue
from api.client.lib import *
from tornado import ioloop, httpclient
from tornado.escape import json_decode
from tornado.httputil import url_concat

MAX_RETRIES = 4
MAX_QUERIES_PER_SECOND = 10

# Batch/Async functions equivalent to those in lib.

def batch_async_get_data(queries, results, map_returned):
    """Same as get_data_points, but operates over batches of requests and does this in async for faster retrieval."""

    http_client = httpclient.AsyncHTTPClient()
    logger = get_default_logger()

    # Pre-init array to store the results in.
    counter = [0]
    num_queries = len(queries)

    # If data is missing we have certain data points which are NOT USABLE
    invalid_idx = []

    # Queue for feeding our "thread" (which are not really threads)
    q = Queue.Queue()

    # Minimum time between requests for given QPS ceiling. 25% extra for overhead due to context switching.
    delta = 1.0 / (MAX_QUERIES_PER_SECOND * 1.25)
    logger.info("min delta between requests = %ss" % delta)

    # Callback function to add data to queue.
    def _feed_queue(idx, noop, previous_time):

        # exhausted all queries
        if idx == len(queries):
            return

        # if we aren't skipping current iteration
        if not noop:
            q.put(queries[idx])

        if q.qsize() > MAX_QUERIES_PER_SECOND or (q.qsize() > int(MAX_QUERIES_PER_SECOND/2) and noop):
            if not noop:
                logger.info("Potential API server performance limit. Pausing queue.")
            # there's a backlog of sorts. let's wait one delta iteration.
            ioloop.IOLoop.instance().call_later(delta, lambda: _feed_queue(idx, True, previous_time))
        else:
            if idx % 100 == 0 and idx != 0:
                logger.info("Done %s queries. QPS: %.2f" % (idx, float(100)/(time.time() - previous_time)))
                previous_time = time.time()
            idx += 1
            ioloop.IOLoop.instance().call_later(delta, lambda: _feed_queue(idx, False, previous_time))

        return

    # Function to add data to our results data structure
    def _process_result(query, response):
        try:
            response = json_decode(response.body)

            # if type(response) != list:
            #     # more failures ...
            #     logger.error("Decoded JSON was not a list. Odd. Looks like this: %s" % str(response))
            #     raise Exception("Returned JSON not a list: %s" % str(response))
        except Exception as e:
            # This request clearly failed. Let's run it agains
            logger.error("Request for %i failed! Adding url back to queue: %s" %
                         (query[0], url_concat(query[2], query[3])))
            q.put(query)
            ioloop.IOLoop.instance().spawn_callback(_send_request)
            return

        map_returned(query, results, response)

        # don't need this anymore. if the queue is empty let them die...
        # Updated our counter.
        counter[0] += 1
        if counter[0] == num_queries:
            logger.info("Ending async events loop.")
            ioloop.IOLoop.instance().stop()
            return

        ioloop.IOLoop.instance().spawn_callback(_send_request)

    # Function to send a request with the http lib.
    def _send_request():
        # We check the queue. If there's more stuff for us to do - let's set about doing it.
        # Otherwise we die our death having served the cause proudly.
        if not q.empty():
            query = q.get()
            (idx, headers, url, params) = query
            url = url_concat(url, params)

            http_client.fetch(url.strip(),
                              (lambda response, query=query: _process_result(query, response)),
                              method='GET',
                              headers=headers, raise_error=False)
            return

        logger.debug("Queue exhausted, let's check again in 2 seconds.")
        ioloop.IOLoop.instance().call_later(2.0, _send_request)

        return

    # Starting feeder
    logger.info("Starting queue feeder.")
    ioloop.IOLoop.instance().spawn_callback(lambda idx=0: _feed_queue(idx, False, time.time()))

    # starting request threads
    logger.info("Starting request 'threads'.")
    for i in range(0, MAX_QUERIES_PER_SECOND * 3):
        ioloop.IOLoop.instance().call_at(time.time() + 1.0 + i * 10 * delta, _send_request)

    # setting everything in motion
    logger.info("Starting async event loop.")
    ioloop.IOLoop.instance().start()

    return invalid_idx


def batch_get_data_points(access_token, api_host, selections, results, map_returned=None):
    """Get all the data points for a given selection, which is some or all
      of: item_id, metric_id, region_id, frequency_id, source_id,
      partner_region_id. Additional arguments are allowed and ignored.
    """

    # TODO support crop calendar
    # if (selection['metric_id'] == CROP_CALENDAR_METRIC_ID):
    #     return get_crop_calendar_data_points(access_token, api_host, **selection)

    queries = []

    if len(selections) > 0 and type(selections[0]) != tuple:
        selections = enumerate(selections)

    for idx, selection in selections:
        headers = {'authorization': 'Bearer ' + access_token}
        url = '/'.join(['https:', '', api_host, 'v2/data'])
        params = get_data_call_params(**selection)
        queries.append((idx, headers, url, params))

    # Default is identity mapping into results list.
    if not map_returned:
        def map_returned(query, results, response):
            results[query[0]] = response

    batch_async_get_data(queries, results, map_returned)

    return results


def batch_lookup(access_token, api_host, entities, results, map_returned=None):
    """Given an entity_type, which is one of 'items', 'metrics',
  'regions', 'units', or 'sources', returns a JSON dict with the
  list of available entities of the given type.
  """

    queries = []

    if len(entities) > 0 and (type(entities[0][1]) != tuple):
        entities = enumerate(entities)

    for idx, entity in entities:
        (entity_type, entity_id) = entity
        url = '/'.join(['https:', '', api_host, 'v2', entity_type, str(entity_id)])
        headers = {'authorization': 'Bearer ' + access_token}
        queries.append((idx, headers, url, {}))

    # Default is identity mapping into results list from data attribute.
    if not map_returned:
        def map_returned(query, results, response):
            results[query[0]] = response['data']

    batch_async_get_data(queries, results, map_returned)

    return results
