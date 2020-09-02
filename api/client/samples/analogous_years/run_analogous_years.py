import argparse
from dateutil.parser import parse
from functools import partial
import os

from groclient import GroClient

from api.client.samples.analogous_years.lib import final_ranks_computation

API_HOST = "api.gro-intelligence.com"


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
    """Checks if the provided dates are valid dates in YYYY-MM-DD format"""
    try:
        parse(s)
        return s
    except ValueError:
        msg = "Not a valid date in YYYY-MM-DD format: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def list_length_validator(list1, list2):
    """Checks if the 2nd list is of the same length as the first and returns the second list
    on success"""
    if len(list1) != len(list2):
        msg = "Mismatch between the number of entries in {} and {}".format(list1, list2)
        raise argparse.ArgumentTypeError(msg)
    else:
        return list2


def check_if_exists(entity_type, entity_value, api_token, api_host=API_HOST):
    """Checks if the Gro-entity_id exists"""
    client = GroClient(api_host, api_token)
    logger = client.get_logger()
    try:
        client.lookup(entity_type, entity_value)
        return entity_value
    except Exception as e:
        message = "Gro-{}_id invalid: '{}'.".format(entity_type, entity_value)
        logger.warning(message)
        raise e


def get_data_series_list(region_id_list, item_id_list, metric_id_list, source_id_list,
                         frequency_id_list, api_token, api_host=API_HOST):
    # checking if the length of the list for metric_id, item_id, source_id and
    # frequency_id match
    item_id_list = list_length_validator(metric_id_list, item_id_list)
    source_id_list = list_length_validator(metric_id_list, source_id_list)
    frequency_id_list = list_length_validator(metric_id_list, frequency_id_list)
    data_series_list = []
    checking = partial(check_if_exists, api_token=api_token)
    for i in range(len(metric_id_list)):
        data_series = {'metric_id': checking('metrics', metric_id_list[i]),
                       'item_id': checking('items', item_id_list[i]),
                       'region_id': checking('regions', region_id_list[0]),
                       'source_id': checking('sources', source_id_list[i]),
                       'frequency_id': checking('frequencies', frequency_id_list[i])}
        data_series_list.append(data_series)
    return data_series_list


def main():
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
                        help='frequency_ids of the corresponding gro-data_series separated by '
                             'spaces')
    parser.add_argument('-w', '--weights', nargs='+', type=float,
                        help='weights corresponding to the data_series separated by spaces')
    parser.add_argument('--initial_date', required=True, type=valid_date,
                        help='Format YYYY-MM-DD')
    parser.add_argument('--final_date', required=True, type=valid_date,
                        help='Format YYYY-MM-DD')
    parser.add_argument('--groapi_token', type=str, default=os.environ['GROAPI_TOKEN'],
                        help='GroAPI token')
    parser.add_argument('--api_host', type=str, default='api.gro-intelligence.com',
                        help='api host')
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
    parser.add_argument('--num_jobs', type=int, default=0,
                        help='number of parallel processes for tsfresh')
    args = parser.parse_args()
    data_series_list = get_data_series_list(args.region_id, args.item_ids, args.metric_ids,
                                            args.source_ids, args.frequency_ids,
                                            api_token=args.groapi_token, api_host=args.api_host)
    folder_name = final_ranks_computation.get_file_name(args.groapi_token, data_series_list,
                                                        initial_date=args.initial_date,
                                                        final_date=args.final_date,
                                                        api_host=args.api_host)
    result = final_ranks_computation.analogous_years(
        args.groapi_token, data_series_list, args.initial_date, args.final_date,
        methods_list=args.methods, all_ranks=args.all_ranks, weights=args.weights, enso=args.ENSO,
        enso_weight=args.ENSO_weight, provided_start_date=args.start_date,
        tsfresh_num_jobs=args.num_jobs, api_host=args.api_host)
    final_ranks_computation.save_to_csv(args.groapi_token, result,
                                        folder_name,
                                        file_name='ranks.csv',
                                        output_dir=args.output_dir,
                                        api_host=args.api_host)
    if args.all_ranks and args.report:
        correlation_matrix = final_ranks_computation.generate_correlation_matrix(result)
        final_ranks_computation.save_to_csv(args.groapi_token, correlation_matrix, folder_name,
                                            file_name='correlation_matrix.csv',
                                            output_dir=args.output_dir, api_host=args.api_host)
        final_ranks_computation.generate_correlation_scatterplots(args.groapi_token, result,
                                                                  folder_name,
                                                                  output_dir=args.output_dir,
                                                                  api_host=args.api_host)
    return None


if __name__ == '__main__':
    main()
