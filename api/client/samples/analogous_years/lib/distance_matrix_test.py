import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
import pytest
from scipy.spatial.distance import euclidean
from sklearn.preprocessing import MaxAbsScaler

from api.client.samples.analogous_years.lib import distance_matrix


# TODO: test_dtw_dist_matrix

def create_test_data():
    return pd.DataFrame({'rows': ['2019-04-01 to 2019-08-01',
                                  '2018-04-01 to 2018-08-01',
                                  '2017-04-01 to 2017-08-01'],
                         '2019-04-01 to 2019-08-01': [0, 40, 9],
                         '2018-04-01 to 2018-08-01': [40, 0, 44],
                         '2017-04-01 to 2017-08-01': [9, 44, 0]}). \
        set_index('rows')


def create_test_dates():
    return [{'initial_date': '2018-04-01', 'final_date': '2018-08-01'},
            {'initial_date': '2016-01-04', 'final_date': '2017-01-08'}]


def create_test_methods():
    return ['euclidean', 'invalid_name']


def test_euclidean_distance_matrix():
    test_data_1 = pd.DataFrame({'rows': ['row_1', 'row_2', 'row_3'],
                                'col_1': [1, 2, 3],
                                'col_2': [4, 5, 6],
                                'col_3': [7, 8, 9]}).set_index('rows')
    expected = np.zeros((test_data_1.shape[0], test_data_1.shape[0]))
    for i in range(test_data_1.shape[0]):
        for j in range(i, test_data_1.shape[0]):
            expected[i, j] = euclidean(test_data_1.iloc[i], test_data_1.iloc[j])
            expected[j, i] = euclidean(test_data_1.iloc[i], test_data_1.iloc[j])
    expected = pd.DataFrame(expected)
    expected.columns = test_data_1.index
    expected.index = test_data_1.index
    assert_frame_equal(distance_matrix.euclidean_dist_matrix(test_data_1), expected)


def test_scaled_labeled_method_distances():
    initial_date = create_test_dates()[0]['initial_date']
    final_date = create_test_dates()[0]['final_date']
    method = create_test_methods()[0]
    admissible_test_date = initial_date + ' to ' + final_date
    expected = create_test_data()
    expected = expected[[admissible_test_date]]
    expected.rename(columns={admissible_test_date:method}, inplace=True)
    scaler = MaxAbsScaler()
    expected.loc[:, method] = scaler.fit_transform(expected[[method]])
    assert_frame_equal(distance_matrix.scaled_labeled_method_distances
                       (create_test_data(), initial_date, final_date,
                        method), expected)


def test_scaled_labeled_method_distances_invalid_date():
    invalid_initial_date = create_test_dates()[1]['initial_date']
    invalid_final_date = create_test_dates()[1]['final_date']
    method = create_test_methods()[0]
    with pytest.raises(KeyError):
        distance_matrix.scaled_labeled_method_distances(create_test_data(),
                                                        invalid_initial_date,
                                                        invalid_final_date,
                                                        method)


def test_scaled_labeled_method_distances_invalid_method():
    initial_date = create_test_dates()[0]['initial_date']
    final_date = create_test_dates()[0]['final_date']
    invalid_method = create_test_methods()[1]
    with pytest.raises(ValueError):
        distance_matrix.scaled_labeled_method_distances(create_test_data(),
                                                        initial_date,
                                                        final_date,
                                                        invalid_method)
