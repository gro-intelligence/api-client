import pandas as pd
import numpy as np
from tsfresh import extract_features
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def tsfresh_feature_extraction(dataframe):
    '''
    :param dataframe:
    :return: pca transformed features
    '''

    dataframe[['end_date', 'start_date']] = dataframe[['end_date', 'start_date']].apply(pd.to_datetime)

    dataframe['year'] = dataframe.apply(lambda x: str(x['end_date'].year), axis=1)
    dataframe['dayofyear'] = dataframe.apply(lambda x: int(x['end_date'].dayofyear), axis=1)
    features =  extract_features(dataframe,
                                 column_id = 'year',
                                 column_sort = 'dayofyear',
                                 column_value = 'value',
                                 )
    features = remove_constant(features)

    return pca_transformation(features)

def remove_constant(dataframe):
    '''
    :param dataframe: A
    :return:
    '''
    return dataframe.loc[:, (dataframe != dataframe.iloc[0]).any()]

def feature_scaling(dataframe):
    '''
    :param dataframe: a pandas dataframe with continuous variables
    :return: normalized variables to be used for PCA
    '''
    scaler = StandardScaler()
    scaler.fit(dataframe)
    return scaler.transform(dataframe)

def pca_transformation(dataframe, n=20):
    '''
    :param dataframe: A normalized dataframe
    :param n: number of components of PCA
    :return: transformed features in a pandas dataframe which capture at least 95% of the variability
    '''
    pca = PCA(n_components=n)
    scaled_dataframe = feature_scaling(dataframe)
    pca.fit(scaled_dataframe)
    features_pca = pd.DataFrame(pca.fit_transform(scaled_dataframe))
    pca_var_cum = np.cumsum(np.round(pca.explained_variance_ratio_, decimals=4)*100)
    for i in range(n - 1, 0, -1):
        if pca_var_cum[i] < 95:
            k = max(i + 1, n)
            break
    return features_pca.iloc[: , :k]




    
