"""
This library contains utilities for
1. consolidating the final ranks
2. saving a dataframe in a chosen location
"""
from functools import reduce
import os

import matplotlib
matplotlib.use('agg')
import seaborn as sns

import numpy as np
import pandas as pd

from groclient import GroClient
from api.client.samples.analogous_years.lib import \
    distance_matrix, \
    feature_extractions, \
    get_transform_data

DEFAULT_API_HOST = 'api.gro-intelligence.com'


def common_start_date(client, data_series, provided_start_date=None):
    """Computes the earliest available start date from which all gro-data_series have data"""
    logger = client.get_logger()
    start_date_list = []
    if provided_start_date:
        start_date_list.append(provided_start_date)
    for i in range(len(data_series)):
        dates = client.get_data_points(**data_series[i])
        if len(dates) == 0:
            msg = "No data found for the following gro-data_series - {}".format(data_series[i])
            logger.warning(msg)
            raise Exception
        else:
            start_date_list.append(dates[0]['start_date'])
    start_date = max(start_date_list)
    for i in range(len(data_series)):
        data_series[i]['start_date'] = start_date
    return {'data_series': data_series, 'start_date': start_date}


def enso_data(start_date):
    enso_data_series = {'metric_id': 15851977,
                        'item_id': 13495,
                        'region_id': 0,
                        'source_id': 124,
                        'start_date': start_date,
                        'frequency_id': 6}
    return enso_data_series


def get_file_name(api_token, data_series_list, initial_date, final_date,
                  api_host=DEFAULT_API_HOST):
    """Combines region, items, and dates to return a string"""
    client = GroClient(api_host, api_token)
    logger = client.get_logger()
    key_words = [client.lookup('regions', data_series_list[0]['region_id'])['name']]
    for i in range(len(data_series_list)):
        key_words.append(client.lookup('items', data_series_list[i]['item_id'])['name'])
    key_words.append(initial_date)
    key_words.append(final_date)
    logger.info("\n Computing analogous years' ranks in {} with respect to {} between {} and {} \n".
                format(key_words[0], key_words[1:-2], initial_date, final_date))
    combined_name = '_'.join(key_words)
    return combined_name


def time_series(client, data_series, initial_date, final_date):
    """
    retrieves a sub-time series of a time series associated with a gro data_series
    :param client: GroClient
    :param data_series: A dictionary of Gro data_series
    :param final_date: 'YYYY-MM-DD'
    :param initial_date: 'YYYY-MM-DD'
    :return: A dataframe with data from the relevant dates
    """
    logger = client.get_logger()
    entities = {'metric_id', 'item_id', 'region_id', 'source_id', 'frequency_id', 'start_date'}
    data_series = {k: data_series[k] for k in data_series if k in entities}
    data = get_transform_data.get_data(client, **data_series)
    try:
        ts = get_transform_data.extract_time_periods_by_dates(data, initial_date, final_date)
        return ts
    except Exception as e:
        message = ('Please check availability of data for {}'.format(client.lookup(
            'items', data_series['item_id'])['name']))
        logger.warning(message)
        raise e


def ay_tsfresh(timeseries, num_jobs=0):
    tsfresh_features = feature_extractions.ts_feature_extraction(
        timeseries, num_jobs=num_jobs)
    return distance_matrix.euclidean_dist_matrix(tsfresh_features)


def ay_cumulative(timeseries, group='period', value='value'):
    cumulative_value = feature_extractions.cumulative(timeseries, group, value)
    return distance_matrix.euclidean_dist_matrix(cumulative_value)


def ay_euclidean(timeseries):
    transposed_pivot_time_series = get_transform_data.stack_time_periods_by_ddmm(
        timeseries).transpose()
    return distance_matrix.euclidean_dist_matrix(transposed_pivot_time_series)


def ay_dtw(timeseries):
    pivot_time_series = get_transform_data.stack_time_periods_by_ddmm(timeseries)
    return distance_matrix.dtw_dist_matrix(pivot_time_series)


def ranked_df_dictionary(client, data_series, initial_date, final_date, item, methods_list,
                         tsfresh_num_jobs=0):
    """
    Returns a dictionary whose keys are given by a 'method_item' and values are the dataframes
    of distances computed for that item using that method. Example: key: cumulative_Rainfall
    :param client: GroClient
    :param data_series: A dictionary of Gro data_series
    :param initial_date: 'YYYY-MM-DD'
    :param final_date: 'YYYY-MM-DD'
    :param item: Gro Item
    :param methods_list: a sublist of ['cumulative', 'euclidean', 'ts-features', 'dtw']
    :param tsfresh_num_jobs: integer, number of parallel processes in tsfresh
    :return: Dictionary of dataframes
    """
    ts = time_series(client, data_series, initial_date, final_date)
    dictionary_of_methods = {'cumulative_' + item: ay_cumulative,
                             'euclidean_' + item: ay_euclidean,
                             'dtw_' + item: ay_dtw,
                             'ts-features_' + item: ay_tsfresh}
    ranked_dfs = {}
    for key, value in dictionary_of_methods.items():
        if key.split('_')[0] in methods_list:
            if key.split('_')[0] == 'ts-features':
                ranked_dfs[key] = distance_matrix.scaled_labeled_method_distances(
                    value(ts, num_jobs=tsfresh_num_jobs), initial_date, final_date, key)
            else:
                ranked_dfs[key] = distance_matrix.scaled_labeled_method_distances(
                    value(ts), initial_date, final_date, key)
    return ranked_dfs


def merge_using_index_column(left, right):
    """
    Merges two dataframes using the indices
    :param left: pandas dataframe
    :param right: pandas dataframe
    :return: pandas dataframe
    """
    return pd.merge(left, right, left_index=True, right_index=True)


def combined_methods_distances(dictionary_of_df):
    """
    Merge all the df listed in the dictionary into a single dataframe containing the scaled
    distances. The keys of the dictionary in this case are the methods
    used to obtain the distances
    :param dictionary_of_df: A dictionary of pandas dataframes
    :return: A dataframe
    """
    rank_df = reduce(merge_using_index_column, list(dictionary_of_df.values()))
    return rank_df


def analogous_years(api_token, data_series_list, initial_date, final_date,
                    methods_list=['euclidean', 'cumulative', 'ts-features'],
                    all_ranks=None, weights=None, enso=None, enso_weight=None,
                    provided_start_date=None, tsfresh_num_jobs=0,
                    api_host=DEFAULT_API_HOST):
    """
    Use L^2 distance function to combine weighted distances from multiple gro-data_series
    and return the rank
    :param api_token: string, Gro-api token
    :param data_series_list: list of dictionaries containing gro data series
    :param initial_date: A date in YYYY-MM-DD format
    :param final_date: A date in YYYY-MM-DD format
    :param methods_list: a sublist of ['cumulative', 'euclidean', 'ts-features', 'dtw']
    :param all_ranks: Boolean to determine if all ranks will be displayed or a composite rank
    :param weights: Float determining the weight given to each data_series
    :param enso: Boolean to include ENSO
    :param enso_weight: Float
    :param provided_start_date: A string in YYYY-MM-DD format
    :param tsfresh_num_jobs: integer, number of parallel processes in tsfresh
    :param api_host:
    :return: A tuple (string, dataframe)
    The string contains '_' separated region, item, date
    The dataframe contains integer values (ranks)
    """
    client = GroClient(api_host, api_token)
    combined_items_distances = None
    data_series_list = common_start_date(client, data_series_list, provided_start_date)[
        'data_series']
    start_date = common_start_date(client, data_series_list, provided_start_date)[
        'start_date']
    if not weights:
        weights = [1] * len(data_series_list)
    if enso:
        data_series_list.append(enso_data(start_date))
        if enso_weight:
            weights.append(enso_weight)
        else:
            weights.append(1)
    for i in range(len(data_series_list)):
        gro_item = client.lookup('items', data_series_list[i]['item_id'])['name']
        combined_methods_distances_df = combined_methods_distances(
            ranked_df_dictionary(
                client, data_series_list[i], initial_date,
                final_date, gro_item, methods_list, tsfresh_num_jobs=tsfresh_num_jobs))
        numpy_combined_methods_distances = combined_methods_distances_df.values
        if combined_items_distances is None:
            combined_items_distances = np.zeros(numpy_combined_methods_distances.shape)
        combined_items_distances = combined_items_distances + np.power(
            weights[i] * numpy_combined_methods_distances, 2)
    combined_items_distances = pd.DataFrame(np.sqrt(combined_items_distances),
                                            index=combined_methods_distances_df.index,
                                            columns=combined_methods_distances_df.columns)
    combined_items_distances.loc[:, 'composite'] = combined_items_distances.sum(axis=1, skipna=True)
    ranks = []
    for column_name in combined_items_distances.columns:
        combined_items_distances.sort_values(by=column_name, inplace=True)
        column_new_name = column_name.split('_')[0] + '_rank'
        combined_items_distances.loc[:, column_new_name] = \
            combined_items_distances.reset_index().index + 1
        ranks.append(column_new_name)
        combined_items_distances.sort_index(inplace=True)
    if all_ranks:
        display_dataframe = combined_items_distances[ranks]
    else:
        display_dataframe = combined_items_distances[['composite_rank']]
    return display_dataframe


def generate_correlation_scatterplots(api_token, dataframe, folder_name, output_dir='',
                                      api_host=DEFAULT_API_HOST):
    client = GroClient(api_host, api_token)
    logger = client.get_logger()
    folder_path = os.path.join(output_dir, './ranks_csv', folder_name)
    sns.set(style="ticks")
    sns_plot = sns.pairplot(dataframe, diag_kind=None)
    correlation_plot_path = os.path.join(folder_path, 'correlation_plot.png')
    logger.info("Saving scatterplots in {}".format(correlation_plot_path))
    return sns_plot.savefig(correlation_plot_path)


def generate_correlation_matrix(dataframe):
    return dataframe.corr(method='spearman')


def save_to_csv(api_token, dataframe, folder_name, file_name='', output_dir='',
                api_host=DEFAULT_API_HOST):
    """ save the dataframe into csv file called <output_dir>/ranks_csv/ranks.csv """
    client = GroClient(api_host, api_token)
    logger = client.get_logger()
    folder_path = os.path.join(output_dir, './ranks_csv', folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, file_name)
    logger.info("\n Saving {} in {} \n".format(file_name, file_path))
    return dataframe.to_csv(file_path)
