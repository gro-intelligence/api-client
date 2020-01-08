"""
This library contains utilities for
1. computing pairwise distances between rows of a dataframe
2. selecting and sorting a specified column of the dataframe
"""

from dtw import dtw
import numpy as np
import pandas as pd
from scipy.spatial.distance import euclidean, pdist, squareform
from sklearn.preprocessing import MaxAbsScaler


def euclidean_dist_matrix(dataframe):
    """
    Calculates a square matrix of euclidean distances between the
    rows of the input dataframe
    :param dataframe: A pandas dataframe
    :return: A pandas dataframe
    """
    df = pd.DataFrame(squareform(pdist(dataframe)))
    df.index = dataframe.index
    df.columns = dataframe.index
    return df


def dtw_dist_matrix(dataframe):
    """
    Calculates a square matrix of dynamic time warping distances between the
    rows of the input dataframe
    :param dataframe: A pandas dataframe
    :return: A pandas dataframe
    """
    distance_matrix = np.zeros((len(dataframe.columns), len(dataframe.columns)))
    for i in range(len(dataframe.columns)):
        for j in range(i, len(dataframe.columns)):
            distance_matrix[i, j] = dtw(dataframe.iloc[:, i],
                                        dataframe.iloc[:, j],
                                        dist=euclidean)[0]
            distance_matrix[j, i] = dtw(dataframe.iloc[:, i],
                                        dataframe.iloc[:, j],
                                        dist=euclidean)[0]
    distance_matrix = pd.DataFrame(distance_matrix)
    distance_matrix.columns = dataframe.columns
    distance_matrix.index = dataframe.columns
    return distance_matrix


def scaled_labeled_method_distances(distance_matrix_df, initial_date, final_date, method):
    """
    Retrieves and scales a column of the input dataframe
    :param distance_matrix_df: A pandas dataframe
    :param final_date: 'YYYY-MM-DD'
    :param initial_date: 'YYYY-MM-DD'
    :param method: method used to compute the distance from the list
    ['cumulative' + GroItem, 'euclidean' + GroItem, 'dtw' + GroItem, 'tsfresh' + GroItem]
    :return: A pandas dataframe
    """
    list_of_methods = ['euclidean', 'cumulative', 'dtw', 'ts-features']
    if method.split('_')[0] not in list_of_methods:
        raise ValueError('Method of calculation unavailable')
    column_name = initial_date + ' to ' + final_date
    ranked_periods_df = pd.DataFrame(distance_matrix_df[column_name])
    scaler = MaxAbsScaler()
    ranked_periods_df.loc[:, column_name] = scaler.fit_transform(ranked_periods_df[[column_name]])
    ranked_periods_df.rename(columns={column_name: method}, inplace=True)
    return ranked_periods_df
