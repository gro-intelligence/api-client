import pandas as pd
from pandas.util.testing import assert_frame_equal

from api.client.samples.analogous_years.lib.final_ranks_computation import \
    combined_methods_distances


def data_combined_methods():
    test_data_1 = pd.DataFrame({'rows': ['row_1', 'row_2', 'row_3'],
                                'row_1': [1, 2, 3],
                                'row_2': [4, 5, 6],
                                'row_3': [7, 8, 9]}).set_index('rows')
    test_data_2 = pd.DataFrame({'rows': ['row_1', 'row_2', 'row_3'],
                                'row_4': [1, 2, 3],
                                'row_5': [4, 5, 6],
                                'row_6': [7, 8, 9]}).set_index('rows')
    dictionary_of_df = {'df1': test_data_1, 'df2': test_data_2}
    return dictionary_of_df


def test_combined_methods_distances():
    expected = pd.DataFrame({'rows': ['row_1', 'row_2', 'row_3'],
                             'row_1': [1, 2, 3],
                             'row_2': [4, 5, 6],
                             'row_3': [7, 8, 9],
                             'row_4': [1, 2, 3],
                             'row_5': [4, 5, 6],
                             'row_6': [7, 8, 9],
                             }).set_index('rows')
    assert_frame_equal(combined_methods_distances(data_combined_methods()), expected)
