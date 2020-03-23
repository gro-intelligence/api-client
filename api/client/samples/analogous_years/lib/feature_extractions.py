"""
This library contains utilities to extract features from
time series
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from tsfresh import extract_features


def ts_feature_extraction(dataframe, num_jobs=0):
    """
    Gets 5 transformed features from 794 features extracted by tsfresh
    :param dataframe: A pandas dataframe
    :param num_jobs: integer, number of parallel processes in tsfresh
    :return: A pandas dataframe
    """
    features = extract_features(dataframe,
                                column_id='period',
                                column_sort='date',
                                column_value='value',
                                n_jobs=num_jobs
                                )
    features = rm_const_cols(features)
    return pca_transformation(features)


def rm_const_cols(dataframe):
    """
    Removes dataframe columns with constant values or null any value
    :param dataframe: A pandas dataframe
    :return: A pandas dataframe
    """
    dataframe = dataframe.dropna(axis=1)  # dropping columns with any null value for PCA
    return dataframe.loc[:, (dataframe != dataframe.iloc[0]).any()]


def feature_scaling(dataframe):
    """
    z-transforms the columns
    :param dataframe: A pandas dataframe
    :return: A pandas dataframe
    """
    # Replace infinities by nulls to finally drop them
    dataframe = dataframe.replace([np.inf, -np.inf], np.nan)
    dataframe = rm_const_cols(dataframe)
    scaler = StandardScaler()
    return scaler.fit_transform(dataframe)


def pca_transformation(dataframe, components=5):
    """
    Computes and retrieves the following number of
    principal component columns given by min(5PCs, 80% variation)
    :param dataframe: A pandas dataframe
    :param components: A positive integer
    :return: A pandas dataframe
    """
    if dataframe.isnull().values.any():
        raise ValueError('Null values in the dataframe, cannot perform PCA')
    # PCA components is bounded above by number of samples
    components = min(components, dataframe.shape[0])
    pca = PCA(n_components=components)
    scaled_dataframe = feature_scaling(dataframe)
    features_pca = pd.DataFrame(pca.fit_transform(scaled_dataframe))
    pca_var_cum = np.cumsum(np.round(pca.explained_variance_ratio_, decimals=4) * 100)
    k = components
    for i in range(components - 1, 0, -1):
        if pca_var_cum[i] < 80:
            k = max(i + 1, components)
            break
    df = features_pca.iloc[:, :k]
    df.index = dataframe.index
    return df


def cumulative(dataframe, column_1, column_2):
    """
    Compute cumulative statistics of the 3rd argument after
    grouping by the second argument in a dataframe
    :param dataframe: A pandas dataframe
    :param column_1: String, a column name
    :param column_2: String, a column name
    :return: A pandas dataframe
    """
    return pd.DataFrame(dataframe.groupby([column_1])[column_2].sum())
