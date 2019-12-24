"""
This library contains utilities for
1. retrieving data series from gro api
2. extracting and transforming relevant part of the data series
"""

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd


def get_data(client, metric_id, item_id, region_id, source_id, frequency_id, start_date):
    """
    :param client: GroClient
    :param metric_id: Gro-metric
    :param item_id: Gro-item associated to the metric
    :param region_id: Gro-region
    :param source_id: Gro-source
    :param frequency_id: Gro-frequency
    :param start_date: start-date of the Gro data series
    :return: A dataframe with an 'end_date' and 'value' column
    """
    data = client.get_data_points(**{'metric_id': metric_id,
                                     'item_id': item_id,
                                     'region_id': region_id,
                                     'source_id': source_id,
                                     'frequency_id': frequency_id,
                                     'start_date': start_date})
    data = pd.DataFrame(data)
    data = data[['end_date', 'value']]
    if data['end_date'].iloc[0] > start_date:
        new_value = data['value'].iloc[0]
        new_row = pd.DataFrame({'end_date': [start_date], 'value': [new_value]})
        data = pd.concat([new_row, data[:]]).reset_index(drop=True)
    return ffill_bfill_nulls(data)


def ffill_bfill_nulls(dataframe):
    dataframe.fillna(method='ffill', inplace=True)
    dataframe.fillna(method='bfill', inplace=True)
    dataframe.reset_index()
    return dataframe


def combine_subregions(df_sub_regions):
    """
    Consolidate values of sub_regions within the data frame
    by grouping together same date entries followed by re-sampling (up-sampling)
    the data to daily frequency
    :param df_sub_regions: A dataframe with subregions
    :return: A dataframe with summed 'value' across regions for each date
    """
    if df_sub_regions['end_date'].is_unique:
        df_consolidated_regions = df_sub_regions
        df_consolidated_regions.index = df_sub_regions['end_date']
    else:
        df_consolidated_regions = df_sub_regions.groupby(['end_date'])[['value']].sum()
    df_consolidated_regions.index = pd.to_datetime(df_consolidated_regions.index)
    df_consolidated_regions = df_consolidated_regions.resample('D').pad()
    df_consolidated_regions['end_date'] = df_consolidated_regions.index
    return df_consolidated_regions


def loop_start_dates(max_date, initial_date, final_date):
    """
    :param max_date: datetime
    :param initial_date: string 'YYYY-MM-DD'
    :param final_date: string 'YYYY-MM-DD'
    :return: dictionary with datetime objects as values
    """
    tz_info = max_date.tzinfo
    initial_date = parse(initial_date)
    initial_date = initial_date.replace(tzinfo=tz_info)
    final_date = parse(final_date)
    final_date = final_date.replace(tzinfo=tz_info)
    if initial_date >= final_date:
        raise ValueError('Initial date {} is not prior to final date {}. '
                         'Change and try again'.format(initial_date, final_date))
    if final_date >= initial_date + relativedelta(years=+1):
        raise ValueError('Initial date {} not within a year of final date {} '
                         'Change and try again'.format(initial_date, final_date))
    if final_date > max_date:
        raise ValueError('Data unavailable after {}'.format(max_date))
    loop_final_date = final_date
    loop_initial_date = initial_date
    while loop_final_date + relativedelta(years=+1) < max_date:
        loop_final_date = loop_final_date + relativedelta(years=+1)
        loop_initial_date = loop_initial_date + relativedelta(years=+1)
    return {'initial_date': loop_initial_date, 'final_date': loop_final_date}


def dates_to_period_string(date_1, date_2):
    """
    :param date_1: datetime object
    :param date_2: datetime object
    :return: string
    """
    return date_1.strftime("%Y-%m-%d") + ' to ' + date_2.strftime("%Y-%m-%d")


def extract_time_periods_by_dates(dataframe, initial_date, final_date):
    """
    Extract a dataframe from an input dataframe of daily values using the
    MM-DD for different years
    :param dataframe: A pandas dataframe
    :param final_date: 'YYYY-MM-DD'
    :param initial_date: 'YYYY-MM-DD'
    :return: A pandas dataframe
    """
    dataframe['date'] = pd.to_datetime(dataframe['end_date'])
    max_date = dataframe['date'].max()
    min_date = dataframe['date'].min()
    loop_final_date = loop_start_dates(
        max_date, initial_date, final_date)['final_date']
    loop_initial_date = loop_start_dates(
        max_date, initial_date, final_date)['initial_date']
    extracted_df_list = []
    while loop_initial_date >= min_date:
        temp_df = dataframe[(dataframe['date'] >= loop_initial_date) &
                            (dataframe['date'] <= loop_final_date)]
        temp_df['period'] = dates_to_period_string(loop_initial_date, loop_final_date)
        loop_initial_date = loop_initial_date + relativedelta(years=-1)
        loop_final_date = loop_final_date + relativedelta(years=-1)
        extracted_df_list.append(temp_df)
    extracted_df = pd.concat(extracted_df_list)
    extracted_df['mm-dd'] = extracted_df['date'].dt.strftime("%m-%d")
    return extracted_df


def stack_time_periods_by_ddmm(dataframe):
    """
    A pivot table with 'period' as columns and 'mm-dd' as rows.
    :param dataframe: A pandas dataframe
    :return: A pandas dataframe
    """
    segmented_periods = pd.pivot_table(dataframe, values='value',
                                       index=['mm-dd'], columns=['period'])
    ffill_bfill_nulls(segmented_periods)
    segmented_periods = segmented_periods[segmented_periods.index != '02-29']
    return segmented_periods
