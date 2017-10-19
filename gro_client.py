import argparse
import sys
from random import random
from api.client.lib import get_access_token, get_available, list_available, get_data_series, get_data_points

API_HOST = 'apidev11201.gro-intelligence.com'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    args = parser.parse_args()

    access_token = get_access_token(API_HOST, args.user_email, args.user_password)

    # Pick a random item that has some data associated with it.
    selected_entities = {}
    item_list = get_available(access_token, API_HOST, 'items')
    item = item_list[int(len(item_list)*random())]
    print "Randomly selected item: {}".format(item['name'])
    selected_entities['itemId'] = item['id']

    # Pick a random metric and region for this item with data available
    entity_list = list_available(access_token, API_HOST, selected_entities)
    entities = entity_list[int(len(entity_list)*random())]
    print "Using entities: {}".format(str(entities))
    selected_entities.update(entities)

    # Random data series examples
    for data_series in get_data_series(access_token, API_HOST,
                                       selected_entities['item_id'],
                                       selected_entities['metric_id'],
                                       selected_entities['region_id']):
        print "Using data series: {}".format(data_series['series_id'])
        for point in get_data_points(access_token, API_HOST,
                              data_series['item_id'],
                              data_series['metric_id'],
                              data_series['region_id'],
                              data_series['frequency_id'],
                              data_series['source_id']):
            print ','.join(map(lambda x: str(x),
                               [point['start_date'], point['end_date'], point['value']]))
        break
