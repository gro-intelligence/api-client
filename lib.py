import requests
import sys
import time
from datetime import datetime


MAX_RETRIES = 4


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
    while retry_count < MAX_RETRIES:
        start_time = time.time()
        data = requests.get(url, params=params, headers=headers, timeout=None)
        elapsed_time = time.time() - start_time
        log_record['date'] = str(datetime.utcnow().date())
        log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
        log_record['retry_count'] = retry_count
        log_record['status_code'] = data.status_code
        if data.status_code == 200: # Checks and retries on the same url if time out occurs
            break
        elif data.status_code != 200 and retry_count == (MAX_RETRIES - 1):
            log_record['tag'] = 'failed_gro_api_request'
            log_record['message'] = data.json()['message']
        if logger:
            logger(log_record)
        retry_count = retry_count + 1
    return data
