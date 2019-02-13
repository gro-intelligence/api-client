from builtins import map
from builtins import str
import logging
import requests
import sys
import time
from datetime import datetime


MAX_RETRIES = 4
DEFAULT_LOG_LEVEL=logging.INFO  # change to DEBUG for more detail

CROP_CALENDAR_METRIC_ID = 2260063


def get_default_logger():
  logger = logging.getLogger(__name__)
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
    get_api_token = requests.post('https://' + api_host + '/api-token',
                          data = {"email": user_email, "password": user_password})
    if get_api_token.status_code == 200:
      logger.debug("Authentication succeeded in get_access_token")
      return get_api_token.json()['data']['accessToken']
    else:
      logger.warning("Error in get_access_token: {}".format(get_api_token.body))
    retry_count += 1
  raise Exception("Giving up on get_access_token after {0} tries.".format(retry_count))


def get_data(url, headers, params=None, logger=None):
  """General 'make api request' function. Assigns headers and builds in retries and logging."""
  base_log_record = dict(route=url, params=params)
  retry_count = 0
  if not logger:
    logger = get_default_logger()
  logger.debug(url)
  logger.debug(params)
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
  resp = get_data(url, headers)
  return resp.json()['data']


def list_available(access_token, api_host, selected_entities):
  """List available entities given some selected entities. Given a dict
  of selected entity ids of the form { <entity_type>: <entity_id>,
  ...}, returns a list of dictionaries representing available {
  item_id: ..., metric_id: ... , region_id: ... ,} for which data
  series are available which satisfy the input selection.
  """
  url = '/'.join(['https:', '', api_host, 'v2/entities/list'])
  headers = {'authorization': 'Bearer ' + access_token}
  params = dict([(snake_to_camel(key), value)
                 for (key, value) in list(selected_entities.items())])
  resp = get_data(url, headers, params)
  try:
    return resp.json()['data']
  except KeyError as e:
    raise Exception(resp.text)


def lookup(access_token, api_host, entity_type, entity_id):
  """Given an entity_type, which is one of 'items', 'metrics',
  'regions', 'units', or 'sources', returns a JSON dict with the
  list of available entities of the given type.
  """
  url = '/'.join(['https:', '', api_host, 'v2', entity_type, str(entity_id)])
  headers = {'authorization': 'Bearer ' + access_token}
  resp = get_data(url, headers)
  try:
    return resp.json()['data']
  except KeyError as e:
    raise Exception(resp.text)


def snake_to_camel(term):
  """Converts hello_world to helloWorld."""
  camel = term.split('_')
  return ''.join(camel[:1] + list([x[0].upper()+x[1:] for x in camel[1:]]))


def get_params_from_selection(**selection):
  """Construct http request params from dict of entity selections. For use with get_data_series()
  and rank_series_by_source().
  """
  params = { }
  for key, value in list(selection.items()):
    if key in ('region_id', 'partner_region_id', 'item_id', 'metric_id', 'source_id', 'frequency_id'):
      params[snake_to_camel(key)] = value
  return params


def get_crop_calendar_params(**selection):
  """Construct http request params from dict of entity selections. Only region and item are required
  since metric/item/source/frequency all have default values and start/end date are not allowed
  inputs since crop calendars are static.
  """
  params = { }
  for key, value in list(selection.items()):
    if key in ('region_id', 'item_id'):
      params[snake_to_camel(key)] = value
  return params


def get_data_call_params(**selection):
  """Construct http request params from dict of entity selections. For use with get_data_points().
  """
  params = get_params_from_selection(**selection)
  for key, value in list(selection.items()):
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
  resp = get_data(url, headers, params)
  try:
    return resp.json()['data']
  except KeyError as e:
    raise Exception(resp.text)


def rank_series_by_source(access_token, api_host, series_list):
  """Given a list of series, return them in source-ranked order: such
  that if there are multiple sources for the same selection, the
  prefered soruce comes first. Differences other than source_id are
  not affected.
  """
  # We sort the internal tuple representations of the dictionaries because otherwise when we call set()
  # we end up with duplicates if iteritems() returns a different order for the same dictionary. See
  # test case...
  selections_sorted = set(tuple(sorted(
    [k_v for k_v in iter(list(single_series.items())) if k_v[0] != 'source_id'],
    key=lambda x: x[0])) for single_series in series_list)

  for series in map(dict, selections_sorted):
    url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = dict((k + 's', v) for k, v in iter(list(
      get_params_from_selection(**series).items())))
    source_ids = get_data(url, headers, params).json()
    for source_id in source_ids:
      # Make a copy to avoid passing the same reference each time.
      series_with_source = dict(series)
      series_with_source['source_id'] = source_id
      yield series_with_source


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

def get_crop_calendar_data_points(access_token, api_host, **selection):
  """Helper function for getting crop calendar data. Has different input/output from the regular
  /v2/data call, so this normalizes the interface and output format to make compatible
  get_data_points().
  """
  headers = {'authorization': 'Bearer ' + access_token }
  url = '/'.join(['https:', '', api_host, 'v2/cropcalendar/data'])
  params = get_crop_calendar_params(**selection)
  resp = get_data(url, headers, params)
  return format_crop_calendar_response(resp.json())


def get_data_points(access_token, api_host, **selection):
  """Get all the data points for a given selection, which is some or all
  of: item_id, metric_id, region_id, frequency_id, source_id,
  partner_region_id. Additional arguments are allowed and ignored.
  """
  if(selection['metric_id'] == CROP_CALENDAR_METRIC_ID):
    return get_crop_calendar_data_points(access_token, api_host, **selection)

  headers = {'authorization': 'Bearer ' + access_token }
  url = '/'.join(['https:', '', api_host, 'v2/data'])
  params = get_data_call_params(**selection)
  resp = get_data(url, headers, params)
  return resp.json()


def universal_search(access_token, api_host, search_terms):
  """Search across all entity types for the given terms.  Returns an a
  list of [id, entity_type] pairs, e.g.: [[5604, u'item'], [10204,
  u'item'], [410032, u'metric'], ....]
  """
  url_pieces = ['https:', '', api_host, 'v2/search']
  url = '/'.join(url_pieces)
  headers = {'authorization': 'Bearer ' + access_token }
  resp = get_data(url, headers, {'q': search_terms})
  return resp.json()


def search(access_token, api_host, entity_type, search_terms):
  """Given an entity_type, which is one of 'items', 'metrics',
  'regions', performs a search for the given terms. Returns a list of
  dictionaries with individual entities, e.g.: [{u'id': 5604}, {u'id':
  10204}, {u'id': 10210}, ....]
  """
  url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
  headers = {'authorization': 'Bearer ' + access_token }
  resp = get_data(url, headers, {'q': search_terms})
  return resp.json()


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
  for parent_entity_id in resp.json().get('data').get(str(entity_id), []):
    yield lookup(access_token, api_host, entity_type, parent_entity_id)


def get_geo_centre(access_token, api_host, region_id):
  """Given a region ID, returns the geographic centre in degrees lat/lon."""
  url = '/'.join(['https:', '', api_host, 'v2/geocentres?regionIds=' + str(region_id)])
  headers = {'authorization': 'Bearer ' + access_token}
  resp = get_data(url, headers)
  return resp.json()["data"]


def get_descendant_regions(access_token, api_host, region_id, descendant_level):
  """Given any region by id, recursively gets all the descendant regions
  that are of the specified level. 

  This takes advantage of the assumption that region graph is
  acyclic. This will only traverse ordered region levels (strictly
  increasing region level id) and thus skips non-administrative region
  levels.
  """
  descendants = []
  region = lookup(access_token, api_host, 'regions', region_id)
  for member_id in region['contains']:
    member = lookup(access_token, api_host, 'regions', member_id)
    if descendant_level == member['level']:
      descendants.append(member)
    elif member['level'] < descendant_level:
      descendants += get_descendant_regions(
        access_token, api_host, member_id, descendant_level)
  return descendants
