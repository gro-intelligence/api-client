from groclient import GroClient
import mock
import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
import pytest

from api.client.samples.analogous_years.lib import get_transform_data


def create_test_data():
    return {'end_date': ['2019-07-31T00:00:00.000Z',
                         '2005-08-28T00:00:00.000Z',
                         '2000-03-01T00:00:00.000Z',
                         '2005-08-28T00:00:00.000Z'],
            'frequency_id': [1, 1, 1, 1],
            'input_unit_id': [2, 2, 2, 2],
            'input_unit_scale': [1, 1, 1, 1],
            'item_id': [2039, 2039, 2039, 2039],
            'metric_id': [2100031, 2100031, 2100031, 2100031],
            'region_id': [13100, 13065, 1107, 13064],
            'start_date': ['2019-07-31T00:00:00.000Z',
                           '2005-08-28T00:00:00.000Z',
                           '2000-03-01T00:00:00.000Z',
                           '2005-08-28T00:00:00.000Z'],
            'unit_id': [2, 2, 2, 2],
            'value': [0.13002748115958, 1.17640700229636,
                      2.39664378851418, 1.10551943121531]}


def create_test_data_for_get_data():
    return pd.DataFrame({'end_date': pd.to_datetime(['2019-07-31T00:00:00.000Z',
                                                     '2019-08-03T00:00:00.000Z',
                                                     '2019-08-05T00:00:00.000Z',
                                                     '2019-08-10T00:00:00.000Z']),
                         'frequency_id': [1, 1, 1, 1],
                         'input_unit_id': [2, 2, 2, 2],
                         'input_unit_scale': [1, 1, 1, 1],
                         'item_id': [2039, 2039, 2039, 2039],
                         'metric_id': [2100031, 2100031, 2100031, 2100031],
                         'region_id': [1215, 1215, 1215, 1215],
                         'start_date': pd.to_datetime(['2019-07-31T00:00:00.000Z',
                                                       '2019-08-03T00:00:00.000Z',
                                                       '2019-08-05T00:00:00.000Z',
                                                       '2019-08-10T00:00:00.000Z']),
                         'unit_id': [2, 2, 2, 2],
                         'value': [0.13002748115958, 1.17640700229636,
                                   2.39664378851418, 1.10551943121531]})


@mock.patch('api.client.gro_client.GroClient.get_df', return_value=create_test_data_for_get_data())
def test_get_data(test_data_1):
    client = GroClient('mock_website', 'mock_access_token')
    start_date_bound = '2019-08-01T00:00:00.000Z'
    expected = pd.DataFrame(pd.DataFrame({'end_date': pd.to_datetime(['2019-08-01T00:00:00.000Z',
                                                                      '2019-08-02T00:00:00.000Z',
                                                                      '2019-08-03T00:00:00.000Z',
                                                                      '2019-08-04T00:00:00.000Z',
                                                                      '2019-08-05T00:00:00.000Z',
                                                                      '2019-08-06T00:00:00.000Z',
                                                                      '2019-08-07T00:00:00.000Z',
                                                                      '2019-08-08T00:00:00.000Z',
                                                                      '2019-08-09T00:00:00.000Z',
                                                                      '2019-08-10T00:00:00.000Z']),
                                          'value': [0.13002748115958, 1.17640700229636,
                                                    1.17640700229636, 2.39664378851418,
                                                    2.39664378851418, 2.39664378851418,
                                                    2.39664378851418, 1.10551943121531,
                                                    1.10551943121531, 1.10551943121531]}))
    expected.index = expected['end_date']
    expected = expected.asfreq('D')

    test_data = get_transform_data.get_data(client, 'metric_id', 'item_id', 'region_id',
                                            'source_id', 'frequency_id', start_date_bound)
    assert_frame_equal(test_data, expected)


def test_combine_subregions_with_subregion():
    test_data = pd.DataFrame(create_test_data())
    test_data.loc[:, 'end_date'] = pd.to_datetime(test_data['end_date'])
    test_data_subregion = test_data[['end_date', 'value']]
    expected_subregion = pd.DataFrame({'end_date': ['2000-03-01T00:00:00.000Z',
                                                    '2005-08-28T00:00:00.000Z',
                                                    '2019-07-31T00:00:00.000Z'],
                                       'value': [2.39664378851418,
                                                 2.28192643351167,
                                                 0.13002748115958]})
    utc_tz = False
    if pd.to_datetime(expected_subregion['end_date'][0]).tzinfo:
        utc_tz = True
    # Depending on the version of pandas, the data type of the datetime object
    # can vary between 'datetime64[ns, UTC]' and 'datetime64[ns]'
    expected_subregion.loc[:, 'end_date'] = pd.to_datetime(expected_subregion['end_date'],
                                                           utc=utc_tz)
    # The order of the columns after applying consolidation function is the following
    expected_subregion = expected_subregion[['value', 'end_date']]
    # The dataframes index columns is same as 'end_date' column
    expected_subregion.index = expected_subregion['end_date']
    # Test the equality of frames
    # expected_subregion.index = pd.to_datetime(expected_subregion.index)
    expected_subregion.loc[:, 'end_date'] = expected_subregion.index
    assert_frame_equal(get_transform_data.combine_subregions(test_data_subregion),
                       expected_subregion)


def test_combine_subregions_with_nosubregion():
    test_data = pd.DataFrame(create_test_data())
    test_data.loc[:, 'end_date'] = pd.to_datetime(test_data['end_date'])
    test_data_subregion = test_data[['end_date', 'value']]
    test_data_nosubregion = test_data_subregion.drop(test_data_subregion.index[-1])
    expected_nosubregion = pd.DataFrame({'end_date': ['2019-07-31T00:00:00.000Z',
                                                      '2005-08-28T00:00:00.000Z',
                                                      '2000-03-01T00:00:00.000Z'],
                                         'value': [0.13002748115958,
                                                   1.17640700229636,
                                                   2.39664378851418]})
    utc_tz = False
    if pd.to_datetime(expected_nosubregion['end_date'][0]).tzinfo:
        utc_tz = True
    # Depending on the version of pandas, the data type of the datetime object
    # can vary between 'datetime64[ns, UTC]' and 'datetime64[ns]'
    expected_nosubregion.index = expected_nosubregion['end_date']
    expected_nosubregion.loc[:, 'end_date'] = pd.to_datetime(expected_nosubregion['end_date'],
                                                             utc=utc_tz)
    expected_nosubregion.index = pd.to_datetime(expected_nosubregion.index, utc=utc_tz)
    expected_nosubregion.loc[:, 'end_date'] = pd.to_datetime(expected_nosubregion.index, utc=utc_tz)
    assert_frame_equal(get_transform_data.combine_subregions(test_data_nosubregion),
                       expected_nosubregion)


def test_combine_subregions_nodate():
    test_data = pd.DataFrame(create_test_data())
    test_data.loc[:, 'end_date'] = pd.to_datetime(test_data['end_date'])
    test_data_subregion = test_data[['end_date', 'value']]
    test_data_no_date = test_data_subregion.drop('end_date', axis=1)
    with pytest.raises(KeyError):
        get_transform_data.combine_subregions(test_data_no_date)


def test_extract_time_periods_by_dates_invalid_test_dates():
    test_data = pd.DataFrame(create_test_data())
    test_data.loc[:, 'end_date'] = pd.to_datetime(test_data['end_date'])
    # this is an invalid date because the initial and final dates are not within 1 year
    invalid_initial_date = '2016-02-02'
    invalid_final_date = '2017-02-02'
    with pytest.raises(ValueError):
        get_transform_data.extract_time_periods_by_dates(test_data,
                                                         invalid_initial_date,
                                                         invalid_final_date)


def test_extract_time_periods_by_dates_invalid_test_data():
    test_data = pd.DataFrame(create_test_data())
    # this is invalid test data as there is no 'end_date' column
    invalid_test_data = test_data.drop('end_date', axis=1)
    initial_date = '2016-02-02'
    final_date = '2017-02-01'
    with pytest.raises(KeyError):
        get_transform_data.extract_time_periods_by_dates(invalid_test_data,
                                                         initial_date,
                                                         final_date)


def test_extract_time_periods_by_dates_with_non_unique_dates():
    test_data = pd.DataFrame(create_test_data())
    initial_date = '2019-03-01'
    final_date = '2019-07-31'
    expected_data = test_data
    expected_data.loc[:, 'date'] = pd.to_datetime(expected_data['end_date'])
    expected_data.loc[:, 'year'] = expected_data['date'].dt.year.astype('str')
    expected_data.loc[:, 'period'] = ['2019-03-01 to 2019-07-31',
                                      '2005-03-01 to 2005-07-31',
                                      '2000-03-01 to 2000-07-31',
                                      '2005-03-01 to 2005-07-31']
    expected_data = expected_data[expected_data.period != '2005-03-01 to 2005-07-31']
    expected_data.loc[:, 'mm-dd'] = expected_data['date'].dt.strftime("%m-%d")
    expected_data = expected_data.sort_values(by=list(expected_data.columns), axis=0,
                                              ascending=False)
    assert_frame_equal(
        get_transform_data.extract_time_periods_by_dates(test_data,
                                                         initial_date,
                                                         final_date),
        expected_data)


def test_stack_time_periods_by_ddmm_nonunique_dates():
    test_data_invalid = pd.DataFrame(create_test_data())
    test_data_invalid.loc[:, 'end_date'] = pd.to_datetime(test_data_invalid['end_date'])
    with pytest.raises(KeyError):
        get_transform_data.stack_time_periods_by_ddmm(test_data_invalid)


def test_stack_time_periods_by_ddmm_unique_dates():
    test_data_invalid = pd.DataFrame(create_test_data())
    test_data_invalid.loc[:, 'end_date'] = pd.to_datetime(test_data_invalid['end_date'])
    test_data_invalid.loc[:, 'date'] = pd.to_datetime(test_data_invalid['end_date'])
    test_data_invalid.loc[:, 'period'] = [
        '2019-01-01 to 2019-12-31',
        '2005-01-01 to 2005-12-31',
        '2000-01-01 to 2000-12-31',
        '2005-01-01 to 2005-12-31']
    test_data_invalid.loc[:, 'mm-dd'] = test_data_invalid['date'].dt.strftime("%m-%d")
    test_data = test_data_invalid.drop(test_data_invalid.index[-1])
    expected = pd.DataFrame({'mm-dd': ['03-01', '07-31', '08-28'],
                             '2000-01-01 to 2000-12-31': [2.39664378851418,
                                                          np.nan,
                                                          np.nan],
                             '2005-01-01 to 2005-12-31': [np.nan,
                                                          np.nan,
                                                          1.17640700229636],
                             '2019-01-01 to 2019-12-31': [np.nan,
                                                          0.13002748115958,
                                                          np.nan]}).set_index('mm-dd')
    expected.columns.name = 'period'
    assert_frame_equal(get_transform_data.stack_time_periods_by_ddmm(test_data), expected)


def test_dates_to_period_string():
    test_dates = ['2019-07-31T00:00:00.000Z',
                  '2019-08-28T00:00:00.000Z']
    test_dates = pd.to_datetime(test_dates)
    expected = '2019-07-31 to 2019-08-28'
    assert get_transform_data.dates_to_period_string(test_dates[0], test_dates[1]) == expected


def test_loop_initiation_dates_invalid_initial_greater_than_final():
    test_max_date = pd.to_datetime('2019-08-31T00:00:00.000Z')
    invalid_initial_date = '2019-07-31'
    invalid_final_date = '2019-06-30'
    with pytest.raises(ValueError):
        get_transform_data.loop_initiation_dates(
            test_max_date, invalid_initial_date, invalid_final_date)


def test_loop_initiation_dates_invalid_final_greater_than_year_from_initial():
    test_max_date = pd.to_datetime('2019-08-31T00:00:00.000Z')
    invalid_initial_date = '2018-06-30'
    invalid_final_date = '2019-07-31'
    with pytest.raises(ValueError):
        get_transform_data.loop_initiation_dates(
            test_max_date, invalid_initial_date, invalid_final_date)


def test_loop_initiation_dates_invalid_final_greater_than_max():
    test_max_date = pd.to_datetime('2019-08-31T00:00:00.000Z')
    invalid_initial_date = '2019-07-31'
    invalid_final_date = '2019-09-30'
    with pytest.raises(ValueError):
        get_transform_data.loop_initiation_dates(
            test_max_date, invalid_initial_date, invalid_final_date)


def test_loop_initiation_dates():
    test_max_date = pd.to_datetime('2019-08-31T00:00:00.000Z')
    invalid_initial_date = '2016-12-31'
    invalid_final_date = '2017-12-01'
    # Depending on the version of pandas, the data type of the datetime object
    # can vary between 'datetime64[ns, UTC]' and 'datetime64[ns]'
    utc_tz = False
    if test_max_date.tzinfo:
        utc_tz = True
    expected = {'initial_date': pd.to_datetime('2017-12-31', utc=utc_tz),
                'final_date': pd.to_datetime('2018-12-01', utc=utc_tz)}
    assert get_transform_data.loop_initiation_dates(
        test_max_date, invalid_initial_date, invalid_final_date) == expected
