import argparse
from dateutil.parser import parse
from functools import partial
import os

from api.client.gro_client import GroClient

from lib import final_ranks_computation


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def valid_date(s):
    try:
        parse(s)
        return s
    except ValueError:
        msg = "Not a valid date in YYYY-MM-DD format: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def list_length_validator(list1, list2):
    if len(list1) != len(list2):
        msg = "Mismatch between the number of entries in {} and {}".format(list1, list2)
        raise argparse.ArgumentTypeError(msg)
    else:
        return list2


def check_if_exists(entity_type, entity_value, client):
    logger = client.get_logger()
    try:
        client.lookup(entity_type, entity_value)
        return entity_value
    except Exception as e:
        message = "Gro-{}_id invalid: '{}'.".format(entity_type, entity_value)
        logger.warning(message)
        raise e


def main():
    API_HOST = "api.gro-intelligence.com"
    parser = argparse.ArgumentParser(description='ConGrouent Years')
    parser.add_argument('-m', '--metric_ids', nargs='+', type=int, default=[2100031, 2540047],
                        help='metric_ids separated by spaces')
    parser.add_argument('-i', '--item_ids', nargs='+', type=int, default=[2039, 3457],
                        help='item_ids corresponding to metric_ids separated by spaces')
    parser.add_argument('-r', '--region_id', nargs='+', type=int, default=[100000100],
                        help='region id of the region')
    parser.add_argument('-s', '--source_ids', nargs='+', type=int, default=[35, 26],
                        help='specify the source_ids of the corresponding item-metric '
                             'separated by spaces')
    parser.add_argument('-f', '--frequency_ids', nargs='+', type=int, default=[1, 1],
                        help='frequency_ids of the corresponding gro-entities separated by spaces')
    parser.add_argument('-w', '--weights', nargs='+', type=float,
                        help='weights corresponding to the entities separated by spaces')
    parser.add_argument('--initial_date', required=True, type=valid_date,
                        help='Format YYYY-MM-DD')
    parser.add_argument('--final_date', required=True, type=valid_date,
                        help='Format YYYY-MM-DD')
    parser.add_argument('--groapi_token', type=str, default=os.environ['GROAPI_TOKEN'],
                        help='GroAPI token')
    parser.add_argument('--output_dir', type=str, default='')
    parser.add_argument('--report', type=str2bool, default=True,
                        help='Generates correlation matrix and scatter plots between ranks')
    parser.add_argument('--methods', nargs='+', type=str,
                        default=['euclidean', 'cumulative', 'ts-features'],
                        choices=['euclidean', 'cumulative', 'ts-features', 'dtw'],
                        help='methods of rank calculation. The arguments can be one or more of'
                             'the following strings - "euclidean", "ts features", "cumulative",'
                             '"dtw"')
    parser.add_argument('--start_date', type=valid_date, help='start date of all the Gro data '
                                                              'series to be used for this '
                                                              'analysis')
    parser.add_argument("--ENSO", action='store_true', help='Include ENSO for rank distance '
                                                            'calculation')
    parser.add_argument('--ENSO-weight', type=float, default=1, help='Weight of the ENSO index')
    parser.add_argument('--all_ranks', action='store_true', help='Lets you see all the ranks'
                                                                 'as opposed to separate method'
                                                                 'ranks')

    args = parser.parse_args()
    entities_weights = []
    item_name_list = []
    methods_list = args.methods
    access_token = args.groapi_token
    client = GroClient(API_HOST, access_token)
    logger = client.get_logger()
    checking = partial(check_if_exists, client=client)

    metric_id_list = args.metric_ids
    item_id_list = list_length_validator(metric_id_list, args.item_ids)
    region_id_list = args.region_id
    source_id_list = list_length_validator(metric_id_list, args.source_ids)
    frequency_id_list = list_length_validator(metric_id_list, args.frequency_ids)
    if args.weights:
        weights = args.weights
        weights = list_length_validator(metric_id_list, weights)
    else:
        weights = [1] * len(metric_id_list)
    start_date_list = []
    if args.start_date:
        start_date_list.append(args.start_date)
    for i in range(len(args.metric_ids)):
        entity = {'metric_id': checking('metrics', metric_id_list[i]),
                  'item_id': checking('items', item_id_list[i]),
                  'region_id': checking('regions', region_id_list[0]),
                  'source_id': checking('sources', source_id_list[i]),
                  'frequency_id': checking('frequencies', frequency_id_list[i])}
        dates = client.get_data_points(**entity)
        if len(dates) == 0 or ('start_date' not in dates[0]):
            msg = "No data found for the following gro-entity - {}".format(entity)
            raise argparse.ArgumentTypeError(msg)
        else:
            start_date_list.append(dates[0]['start_date'])
    start_date = max(start_date_list)
    for i in range(len(metric_id_list)):
        entities_weights.append({'metric_id': metric_id_list[i],
                                 'item_id': item_id_list[i],
                                 'region_id': region_id_list[0],
                                 'source_id': source_id_list[i],
                                 'frequency_id': frequency_id_list[i],
                                 'start_date': start_date,
                                 'weight': weights[i]})
        item_name = client.lookup('items', item_id_list[i])['name']
        item_name_list.append(item_name)
    if args.ENSO:
        enso_entity_weight = {'metric_id': 15851977,
                              'item_id': 13495,
                              'region_id': 0,
                              'source_id': 124,
                              'start_date': start_date,
                              'frequency_id': 6,
                              'weight': args.ENSO_weight}
        entities_weights.append(enso_entity_weight)
        enso_name = client.lookup('items', 13495)['name']
        item_name_list.append(enso_name)
    complete_item_name = '_'.join(item_name_list)

    initial_date = args.initial_date
    final_date = args.final_date
    output_dir = args.output_dir
    report = args.report
    region = client.lookup('regions', entities_weights[0]['region_id'])['name']
    file_name = region + '_' + complete_item_name + '_' + \
                initial_date + '_' + final_date + '_ranks'
    result = final_ranks_computation.save_to_csv(
        final_ranks_computation.combined_items_final_ranks(
            client, entities_weights, initial_date, final_date, methods_list, args.all_ranks),
        output_dir, file_name, report, args.all_ranks, logger)
    return result


if __name__ == '__main__':
    main()
