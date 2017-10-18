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
    assert resp.status_code == 200, 'Request failed: {}'.format(resp)
    return resp.json()


def get_data_series(access_token, item_id, metric_id, region_id, frequency, source_id):
    url = '/'.join(['https:', '', API_HOST, 'v2', 'data'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = { 'regionId': region_id, 'itemId': item_id, 'metricId': metric_id,
               'frequency': frequency, 'sourceId': source_id}
    resp = get_data(url, headers, params, lambda x: sys.stderr.write(str(x)))
    assert resp.status_code == 200, 'Request failed: {}'.format(resp)
    return resp.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    args = parser.parse_args()

    access_token = get_access_token(API_HOST, args.user_email, args.user_password)
    
    # Find all items that have some data series
    print get_available(access_token, 'items')
    # Find all metrics that have some data series
    print get_available(access_token, 'metrics')


    # Random data series examples
    print get_data_series(access_token, 63, 860032, 1001, 'annual', 2)


