import logging
import requests
import sys
import time
from datetime import datetime


MAX_RETRIES = 4
DEFAULT_LOG_LEVEL=logging.WARNING  # change to DEBUG for more detail


def get_default_logger():
  logging.basicConfig(level=DEFAULT_LOG_LEVEL)
  logger = logging.getLogger(__name__)
  if not logger.handlers:
    stderr_handler = logging.StreamHandler()
    logger.addHandler(stderr_handler)
  return logger


def get_access_token(api_host, user_email, user_password, logger=None):
  retry_count = 0
  if not logger:
    logger = get_default_logger()
  while retry_count < MAX_RETRIES:
    login = requests.post('https://' + api_host + '/login',
                          data = {"email": user_email, "password": user_password})
    if login.status_code == 200:
      logger.debug("Authentication succeeded in get_access_token")
      return login.json()['data']['accessToken']
    else:
      logger.warning("Error in get_access_token: {}".format(login))
    retry_count += 1
  raise Exception("Giving up on get_access_token after {0} tries.".format(retry_count))


def get_data(url, headers, params=None, logger=None):
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
      logger.info('OK', extra=log_record)
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
  resp = get_data(url, headers, selected_entities)
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
  camel = ''.join(term.title().split('_'))
  return camel[0].lower() + camel[1:]


def get_params_from_selection(**selection):
  """Construct http request params from dict of entity selections."""
  params = { }
  for key, value in selection.items():
    if key in ('region_id', 'partner_region_id', 'item_id',
               'metric_id', 'source_id', 'frequency_id'):
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


def get_data_points(access_token, api_host, **selection):
  """Get all the data points for a given selection, which is some or all
  of: item_id, metric_id, region_id, frequency_id, source_id,
  partner_region_id. Additional arguments are allowed and ignored.
  """
  url = '/'.join(['https:', '', api_host, 'v2/data'])
  headers = {'authorization': 'Bearer ' + access_token }
  params = get_params_from_selection(**selection)
  resp = get_data(url, headers, params)
  return resp.json()


def search(access_token, api_host,
           entity_type, search_terms):
  """Given an entity_type, which is one of 'items', 'metrics',
  'regions', performs a search for the given terms.
  """
  url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
  headers = {'authorization': 'Bearer ' + access_token }
  resp = get_data(url, headers, {'q': search_terms})
  return resp.json()


def search_and_lookup(access_token, api_host,
                      entity_type, search_terms):
  """Does a search for the given search terms, and for each result
  yields a dict of the entity and it's properties:
     { 'id': <integer id of entity, unique within this entity type>,
       'name':  <string canonical name>
       'contains': <array of ids of entities that are contained in this one>,
       ....
       <other properties> }
  """
  search_results = search(access_token, api_host, entity_type, search_terms)
  for result in search_results[entity_type]:
    yield lookup(access_token, api_host, entity_type, result['id'])


def lookup_belongs(access_token, api_host, entity_type, entity_id):
  """Given an entity_type, which is one of 'items', 'metrics',
    'regions', returns a JSON dict with the list of available entities
    of the given type.
  """
  url = '/'.join(['https:', '', api_host, 'v2', entity_type, 'belongs-to'])
  params = { 'ids': str(entity_id) }
  headers = {'authorization': 'Bearer ' + access_token}
  resp = get_data(url, headers, params)
  for parent_entity_id in resp.json()['data']:
    yield lookup(access_token, api_host, entity_type, parent_entity_id)
