import datetime
import numpy as np

from prevented_model_helpers import get_iso_weekly_yearly, get_first_iso_week_date


def test_get_first_iso_week_date():
    # same year
    assert get_first_iso_week_date(2010) == datetime.datetime(2010, 01, 04)
    assert get_first_iso_week_date(1910) == datetime.datetime(1910, 01, 03)

    # previous year
    assert get_first_iso_week_date(1914) == datetime.datetime(1913, 12, 29)
    assert get_first_iso_week_date(1952) == datetime.datetime(1951, 12, 31)

    # jan 1st
    assert get_first_iso_week_date(1912) == datetime.datetime(1912, 01, 01)


def test_get_iso_weekly_yearly():
    # 500 weeks, 5 points each week
    weekly_data = np.random.rand(500, 5)
    data_epoch = datetime.datetime(1912, 1, 8)

    output = get_iso_weekly_yearly(weekly_data, data_epoch, 1912, 10)

    # check offset starting week
    assert np.all(output[0, 1, :] == weekly_data[0, :])
    # check nan padding start
    assert np.all(np.isnan(output[0, 0, :]))
    # check nan padding end
    assert np.all(np.isnan(output[9, 52, :]))
    # check some random week
    assert np.all(output[1, 2, :] == weekly_data[53, :])

#TODO: write tests for remaining helper functions.