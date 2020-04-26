import numpy as np
from numpy.testing import assert_almost_equal
import pandas as pd
from pandas.util.testing import assert_frame_equal
import pytest

from api.client.samples.analogous_years.lib import feature_extractions


def create_test_data():
    test_df = pd.DataFrame({'rows': ['row_1', 'row_2', 'row_3'],
                            'col_1': [1, 2, 3],
                            'col_2': [4, 4, 4],
                            'col_3': [7, 8, np.nan]}).set_index('rows')
    return test_df


def test_rm_const_cols():
    expected_df = create_test_data().drop('col_2', axis=1)
    expected_df = expected_df.drop('col_3', axis=1)
    assert_frame_equal(feature_extractions.rm_const_cols(create_test_data()), expected_df)


def test_feature_scaling():
    expected_df = create_test_data()
    for column in list(create_test_data().columns):
        expected_df.loc[:, column] = expected_df[column] - (create_test_data()[column].mean())
        if create_test_data()[column].to_numpy().std() != 0:
            std = np.nanstd(create_test_data()[column].to_numpy())
            expected_df.loc[:, column] = expected_df[column] / std
        else:
            expected_df.loc[:, column] = 0.0
    expected_df = feature_extractions.rm_const_cols(expected_df)
    assert_almost_equal(feature_extractions.feature_scaling(create_test_data()),
                        np.array(expected_df))


def test_cumulative():
    valid_data = create_test_data()
    valid_data.index = ['row_1', 'row_1', 'row_2']
    valid_data.loc[:, 'period'] = valid_data.index
    valid_data.loc[:, 'value'] = valid_data['col_1']
    expected = pd.DataFrame({'period': ['row_1', 'row_2'],
                             'value': [3, 3]}).set_index('period')
    assert_frame_equal(feature_extractions.cumulative(valid_data, 'period', 'value'), expected)


def test_pca_transformation():
    null_data = create_test_data()
    with pytest.raises(ValueError):
        feature_extractions.pca_transformation(null_data)
