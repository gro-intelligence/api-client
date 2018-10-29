import Queue
import logging
import numpy as np
import random

import requests
import sys
import time
from datetime import datetime

from tornado import ioloop, httpclient, gen
from tornado.escape import json_decode
from tornado.httputil import url_concat

MAX_RETRIES = 4
MAX_QUERIES_PER_SECOND = 10
DEFAULT_LOG_LEVEL = logging.INFO  # change to DEBUG for more detail

CROP_CALENDAR_METRIC_ID = 2260063


def get_default_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(DEFAULT_LOG_LEVEL)
    stderr_handler = logging.StreamHandler()
    logger_root = logging.getLogger()
    if not logger_root.handlers:
        logger_root.addHandler(stderr_handler)
    return logger


def get_access_token(api_host, user_email, user_password, logger=None):
    retry_count = 0
    if not logger:
        logger = get_default_logger()
    while retry_count < MAX_RETRIES:
        login = requests.post('https://' + api_host + '/login',
                              data={"email": user_email, "password": user_password})
        if login.status_code == 200:
            logger.debug("Authentication succeeded in get_access_token")
            return login.json()['data']['accessToken']
        else:
            logger.warning("Error in get_access_token: {}".format(login))
        retry_count += 1
    raise Exception("Giving up on get_access_token after {0} tries.".format(retry_count))


def get_data(url, headers, params=None, logger=None):
    """General 'make api request' function. Assigns headers and builds in retries and logging."""
    base_log_record = dict(route=url, params=params)
    retry_count = 0
    if not logger:
        logger = get_default_logger()
    logger.debug(url)
    while retry_count < MAX_RETRIES:
        start_time = time.time()
        data = requests.get(url, params=params, headers=headers, timeout=None)
        elapsed_time = time.time() - start_time
        log_record = dict(base_log_record)
        log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
        log_record['retry_count'] = retry_count
        log_record['status_code'] = data.status_code
        if data.status_code == 200:
            logger.debug('OK', extra=log_record)
            return data
        retry_count += 1
        log_record['tag'] = 'failed_gro_api_request'
        if retry_count < MAX_RETRIES:
            logger.warning(data.text, extra=log_record)
        else:
            logger.error(data.text, extra=log_record)
    raise Exception('Giving up on {} after {} tries. Error is: {}.'.format(url, retry_count, data.text))


def get_available(access_token, api_host, entity_type):
    """Given an entity_type, which is one of 'items', 'metrics',
    'regions', returns a JSON dict with the list of available entities
    of the given type.
    """
    url = '/'.join(['https:', '', api_host, 'v2', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers).json()
    return resp['data']


def list_available(access_token, api_host, selected_entities):
    """List available entities given some selected entities. Given a dict
  of selected entity ids of the form { <entity_type>: <entity_id>,
  ...}, returns a list of dictionaries representing available {
  item_id: ..., metric_id: ... , region_id: ... ,} for which data
  series are available which satisfy the input selection.
  """
    url = '/'.join(['https:', '', api_host, 'v2/entities/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, selected_entities).json()
    try:
        return resp['data']
    except KeyError as e:
        raise Exception(resp.text)


def lookup(access_token, api_host, entity_type, entity_id):
    """Given an entity_type, which is one of 'items', 'metrics',
  'regions', 'units', or 'sources', returns a JSON dict with the
  list of available entities of the given type.
  """
    url = '/'.join(['https:', '', api_host, 'v2', entity_type, str(entity_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers).json()
    try:
        return resp['data']
    except KeyError as e:
        raise Exception(resp.text)


def snake_to_camel(term):
    """Converts hello_world to helloWorld."""
    camel = ''.join(term.title().split('_'))
    return camel[0].lower() + camel[1:]


def get_params_from_selection(**selection):
    """Construct http request params from dict of entity selections. For use with get_data_series()
  and rank_series_by_source().
  """
    params = {}
    for key, value in selection.items():
        if key in ('region_id', 'partner_region_id', 'item_id', 'metric_id'):
            params[snake_to_camel(key)] = value
    return params


def get_crop_calendar_params(**selection):
    """Construct http request params from dict of entity selections. Only region and item are required
  since metric/item/source/frequency all have default values and start/end date are not allowed
  inputs since crop calendars are static.
  """
    params = {}
    for key, value in selection.items():
        if key in ('region_id', 'item_id'):
            params[snake_to_camel(key)] = value
    return params


def get_data_call_params(**selection):
    """Construct http request params from dict of entity selections. For use with get_data_points().
  """
    params = get_params_from_selection(**selection)
    for key, value in selection.items():
        if key in ('source_id', 'frequency_id', 'start_date', 'end_date', 'show_revisions'):
            params[snake_to_camel(key)] = value
    return params


def get_data_series(access_token, api_host, **selection):
    """Get data series records for the given selection of entities.  which
  is some or all of: item_id, metric_id, region_id, frequency_id,
  source_id, partner_region_id. Additional arguments are allowed and
  ignored.
  """
    url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params_from_selection(**selection)
    resp = get_data(url, headers, params).json()
    try:
        return resp['data']
    except KeyError as e:
        raise Exception(resp.text)


def rank_series_by_source(access_token, api_host, series_list):
    """Given a list of series, return them in source-ranked order: such
  that if there are multiple sources for the same selection, the
  prefered soruce comes first. Differences other than source_id are
  not affected.
  """
    selections = set(tuple(filter(lambda (k, v): k != 'source_id',
                                  single_series.iteritems()))
                     for single_series in series_list)
    for series in map(dict, selections):
        url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
        headers = {'authorization': 'Bearer ' + access_token}
        params = dict((k + 's', v)
                      for k, v in get_params_from_selection(**series).iteritems())
        source_ids = get_data(url, headers, params).json()
        for source_id in source_ids:
            series['source_id'] = source_id
            yield series


def format_crop_calendar_response(resp):
    """Makes the v2/cropcalendar/data output a similar format to the normal /v2/data output. Splits
  the one point with plantingStartDate/plantingEndDate/harvestingStartDate/harvestingEndDate into
  two distinct points with start/end where the value is the state of the crop as a string.
  """
    points = []
    for point in resp:
        # A single point may have multiple data entries if there are multiple harvests
        for dataEntry in point['data']:
            # Some start/end dates can be undefined (ex: {regionId: 12314, itemId: 95} - Wheat in Alta,
            # Russia). Those are returned as empty strings, so here I am checking for that and replacing
            # those cases with Nones. Also, in some cases both start AND end are undefined, in which
            # case I am excluding the data point entirely.
            if (dataEntry['plantingStartDate'] != '' or dataEntry['plantingEndDate'] != ''):
                points.append({
                    u'input_unit_scale': None,
                    u'region_id': point['regionId'],
                    u'end_date': (dataEntry['plantingEndDate'] if dataEntry['plantingEndDate'] != '' else None),
                    u'input_unit_id': None,
                    u'value': 'planting',
                    u'frequency_id': point['frequencyId'],
                    u'available_date': None,
                    u'item_id': point['itemId'],
                    u'reporting_date': None,
                    u'start_date': (dataEntry['plantingStartDate'] if dataEntry['plantingStartDate'] != '' else None),
                    u'metric_id': point['metricId']
                })
            if (dataEntry['harvestingStartDate'] != '' or dataEntry['harvestingEndDate'] != ''):
                points.append({
                    u'input_unit_scale': None,
                    u'region_id': point['regionId'],
                    u'end_date': (dataEntry['harvestingEndDate'] if dataEntry['harvestingEndDate'] != '' else None),
                    u'input_unit_id': None,
                    u'value': 'harvesting',
                    u'frequency_id': point['frequencyId'],
                    u'available_date': None,
                    u'item_id': point['itemId'],
                    u'reporting_date': None,
                    u'start_date': (
                        dataEntry['harvestingStartDate'] if dataEntry['harvestingStartDate'] != '' else None),
                    u'metric_id': point['metricId']
                })
    return points


def get_crop_calendar_data_points(access_token, api_host, **selection):
    """Helper function for getting crop calendar data. Has different input/output from the regular
  /v2/data call, so this normalizes the interface and output format to make compatible
  get_data_points().
  """
    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/cropcalendar/data'])
    params = get_crop_calendar_params(**selection)
    resp = get_data(url, headers, params).json()
    return format_crop_calendar_response(resp)


def get_data_points(access_token, api_host, **selection):
    """Get all the data points for a given selection, which is some or all
  of: item_id, metric_id, region_id, frequency_id, source_id,
  partner_region_id. Additional arguments are allowed and ignored.
  """
    if (selection['metric_id'] == CROP_CALENDAR_METRIC_ID):
        return get_crop_calendar_data_points(access_token, api_host, **selection)

    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/data'])
    params = get_data_call_params(**selection)
    resp = get_data(url, headers, params).json()

    return resp


def search(access_token, api_host, entity_type, search_terms):
    """Given an entity_type, which is one of 'items', 'metrics',
  'regions', performs a search for the given terms.
  """
    url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, {'q': search_terms}).json()
    return resp


def search_and_lookup(access_token, api_host, entity_type, search_terms):
    """Does a search for the given search terms, and for each result
  yields a dict of the entity and it's properties:
     { 'id': <integer id of entity, unique within this entity type>,
       'name':  <string canonical name>
       'contains': <array of ids of entities that are contained in this one>,
       ....
       <other properties> }
  """
    search_results = search(access_token, api_host, entity_type, search_terms)
    for result in search_results:
        yield lookup(access_token, api_host, entity_type, result['id'])


def lookup_belongs(access_token, api_host, entity_type, entity_id):
    """Given an entity_type, which is one of 'items', 'metrics',
  'regions', and id, generates a list of JSON dicts of entities it
  belongs to.
  """
    url = '/'.join(['https:', '', api_host, 'v2', entity_type, 'belongs-to'])
    params = {'ids': str(entity_id)}
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, params)
    for parent_entity_id in resp.get('data').get(str(entity_id)):
        yield lookup(access_token, api_host, entity_type, parent_entity_id)


# Batch/Async functions equivalent to above.


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

    if len(entities) > 0 and type(entities[0]) != tuple:
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
