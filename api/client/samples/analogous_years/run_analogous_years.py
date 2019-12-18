import argparse
from dateutil.parser import parse
from functools import partial
import os

from api.client.gro_client import GroClient

# from api.client.samples.analogous_years.lib import final_ranks_computation
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
    entities = []
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

    for i in range(len(args.metric_ids)):
        entity = {'metric_id': checking('metrics', metric_id_list[i]),
                  'item_id': checking('items', item_id_list[i]),
                  'region_id': checking('regions', region_id_list[0]),
                  'source_id': checking('sources', source_id_list[i]),
                  'frequency_id': checking('frequencies', frequency_id_list[i])}
        entities.append(entity)
    weights = args.weights
    if weights:
        weights = list_length_validator(metric_id_list, weights)
    initial_date = args.initial_date
    final_date = args.final_date
    output_dir = args.output_dir
    report = args.report
    file_name, result = final_ranks_computation.combined_items_final_ranks(
            client, entities, initial_date, final_date,
            methods_list, args.all_ranks, weights, args.ENSO, args.ENSO_weight,
        args.start_date)
    store_result = final_ranks_computation.save_to_csv(
        (file_name, result), output_dir, report, args.all_ranks, logger)
    return store_result


if __name__ == '__main__':
    main()
