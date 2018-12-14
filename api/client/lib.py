import functools
import logging
import time

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import IOLoop
from tornado.escape import json_decode

# So we can have both
from tornado.queues import Queue

try:
    # Python3
    from urllib.parse import urlencode
except ImportError:
    # Python2
    from urllib import urlencode

MAX_RETRIES = 4
DEFAULT_LOG_LEVEL=logging.INFO  # change to DEBUG for more detail
MAX_QUERIES_PER_SECOND = 10
CROP_CALENDAR_METRIC_ID = 2260063
http_client = AsyncHTTPClient()

########################################################################################################################
# internal and helper functions
########################################################################################################################

def get_default_logger(name=__name__):
  logger = logging.getLogger(name)
  logger.setLevel(DEFAULT_LOG_LEVEL)
  if not logger.handlers:
    stderr_handler = logging.StreamHandler()
    logger.addHandler(stderr_handler)
  return logger


def get_access_token(api_host, user_email, user_password, logger=None):
  retry_count = 0
  if not logger:
    logger = get_default_logger()
  while retry_count < MAX_RETRIES:
    body = "email=%s&password=%s" % (user_email, user_password)
    login_request = HTTPRequest('https://' + api_host + '/login',
                                method="POST",
                                body=body)
    login = IOLoop.current().run_sync(functools.partial(http_client.fetch, login_request))
    if login.code == 200:
      logger.debug("Authentication succeeded in get_access_token")
      return json_decode(login.body)['data']['accessToken']
    else:
      logger.warning("Error in get_access_token: {}".format(login))
    retry_count += 1
  raise Exception("Giving up on get_access_token after {0} tries.".format(retry_count))


def snake_to_camel(term):
  """Converts hello_world to helloWorld."""
  camel = term.split('_')
  return ''.join(camel[:1]+ map(lambda x: x[0].upper()+x[1:], camel[1:]))


def get_params_from_selection(**selection):
  """Construct http request params from dict of entity selections. For use with get_data_series()
  and rank_series_by_source().
  """
  params = { }
  for key, value in selection.items():
    if key in ('region_id', 'partner_region_id', 'item_id', 'metric_id', 'frequency_id', 'source_id'):
      params[snake_to_camel(key)] = value
  return params

def get_data_call_params(**selection):
  """Construct http request params from dict of entity selections. For use with get_data_points().
  """
  params = get_params_from_selection(**selection)
  for key, value in selection.items():
    if key in ('start_date', 'end_date', 'show_revisions'):
      params[snake_to_camel(key)] = value
  return params

def get_crop_calendar_params(**selection):
  """Construct http request params from dict of entity selections. Only region and item are required
  since metric/item/source/frequency all have default values and start/end date are not allowed
  inputs since crop calendars are static.
  """
  params = { }
  for key, value in selection.items():
    if key in ('region_id', 'item_id'):
      params[snake_to_camel(key)] = value
  return params

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
      if(dataEntry['plantingStartDate'] != '' or dataEntry['plantingEndDate'] != ''):
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
      if(dataEntry['harvestingStartDate'] != '' or dataEntry['harvestingEndDate'] != ''):
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
          u'start_date': (dataEntry['harvestingStartDate'] if dataEntry['harvestingStartDate'] != '' else None),
          u'metric_id': point['metricId']
        })
  return points

########################################################################################################################
# synchronous and batch asynchronous decorators.
########################################################################################################################

def synchronous(func):

    def sync_wrapper(*args, **kwargs):
        return IOLoop.current().run_sync(functools.partial(func, *args, **kwargs))

    return sync_wrapper

def queued_batch_async(func):

    logger = get_default_logger("batch_async")

    def batch_async_wrapper(access_token, api_host, list_of_list_of_args, output_list=None, map_result=None):
        """
        Asynchronous version of get_data operating on multiple queries simultaneously.
        :param access_token:
        :param api_host:
        :param list_of_list_of_args:
        :param output_list:
        :param map_result:
        :return:
        """

        assert type(list_of_list_of_args) is list, \
            "Only argument to a batch async decorated function should be a list of a list of the individual " \
            "non-keyword arguments being passed to the original function." \

        if output_list is None:
            output_list = [0] * len(list_of_list_of_args)

        # Default is identity mapping into results list.
        if not map_result:
            def map_result(idx, query, response):
                output_list[idx] = response

        # Queue holds at most 1 second of queries as to not overload the server if it's "stuck"
        q = Queue(maxsize=MAX_QUERIES_PER_SECOND)

        @gen.coroutine
        def consumer():
            while True:
                idx, item = yield q.get()
                try:
                    logger.debug('Doing work on %s', idx)
                    result = yield func(access_token, api_host, item)
                    map_result(idx, item, result)
                except Exception as e:
                    # if it fails this many times... let it go.
                    print(e)
                    yield map_result(idx, item, None)
                finally:
                    q.task_done()

        @gen.coroutine
        def producer():
            """ Uses the interleaving pattern from https://www.tornadoweb.org/en/stable/guide/coroutines.html
            to place items in the queue at a fixed rate.
            """
            for idx, item in enumerate(list_of_list_of_args):
                timer = gen.sleep(1.0 / float(MAX_QUERIES_PER_SECOND))  # Start the clock.
                yield q.put((idx, item))
                logger.debug('Put ', idx)
                logger.debug("length of queue", q.qsize())
                yield timer
                logger.debug('Ready to put next')

        @gen.coroutine
        def main():
            # Start consumer without waiting (since it never finishes).
            for i in range(MAX_QUERIES_PER_SECOND):
                IOLoop.current().spawn_callback(consumer)
            yield producer()  # Wait for producer to put all tasks.
            yield q.join()  # Wait for consumer to finish all tasks.

        IOLoop.current().run_sync(main)

        return output_list

    return batch_async_wrapper

@gen.coroutine
def _get_data(url, headers, params=None, logger=None):
  """General 'make api request' function. Assigns headers and builds in retries and logging."""
  base_log_record = dict(route=url, params=params)
  retry_count = 0
  if not logger:
    logger = get_default_logger()
  logger.debug(url)
  while retry_count < MAX_RETRIES:
    start_time = time.time()
    if params is not None:
        params_encode = urlencode(params)
        url = '{url}?{params}'.format(url=url, params=params_encode)
    http_request = HTTPRequest(url, method="GET", headers=headers, request_timeout=None)
    data = yield http_client.fetch(http_request)
    elapsed_time = time.time() - start_time
    log_record = dict(base_log_record)
    log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
    log_record['retry_count'] = retry_count
    log_record['status_code'] = data.code
    if data.code == 200:
      logger.debug('OK', extra=log_record)
      raise gen.Return(data.body)
    retry_count += 1
    log_record['tag'] = 'failed_gro_api_request'
    if retry_count < MAX_RETRIES:
      logger.warning(data.text, extra=log_record)
    else:
      logger.error(data.text, extra=log_record)
  raise Exception('Giving up on {} after {} tries. Error is: {}.'.format(url, retry_count, data.text))

@synchronous
def get_data(url, headers, params=None, logger=None):
    return _get_data(url, headers, params=None, logger=None)

@gen.coroutine
def _get_crop_calendar_data_points(access_token, api_host, **selection):
  """Helper function for getting crop calendar data. Has different input/output from the regular
  /v2/data call, so this normalizes the interface and output format to make compatible
  get_data_points().
  """
  headers = {'authorization': 'Bearer ' + access_token }
  url = '/'.join(['https:', '', api_host, 'v2/cropcalendar/data'])
  params = get_crop_calendar_params(**selection)
  resp = yield _get_data(url, headers, params)
  raise gen.Return(format_crop_calendar_response(json_decode(resp)))

##########################################################################################################
# functions without a batch mode
#########################################################################################################

def rank_series_by_source(access_token, api_host, series_list):
  """Given a list of series, return them in source-ranked order: such
  that if there are multiple sources for the same selection, the
  prefered soruce comes first. Differences other than source_id are
  not affected.
  """

  # We sort the internal tuple representations of the dictionaries because otherwise when we call set()
  # we end up with duplicates if iteritems() returns a different order for the same dictionary. See
  # test case...
  selections_sorted = set(
                          tuple(
                              sorted(
                                filter(lambda (k, v): k != 'source_id', single_series.iteritems()),
                                key=lambda x: x[0]
                              )
                          ) for single_series in series_list
                        )

  for series in map(dict, selections_sorted):
    url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = dict((k + 's', v)
                  for k, v in get_params_from_selection(**series).iteritems())
    source_ids = json_decode(get_data(url, headers, params))
    for source_id in source_ids:
      # Make a copy to avoid passing the same reference each time.
      series_with_source = dict(series)
      series_with_source['source_id'] = source_id
      yield series_with_source

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
  params = { 'ids': str(entity_id) }
  headers = {'authorization': 'Bearer ' + access_token}
  resp = get_data(url, headers, params)
  for parent_entity_id in json_decode(resp).get('data').get(str(entity_id)):
    yield lookup(access_token, api_host, entity_type, parent_entity_id)


##########################################################################################################
# functions with a normal mode and a batch mode
#########################################################################################################

@gen.coroutine
def _get_available(access_token, api_host, entity_type):
  """Given an entity_type, which is one of 'items', 'metrics',
    'regions', returns a JSON dict with the list of available entities
    of the given type.
    """
  url = '/'.join(['https:', '', api_host, 'v2', entity_type])
  headers = {'authorization': 'Bearer ' + access_token}
  resp = yield _get_data(url, headers)
  raise gen.Return(json_decode(resp)['data'])

@synchronous
def get_available(access_token, api_host, entity_type):
    return _get_available(access_token, api_host, entity_type)

@queued_batch_async
def batch_async_get_available(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _get_available(access_token, api_host, *list_of_args)

@gen.coroutine
def _list_available(access_token, api_host, selected_entities):
  """List available entities given some selected entities. Given a dict
  of selected entity ids of the form { <entity_type>: <entity_id>,
  ...}, returns a list of dictionaries representing available {
  item_id: ..., metric_id: ... , region_id: ... ,} for which data
  series are available which satisfy the input selection.
  """
  url = '/'.join(['https:', '', api_host, 'v2/entities/list'])
  headers = {'authorization': 'Bearer ' + access_token}
  params = dict(map(lambda (key, value): (snake_to_camel(key), value),
                    selected_entities.items()))
  resp = yield _get_data(url, headers, params)
  try:
    raise gen.Return(json_decode(resp)['data'])
  except KeyError as e:
    raise Exception(resp.text)

@synchronous
def list_available(access_token, api_host, selected_entities):
    return _list_available(access_token, api_host, selected_entities)

@queued_batch_async
def batch_async_list_available(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _list_available(access_token, api_host, *list_of_args)

@gen.coroutine
def _get_data_series(access_token, api_host, **selection):
  """Get data series records for the given selection of entities.  which
  is some or all of: item_id, metric_id, region_id, frequency_id,
  source_id, partner_region_id. Additional arguments are allowed and
  ignored.
  """
  url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
  headers = {'authorization': 'Bearer ' + access_token}
  params = get_params_from_selection(**selection)
  resp = yield _get_data(url, headers, params)
  try:
    raise gen.Return(json_decode(resp)['data'])
  except KeyError as e:
    raise Exception(resp.text)

@synchronous
def get_data_series(access_token, api_host, **selection):
    return _get_data_series(access_token, api_host, **selection)

@queued_batch_async
def batch_async_get_data_series(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _get_data_series(access_token, api_host, *list_of_args)

@gen.coroutine
def _get_data_points(access_token, api_host, **selection):
  """Get all the data points for a given selection, which is some or all
  of: item_id, metric_id, region_id, frequency_id, source_id,
  partner_region_id. Additional arguments are allowed and ignored.
  """
  if selection['metric_id'] == CROP_CALENDAR_METRIC_ID:
    crop_calendar_values = yield _get_crop_calendar_data_points(access_token, api_host, **selection)
    raise gen.Return(crop_calendar_values)

  headers = {'authorization': 'Bearer ' + access_token }
  url = '/'.join(['https:', '', api_host, 'v2/data'])
  params = get_data_call_params(**selection)
  resp = yield _get_data(url, headers, params)
  raise gen.Return(json_decode(resp))

@synchronous
def get_data_points(access_token, api_host, **selection):
    return _get_data_points(access_token, api_host, **selection)

@queued_batch_async
def batch_async_get_data_points(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _get_data_points(access_token, api_host, **list_of_args)

@gen.coroutine
def _lookup(access_token, api_host, entity_type, entity_id):
  """Given an entity_type, which is one of 'items', 'metrics',
  'regions', 'units', or 'sources', returns a JSON dict with the
  list of available entities of the given type.
  """
  url = '/'.join(['https:', '', api_host, 'v2', entity_type, str(entity_id)])
  headers = {'authorization': 'Bearer ' + access_token}
  resp = yield _get_data(url, headers)
  try:
    raise gen.Return(json_decode(resp)['data'])
  except KeyError as e:
    raise Exception(resp.text)

@synchronous
def lookup(access_token, api_host, entity_type, entity_id):
    return _lookup(access_token, api_host, entity_type, entity_id)

@queued_batch_async
def batch_async_lookup(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _lookup(access_token, api_host, *list_of_args)

@gen.coroutine
def _universal_search(access_token, api_host, search_terms):
  """Search across all entity types for the given terms.  Returns an a
  list of [id, entity_type] pairs, e.g.: [[5604, u'item'], [10204,
  u'item'], [410032, u'metric'], ....]
  """
  url_pieces = ['https:', '', api_host, 'v2/search']
  url = '/'.join(url_pieces)
  headers = {'authorization': 'Bearer ' + access_token }
  resp = yield _get_data(url, headers, {'q': search_terms})
  raise gen.Return(json_decode(resp))

@synchronous
def universal_search(access_token, api_host, search_terms):
    return _universal_search(access_token, api_host, search_terms)

@queued_batch_async
def batch_async_universal_search(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _universal_search(access_token, api_host, *list_of_args)

@gen.coroutine
def _search(access_token, api_host, entity_type, search_terms):
  """Given an entity_type, which is one of 'items', 'metrics',
  'regions', performs a search for the given terms. Returns a list of
  dictionaries with individual entities, e.g.: [{u'id': 5604}, {u'id':
  10204}, {u'id': 10210}, ....]
  """
  url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
  headers = {'authorization': 'Bearer ' + access_token }
  resp = yield _get_data(url, headers, {'q': search_terms})
  raise gen.Return(json_decode(resp))

@synchronous
def search(access_token, api_host, entity_type, search_terms):
    return _search(access_token, api_host, entity_type, search_terms)

@queued_batch_async
def batch_async_search(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return  _search(access_token, api_host, *list_of_args)

@gen.coroutine
def _get_geo_centre(access_token, api_host, region_id):
  """Given a region ID, returns the geographic centre in degrees lat/lon."""
  url = '/'.join(['https:', '', api_host, 'v2/geocentres?regionIds=' + str(region_id)])
  headers = {'authorization': 'Bearer ' + access_token}
  resp = yield _get_data(url, headers)
  raise gen.Return(json_decode(resp)["data"])

@synchronous
def get_geo_centre(access_token, api_host, region_id):
    return _get_geo_centre(access_token, api_host, region_id)

@queued_batch_async
def batch_async_get_geo_centre(access_token, api_host, list_of_args, output_list=None, map_result=None):
    return _get_geo_centre(access_token, api_host, *list_of_args)
