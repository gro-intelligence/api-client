import argparse
import sys
from api.client.lib import get_data, get_access_token

API_HOST = 'clewsapi.gro-intelligence.com'


def get_available(access_token, entity_type):
    """Given an entity_type, which is one of 'items', 'metrics',
    'regions', returns a JSON dict with the list of available entities
    of the given type.
    """
    url = '/'.join(['https:', '', API_HOST, 'v2', 'available', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    if resp.status_code != 200:
        raise Exception('Request failed: {}'.format(resp.json()))
    return resp.json()


def main(access_token):
    url = '/'.join(['https:', '', API_HOST, 'v2', 'data'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = { 'regionId': 1001, 'itemId': 63, 'metricId': 860032,
               'frequency': 'annual', 'sourceId': 2}
    resp = get_data(url, headers, params, lambda x: sys.stderr.write(str(x)))
    if resp.status_code != 200:
        raise Exception('Request failed: {}'.format(resp.json()))
    print resp.json()
    print get_available(access_token, 'items')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    args = parser.parse_args()

    access_token = get_access_token(API_HOST, args.user_email, args.user_password)
    main(access_token)

