import argparse
import sys
from random import random
from api.client.lib import get_data, get_access_token

API_HOST = 'apidev11201.gro-intelligence.com'


def get_available(access_token, entity_type):
    """Given an entity_type, which is one of 'items', 'metrics',
    'regions', returns a JSON dict with the list of available entities
    of the given type.
    """
    url = '/'.join(['https:', '', API_HOST, 'v2/available', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()


def list_available(access_token, params):
    url = '/'.join(['https:', '', API_HOST, 'v2/entities/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, params)
    return resp.json()['data']


def get_data_series(access_token, item_id, metric_id, region_id):
    url = '/'.join(['https:', '', API_HOST, 'v2/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = { 'regionId': region_id, 'itemId': item_id, 'metricId': metric_id}
    resp = get_data(url, headers, params, lambda x: sys.stderr.write(str(x)))
    return resp.json()['data']


def get_data_points(access_token, item_id, metric_id, region_id, frequency, source_id):
    url = '/'.join(['https:', '', API_HOST, 'v2/data'])
    headers = {'authorization': 'Bearer ' + access_token }
    params = {'regionId': region_id, 'itemId': item_id, 'metricId': metric_id,
              'frequencyId': frequency, 'sourceId': source_id}
    resp = get_data(url, headers, params, lambda x: sys.stderr.write(str(x)))
    return resp.json()['data']


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    args = parser.parse_args()

    access_token = get_access_token(API_HOST, args.user_email, args.user_password)

    # Find some random item that has data series
    selected_entities = {}
    for item in  get_available(access_token, 'items'):
        if random() > 0.5:
            print "Randomly selected item: {}".format(item['name'])
            selected_entities['itemId'] = item['id']
            break

    # Find all metrics that have some data series
    for entities in list_available(access_token, selected_entities):
        if random() > 0.1:
            print "Using entities: {}".format(str(entities))
            selected_entities.update(entities)
            break

    # Random data series examples
    for data_series in get_data_series(access_token,
                                       selected_entities['item_id'],
                                       selected_entities['metric_id'],
                                       selected_entities['region_id']):
        print "Using data series: {}".format(data_series['series_id'])
        print get_data_points(access_token,
                              data_series['item_id'],
                              data_series['metric_id'],
                              data_series['region_id'],
                              data_series['frequency_id'],
                              data_series['source_id'])
        break
