# Basic gro api client.
#
# Usage example:
#
#   export PYTHONPATH=./gro
#   python gro/api/client/gro_client.py --item soybeans  --region brazil --partner_region china --metric export --user_email ... --user_password ...
#   python gro/api/client/gro_client.py --item=sesame --region=ethiopia --user_email=... --user_password=...

import argparse
import sys
import unicodecsv
from random import random
import pandas
import api.client.lib


OUTPUT_FILENAME = 'gro_client_output.csv'


def get_df(client, **selected_entities):
    """Get the content of data series in a pandas frame.
    selected_entities should be some or all of: item_id, metric_id,
    region_id, frequency_id, source_id, partner_region_id
    """
    return pandas.DataFrame(client.get_data_points(**selected_entities))


def print_one_data_series(client, data_series):
    print "Using data series: {}".format(str(data_series))
    print "Outputing to file: {}".format(OUTPUT_FILENAME)
    writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))
    for point in client.get_data_points(**data_series):
        writer.writerow([point['start_date'], point['end_date'],
                         point['value'] * point['input_unit_scale'],
                         client.lookup_unit_abbreviation(point['input_unit_id'])])


def print_random_data_series(client, data_series_list):
    """Example which prints out a CSV of a random data series that
    satisfies the (optional) given selection.
    """
    print_one_data_series(
        client, data_series_list[int(len(data_series_list)*random())])


def pick_source_and_print_data_series(client, data_series_list):
    for data_series in client.rank_series_by_source(data_series_list):
        print_one_data_series(client, data_series)
        break


def search_for_entity(client, entity_type, keywords):
    """Returns the first result of entity_type (which is items, metrics or
    regions) that matches the given keywords.
    """
    results = client.search(entity_type, keywords)
    for result in results[entity_type]:
        print u"Picking first result out of {} {}: {}, {}".format(
            len(results[entity_type]), entity_type, result['id'], result['name'])
        return result['id']
    return None


def pick_random_entities(client):
    """Pick a random item that has some data associated with it, and a
    random metric and region pair for that item with data
    available.
    """
    item_list = client.get_available('items')
    num = 0
    while not num:
        item = item_list[int(len(item_list)*random())]
        print "Randomly selected item: {}".format(item['name'])
        selected_entities = {'itemId':  item['id']}
        entity_list = client.list_available(selected_entities)
        num = len(entity_list)
    entities = entity_list[int(num*random())]
    print "Using entities: {}".format(str(entities))
    selected_entities.update(entities)
    return selected_entities


def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--api_host", default="api.gro-intelligence.com")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--item")
    parser.add_argument("--metric")
    parser.add_argument("--region")
    parser.add_argument("--partner_region")
    parser.add_argument("--print_token", action='store_true')
    parser.add_argument("--token")
    args = parser.parse_args()

    assert (args.user_email and args.user_password) or args.token, \
        "Need --token, or --user_email and --user_password"
    access_token = None
    if args.token:
        access_token = args.token
    else:
        access_token = api.client.lib.get_access_token(args.api_host, args.user_email, args.user_password)
    if args.print_token:
        print access_token
        sys.exit(0)
    client = api.client.Client(args.api_host, access_token)

    selected_entities = {}
    if args.item:
        selected_entities['item_id'] = search_for_entity(client, 'items', args.item)
    if args.metric:
        selected_entities['metric_id'] = search_for_entity(client, 'metrics', args.metric)
    if args.region:
        selected_entities['region_id'] = search_for_entity(client, 'regions', args.region)
    if args.partner_region:
        selected_entities['partner_region_id'] = search_for_entity(client, 'regions', args.partner_region)

    if not selected_entities:
        selected_entities = pick_random_entities(client)
    data_series_list = client.get_data_series(**selected_entities)
    if not data_series_list:
        raise Exception("No data series available for {}".format(selected_entities))
    else:
        print "Found {} distinct data series".format(len(data_series_list))
    # Use  print_random_data_series or pick_source_and_print_data_series
    pick_source_and_print_data_series(client, data_series_list)
    # print_random_data_series(client, data_series_list)


if __name__ == "__main__":
    main()
