import requests
import sys
import time
from datetime import datetime


MAX_RETRIES = 4


def stderr_logger(record):
  sys.stderr.write(str(record))


def get_access_token(api_host, user_email, user_password):
  retry_count = 0
  while retry_count < MAX_RETRIES:
    try:
      login = requests.post('https://' + api_host + '/login',
                            data = {"email": user_email, "password": user_password})
      return login.json()['data']['accessToken']
    except (ValueError, KeyError) as err:
      sys.stderr.write("Failed to get access token: {0}\n".format(err))
    retry_count += 1
  raise ValueError("Can't get access token, giving up after {0} tries.".format(retry_count))


def get_data(url, headers, params=None, logger=None):
  log_record = dict(route=url, params=params)
  retry_count = 0
  if not logger:
    logger = stderr_logger
  while retry_count < MAX_RETRIES:
    start_time = time.time()
    data = requests.get(url, params=params, headers=headers, timeout=None)
    elapsed_time = time.time() - start_time
    log_record['date'] = str(datetime.utcnow().date())
    log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
    log_record['retry_count'] = retry_count
    log_record['status_code'] = data.status_code
    if data.status_code == 200:
      break
    elif retry_count >= (MAX_RETRIES - 1):
      log_record['tag'] = 'failed_gro_api_request'
      log_record['message'] = data.text
    logger(log_record)
    retry_count += 1
  return data


def get_available(access_token, api_host, entity_type):
  """Given an entity_type, which is one of 'items', 'metrics',
    'regions', returns a JSON dict with the list of available entities
    of the given type.
    """
  url = '/'.join(['https:', '', api_host, 'v2/available', entity_type])
  headers = {'authorization': 'Bearer ' + access_token}
  resp = get_data(url, headers)
  return resp.json()


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


def get_data_series(access_token, api_host, item_id, metric_id, region_id):
  """Get data series records for the given selected entities."""
  url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
  headers = {'authorization': 'Bearer ' + access_token}
  params = { }
  if region_id:
    params['regionId'] = region_id
  if item_id:
    params['itemId'] = item_id
  if metric_id:
    params['metricId'] =  metric_id
  resp = get_data(url, headers, params, lambda x: sys.stderr.write(str(x) + "\n"))
  try:
    return resp.json()['data']
  except KeyError as e:
    raise Exception(resp.text)


def get_data_points(access_token, api_host,
                    item_id, metric_id, region_id, frequency_id, source_id):
  url = '/'.join(['https:', '', api_host, 'v2/data'])
  headers = {'authorization': 'Bearer ' + access_token }
  params = {'regionId': region_id, 'itemId': item_id, 'metricId': metric_id,
            'frequencyId': frequency_id, 'sourceId': source_id}
  resp = get_data(url, headers, params, lambda x: sys.stderr.write(str(x) + "\n"))
  try:
    return resp.json()['data']
  except KeyError as e:
    raise Exception(resp.text)


def search(access_token, api_host,
           entity_type, search_terms):
  """Given an entity_type, which is one of 'items', 'metrics',
  'regions', performs a search for the given terms.
  """
  url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
  headers = {'authorization': 'Bearer ' + access_token }
  resp = get_data(url, headers, {'q': search_terms},
                  lambda x: sys.stderr.write(str(x) + "\n"))
  return resp.json()
