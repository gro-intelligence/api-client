"""
This library contains utilities for
1. consolidating the final ranks
2. saving a dataframe in a chosen location
"""
from functools import reduce
import os

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import comb

from . import \
    distance_matrix, \
    feature_extractions, \
    get_transform_data


def time_series(client, entity, initial_date, final_date):
    """
    retrieves a sub-time series of a time series associated with a gro entity
    :param client: GroClient
    :param entity: A dictionary of GroEntity
    :param final_date: 'YYYY-MM-DD'
    :param initial_date: 'YYYY-MM-DD'
    :return: A dataframe with data from the relevant dates
    """
    logger = client.get_logger()
    data = get_transform_data.get_data(client, **entity)
    consolidated_data = get_transform_data.combine_subregions(data)
    try:
        ts = get_transform_data.extract_time_periods_by_dates(consolidated_data,
                                                              initial_date,
                                                              final_date)
        return ts
    except Exception as e:
        message = ('Please check availability of data for {}'.format(client.lookup(
            'items', entity['item_id'])['name']))
        logger.warning(message)
        raise e


def ay_tsfresh(timeseries):
    tsfresh_features = feature_extractions.ts_feature_extraction(timeseries)
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


def ranked_df_dictionary(client, entity, initial_date, final_date, item, methods_list):
    """
    Returns a dictionary whose keys are given by a 'method_item' and values are the dataframes
    of distances computed for that item using that method. Example: key: cumulative_Rainfall
    :param client: GroClient
    :param entity: A dictionary of Gro entity
    :param initial_date: 'YYYY-MM-DD'
    :param final_date: 'YYYY-MM-DD'
    :param item: Gro Item
    :param methods_list: a sublist of ['cumulative', 'euclidean', 'ts-features', 'dtw']
    :return: Dictionary of dataframes
    """
    ts = time_series(client, entity, initial_date, final_date)
    dictionary_of_methods = {'cumulative_' + item: ay_cumulative,
                             'euclidean_' + item: ay_euclidean,
                             'dtw_' + item: ay_dtw,
                             'ts-features_' + item: ay_tsfresh}
    ranked_dfs = {}
    for key, value in dictionary_of_methods.items():
        if key.split('_')[0] in methods_list:
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


def combined_items_final_ranks(client, entities_weights, initial_date, final_date, methods_list,
                               all_ranks):
    """
    Use L^2 distance function to combine weighted distances from multiple gro-entities
    and return the rank
    :param client: Gro_client
    :param entities_weights: A dictionary of gro entity and weight associated to the gro entity
    :param initial_date: A date in YYYY-MM-DD format
    :param final_date: A date in YYYY-MM-DD format
    :param methods_list: a sublist of ['cumulative', 'euclidean', 'ts-features', 'dtw']
    :param all_ranks: Boolean to determine if all ranks will be displayed or a composite rank
    :return: A dataframe containing integer values (ranks)
    """
    combined_items_distances = None
    for entity_weight in entities_weights:
        gro_item = client.lookup('items', entity_weight['item_id'])['name']
        weight = entity_weight.pop('weight')
        combined_methods_distances_df = combined_methods_distances(
            ranked_df_dictionary(
                client, entity_weight, initial_date,
                final_date, gro_item, methods_list))
        numpy_combined_methods_distances = combined_methods_distances_df.values
        if combined_items_distances is None:
            combined_items_distances = np.zeros(numpy_combined_methods_distances.shape)
        combined_items_distances = combined_items_distances + np.power(
            weight * numpy_combined_methods_distances, 2)
    combined_items_distances = pd.DataFrame(np.sqrt(combined_items_distances),
                                            index=combined_methods_distances_df.index,
                                            columns=combined_methods_distances_df.columns)
    combined_items_distances['composite'] = combined_items_distances.sum(axis=1, skipna=True)
    ranks = []
    for column_name in combined_items_distances.columns:
        combined_items_distances.sort_values(by=column_name, inplace=True)
        column_new_name = column_name.split('_')[0] + '_rank'
        combined_items_distances[column_new_name] = \
            combined_items_distances.reset_index().index + 1
        ranks.append(column_new_name)
        combined_items_distances.sort_index(inplace=True)
    if all_ranks:
        display = combined_items_distances[ranks]
    else:
        display = combined_items_distances['composite_rank']
    return display


def save_to_csv(dataframe, output_dir, file_name, report, all_ranks, logger):
    """ save the dataframe into csv file called <output_dir>/ranks_csv/ranks.csv """
    folder_path = os.path.join(output_dir, './ranks_csv', file_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    if report and all_ranks:
        fig = plt.figure()
        k = 0
        rows = np.ceil(comb(len(list(dataframe.columns)), 2) / 2)
        for i in range(len(dataframe.columns)):
            for j in range(i + 1, len(dataframe.columns)):
                k = k + 1
                plt.subplot(rows, 2, k)
                plt.subplots_adjust(left=None, bottom=None, right=None, top=None,
                                    wspace=0.8, hspace=0.8)
                plt.plot(dataframe.columns[i],
                         dataframe.columns[j],
                         'b.',
                         data=dataframe)
                plt.xlabel(dataframe.columns[i].split('_')[0])
                plt.ylabel(dataframe.columns[j].split('_')[0])
        correlation_plot_path = os.path.join(folder_path, 'correlation_plot.png')
        fig.savefig(correlation_plot_path)
        logger.info("Saving correlation plot in {}".format(correlation_plot_path))
        correlation_matrix_path = os.path.join(folder_path, 'correlation_matrix.csv')
        dataframe.corr(method='spearman').to_csv(correlation_matrix_path)
        logger.info("Saving correlation matrix csv file in {}".format(correlation_matrix_path))
    file_path = os.path.join(folder_path, file_name + '.csv')
    logger.info("Saving ranks as csv file in {}".format(file_path))
    return dataframe.to_csv(file_path)
