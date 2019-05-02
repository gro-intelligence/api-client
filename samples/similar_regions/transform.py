"""
Numpy data transforms for API data.

This file contains a library of Transformer classes that expand sklearn transformation functionality
http://scikit-learn.org/stable/data_transforms.html, and necessary utilities.

Each transformer class has a fit method (generic in most cases) and a transform method.
The transform methods return a transformed numpy array, sometimes with a list of features,
if the transformed dataframe has different columns as the original one.

Eventually these could be incorporated into the API to reduce client side complexity for customers.
"""

import dateparser
import numpy as np
from sklearn.base import TransformerMixin
from scipy.fftpack import fft
from datetime import datetime, timedelta

class Transformer(TransformerMixin):
    """
    Base class of tranformers
    """
    def __init__(self):
        self.features = 0 #number of output features or desired number of features

    def transform(self, input):
        """
        Return a transformed version of the input. No guarantees are made about the format or dimensions of the output.
        :param input: a numpy array
        :return: a transformed version of the numpy array
        """
        pass

    def get_num_features(self):
        """
        Return the number of features this transformer will give for a given input size.
        :return: number of features in the returned data point.
        """
        pass


class FourierCoef(Transformer):

    def __init__(self, start_idx, num_features):

        """
        Initialize the fourier transform.
        :param features: Number of coefficients to output. Gives the n lowest frequency coefficients.
        pass -1 for all coefficients.
        """

        self.num_features = num_features
        self.start_idx = start_idx

    def transform(self, time_series):
        """
        Return the coefficients of the data.
        :param time_series: the timeseries values sampled at a regular interval with sampling frequency 1 we assume.
        :return: The coefficients after the linear shift.
        """

        # FFT by default computes over the last axis.
        ranges = np.r_[0,self.start_idx:self.start_idx + self.num_features - 1].astype(int)
        assert(len(ranges) == self.num_features)
        fft_time_series = fft(time_series)[ranges]

        #Only interested in magnitude! not in phase in this case
        return np.abs(fft_time_series)

# Other transformers
def post_process_timeseries(num_of_points, start_datetime, time_series, start_idx, num_features, period_length_days=1):
    dataset_imputed, coverage = _impute(num_of_points, period_length_days, start_datetime, time_series)

    # if imputing fails, we can't do fft either
    if dataset_imputed is None:
        return None, 0.0

    fourier = FourierCoef(start_idx, num_features)
    coefs = fourier.transform(dataset_imputed)

    return coefs, coverage

# temporary until filling nulls is enabled in prod api
def _fill_in_blank_days(num_of_points, start_datetime, pulled_dataset):
    dataset = np.zeros(num_of_points)

    ptr_idx_incomplete_list = 0

    their_start_date = dateparser.parse(pulled_dataset[0]["start_date"])

    date_delta = 0

    if their_start_date.date() < start_datetime.date():
        date_delta = (start_datetime.date() - their_start_date.date()).days

    ptr_idx_incomplete_list += date_delta

    for day_idx in range(0, num_of_points):
        curr_idx_date = (start_datetime + timedelta(days=day_idx)).isoformat() + ".000Z"

        if ptr_idx_incomplete_list >= len(pulled_dataset) or pulled_dataset[ptr_idx_incomplete_list][
            "start_date"] != curr_idx_date:
            # add null entry at this point for later imputation.
            dataset[day_idx] = float('NaN')
        else:
            dataset[day_idx] = pulled_dataset[ptr_idx_incomplete_list]["value"]
            ptr_idx_incomplete_list += 1

    return dataset

def _impute(num_of_points, period_length_days, start_datetime, pulled_dataset):
    x_output = np.arange(0, period_length_days * num_of_points, period_length_days)

    x_input = []
    y_input = []

    num_of_valid_points_pulled_dataset = 0

    for datapoint in pulled_dataset:
        if datapoint["value"] is not None:
            delta = (datetime.strptime(datapoint["start_date"][0:10], "%Y-%m-%d").date() - start_datetime.date()).days
            x_input.append(delta)
            y_input.append(datapoint["value"])
            num_of_valid_points_pulled_dataset += 1

    # num data points to interpolate
    if len(x_input) == 0:
        return None, 0.0

    y_output = np.interp(x_output, x_input, y_input)
    coverage = float(num_of_valid_points_pulled_dataset) / num_of_points

    return y_output, coverage

