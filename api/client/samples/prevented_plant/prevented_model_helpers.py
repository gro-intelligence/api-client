import datetime
import pickle
import numpy as np
import pandas as pd


def get_first_iso_week_date(year):
    datetime_first_january_output_year = datetime.datetime(year, 1, 1)
    iso_first_january_output_year = datetime.datetime(year, 1, 1).isocalendar()
    print(iso_first_january_output_year)
    output_start_datetime = datetime_first_january_output_year + datetime.timedelta(
        days=1 + (-iso_first_january_output_year[2] if
                  iso_first_january_output_year[0] == year
                  else (7 - iso_first_january_output_year[2])))

    return output_start_datetime


# Given weekly data of shape (num_weeks, some_data)
# returns an array of shape (num_years, 53, some_data) for first 53 weeks of data for each year
#
# Since some years are only 52 weeks, this may cause a week's data overlap with previous or next year.
#
# start_year should be year (absolute, i.e. 2011) you want output array indexing to start at
# num_years should be number of years from then you want outputted (don't exceed available data), (i.e. 2011 + 5 = 2016)
# epoch gives the date weekly_data starts being available (i.e. the starting monday of the first week)
def get_iso_weekly_yearly(weekly_data, data_epoch, output_start_year, num_years):
    assert (len(weekly_data.shape) == 2)
    # weekly data must start on a monday
    assert data_epoch.isocalendar()[2] == 1

    yearly_output = np.zeros((num_years, 53, weekly_data.shape[1]))

    for year_rel in range(num_years):
        year_abs = year_rel + output_start_year
        output_start_datetime = get_first_iso_week_date(year_abs)
        start_week_idx = (output_start_datetime - data_epoch).days // 7
        pre_pad = 0 if 0 - start_week_idx < 0 else 0 - start_week_idx
        post_pad = 0 if (start_week_idx + 53 - weekly_data.shape[0]) < 0 else (
                start_week_idx + 53 - weekly_data.shape[0])
        yearly_output[year_rel, :, :] = np.lib.pad(weekly_data[np.max([start_week_idx, 0]):start_week_idx + 53],
                                                   [(pre_pad, post_pad), (0, 0)],
                                                   'constant', constant_values=np.nan)

    return yearly_output


# stubs for saving/loading data
def s(data, name):
    with open(name + ".pickle", "wb") as handle:
        pickle.dump(data, handle)


def l(name):
    with open(name + ".pickle", "rb") as handle:
        return pickle.load(handle)

#TODO: Maybe move this into GroClient.
def region_combinator_data_series_dict(client, data_series_dict, regions, start_date=None, end_date=None):
    """
    Fetches and returns the data series definitions from data_series_dict for each region in regions within the date
    range of start_date to end_date (inclusive).
    :param client: a GroClient
    :param data_series_dict: A dict of name_of_data_series -> data_series_definition
    :param regions: A list of regions to get each data_series_definition for
    :param start_date: A datetime.datetime object
    :param end_date: A datetime.datetime object
    :return:
    """
    data = {}

    for name, data_series in data_series_dict.items():
        for region_id in regions:
            # add region
            data_series_tmp = data_series.copy()
            data_series_tmp["region_id"] = region_id

            # add date
            if start_date is not None:
                data_series_tmp["start_date"] = start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            if end_date is not None:
                data_series_tmp["end_date"] = end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

            client.add_single_data_series(data_series_tmp)

        data[name] = client.pop_df()

    return data

def impute(data_series, data_raw, start_date, end_date, region_ids):
    """
    Given a data series definition and a start/end date, impute the missing timeseries points (date->value pairs) using
    one of the available strategies.
    :param data_series: A dict of data_series_name->data_series_dict
    :param data_raw: The raw pandas frame of downloaded data
    :param start_date: A datetime.datetime object instance
    :param end_date: A datetime.datetime object instance
    :param region_ids: A list of region ids needed in case some are missing completely.
    :return:
    """
    for data_series_name, data_series_def in data_series.items():

        # TODO: support all the Gro's frequencies
        if data_series_def["frequency_id"] == 9:
            frequency = 'Y'
        elif data_series_def["frequency_id"] == 1:
            frequency = 'D'
        elif data_series_def["frequency_id"] == 2:
            frequency = 'W-SUN'
        else:
            raise Exception("no support for imputing this frequency")

        date_index = pd.date_range(start=start_date, end=end_date, freq=frequency)

        if 'region_id' not in data_raw[data_series_name]:
            data_raw[data_series_name]["region_id"] = ""
            data_raw[data_series_name]["end_date"] = ""
            data_raw[data_series_name]["value"] = ""

        data_raw[data_series_name] = data_raw[data_series_name].set_index(["region_id", "end_date"]).reindex(
            pd.MultiIndex.from_product([region_ids, date_index], names=['region_id', 'end_date']),
            fill_value=np.nan)

        if "impute" in data_series_def:
            #TODO: support more imputations
            if data_series_def["impute"] == "zero":
                data_raw[data_series_name].loc[data_raw[data_series_name].value.isna(), "value"] = 0.0

    return data_raw
