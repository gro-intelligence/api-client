# Basic gro api client.
#
# Usage example:
#
#   export PYTHONPATH=~/src/gro
#   python ~/src/gro/api/client/gro_client.py --user_email=nemo@gro-intelligence.com --user_password=<s3krit> --item=sesame --region=ethiopia
#   python ~/src/gro/api/client/gro_client.py --user_email=nemo@gro-intelligence.com --user_password=<s3krit>
#   python ~/src/gro/api/client/gro_client.py --user_email=nemo@gro-intelligence.com --user_password=<s3krit> --metric=export

import argparse
import sys
from random import random
from api.client.lib import get_access_token, get_available, list_available, get_data_series, get_data_points, search


API_HOST = 'apidev11201.gro-intelligence.com'


def print_random_data_series(access_token, selected_entities):
    """Example which prints out a CSV of a random data series that
    satisfies the (optional) given selection.
    """
    # Pick a random data series for this selection
    data_series_list = get_data_series(access_token, API_HOST,
                                       selected_entities.get('item_id'),
                                       selected_entities.get('metric_id'),
                                       selected_entities.get('region_id'))
    data_series = data_series_list[int(len(data_series_list)*random())]
    print "Using data series: {}".format(str(data_series))
    for point in get_data_points(access_token, API_HOST,
                                 data_series['item_id'],
                                 data_series['metric_id'],
                                 data_series['region_id'],
                                 data_series['frequency_id'],
                                 data_series['source_id']):
        # Print out a CSV of time series: time period, value (there
        # are plenty of other columns like units)
        print ','.join(map(lambda x: str(x),
                           [point['start_date'], point['end_date'], point['value']]))


def search_for_entity(access_token, entity_type, keywords):
    """Returns the first result of entity_type (which is items, metrics or
    regions) that matches the given keywords.
    """
    results = search(access_token, API_HOST, entity_type, keywords)
    num_results = len(results[entity_type])
    for result in results[entity_type]:
        print "Picking first result out of {} {}: {}, {}".format(
            num_results, entity_type, result['id'], result['name'])
        return result['id']
    return None


def pick_random_entities(access_token):
    """Pick a random item that has some data associated with it, and a
    random metric and region pair for that item with data
    available.
    """
    item_list = get_available(access_token, API_HOST, 'items')
    item = item_list[int(len(item_list)*random())]
    print "Randomly selected item: {}".format(item['name'])
    selected_entities['item_id'] = item['id']


    entity_list = list_available(access_token, API_HOST, selected_entities)
    entities = entity_list[int(len(entity_list)*random())]
    print "Using entities: {}".format(str(entities))
    selected_entities.update(entities)
    return selected_entities


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--item")
    parser.add_argument("--metric")
    parser.add_argument("--region")
    parser.add_argument("--print_token", action='store_true')
    parser.add_argument("--token")
    args = parser.parse_args()

    access_token = None
    if args.token:
        access_token = args.token
    else:
        access_token = get_access_token(API_HOST, args.user_email, args.user_password)

    if args.print_token:
        print access_token
        sys.exit(0)

    selected_entities = {}
    if args.item:
        selected_entities['item_id'] = search_for_entity(access_token,
                                                         'items', args.item)
    if args.metric:
        selected_entities['metric_id'] = search_for_entity(access_token,
                                                           'metrics', args.metric)
    if args.region:
        selected_entities['region_id'] = search_for_entity(access_token,
                                                           'regions', args.region)
    if not selected_entities:
        selected_entities = pick_random_entities(access_token)
    print_random_data_series(access_token, selected_entities)
