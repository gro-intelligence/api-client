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
from scipy.fftpack import fft, ifft
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

    def get_num_features(self):
        return self.num_features

    def transform(self, time_series):
        """
        Return the coefficients of the data.
        :param timeseries:
        :return: The coefficients after the linear shift.
        """

        # FFT by default computes over the last axis.
        ranges = np.r_[0,self.start_idx:self.start_idx + self.num_features - 1].astype(int)
        assert(len(ranges) == self.num_features)
        fft_time_series = fft(time_series)[ranges]

        #Only interested in magnitude! not in phase in this case
        return np.abs(fft_time_series)

    def get_offset(self, timeseries_a, timeseries_b, period_in_samples):
        """
        :param timeseries_a: The reference discrete timeseries.
        :param timeseries_b: The discrete timeseries whose offset we want to find relative to timeseries_a.
        :param period_in_samples: Our prior assumption of what the period in the data is. E.g. for yearly cycles and
        sampling every day, this would be 365.
        :return: Returns the offset in number of samples.

        Please note: a and b must of the same number of samples.
        """

        # This supposedly computes the argmax_b phase(correlation(a,b))

        correlation_max_index = np.argmax(ifft(np.conj(fft(timeseries_a)) * fft(timeseries_b))[0:period_in_samples])
        return correlation_max_index


class Imputation(Transformer):
    """
    Fill in missing time using interpolation and backfill using np.interp :)
    self.features should be in temporal order
    """

    def transform(self, input):
        """
        Please note this operates in place on the array.
        :param input: input np array
        :param fill_method: boolean, whether to forward fill in addition to backfill
        :return: a imputed dataframe, a list of features
        """

        # interpolate data
        nans, x = self._nan_helper(input)
        input[nans] = np.interp(x(nans), x(~nans), input[~nans])

        return input

    # FROM https://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array
    def _nan_helper(self, y):
        """Helper to handle indices and logical indices of NaNs.

        Input:
            - y, 1d numpy array with possible NaNs
        Output:
            - nans, logical indices of NaNs
            - index, a function, with signature indices= index(logical_indices),
              to convert logical indices of NaNs to 'equivalent' indices
        Example:
            # linear interpolation of NaNs
            nans, x= nan_helper(y)
            y[nans]= np.interp(x(nans), x(~nans), y[~nans])
        """

        return np.isnan(y), lambda z: z.nonzero()[0]


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
#
# This was an attempt to make impute() faster. It failed to produce faster results. :( Feel free to improve.
#
# def _impute2(num_of_points, period_length_days, start_datetime, pulled_dataset):
#
#     start = time.time()
#
#     x_output = np.arange(0, period_length_days * num_of_points, period_length_days)
#
#     x_input = np.zeros(len(pulled_dataset))
#     y_input = np.zeros(len(pulled_dataset))
#
#     for idx, datapoint in enumerate(pulled_dataset):
#         delta = (datetime.strptime(datapoint["start_date"][0:10], "%Y-%m-%d").date() -
#                  start_datetime.date()).days
#         x_input[idx] = delta
#         y_input[idx] = datapoint["value"]
#
#     idxs = ~np.isnan(y_input)
#     x_input = x_input[idxs]
#     y_input = y_input[idxs]
#
#     num_valid_points = len(y_input)
#
#     y_output = np.interp(x_output, x_input, y_input)
#     coverage = float(num_valid_points) / num_of_points
#
#     end = time.time()
#     print("new", end - start)
#
#     return y_output, coverage


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

# TEST CASE
#
# no_of_points = 5
# period_length_days = 1
# start_datetime = datetime(2000, 3, 6)
# pulled_dataset = [{u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2000-03-12T00:00:00.000Z', u'input_unit_id': 2, u'frequency_name': u'weekly', u'value': 5.35641369409496, u'frequency_id': 2, u'available_date': u'2018-09-17T00:00:00.000Z', u'item_id': 2039, u'start_date': u'2000-03-06T00:00:00.000Z', u'metric_id': 2100031},
#                   {u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2000-03-19T00:00:00.000Z', u'input_unit_id': 2, u'frequency_name': u'weekly', u'value': 0.483880685965375, u'frequency_id': 2, u'available_date': u'2018-09-17T00:00:00.000Z', u'item_id': 2039, u'start_date': u'2000-03-07T00:00:00.000Z', u'metric_id': 2100031},
#                   {u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2000-03-26T00:00:00.000Z', u'input_unit_id': 2, u'frequency_name': u'weekly', u'value': 0.697971197718248, u'frequency_id': 2, u'available_date': u'2018-09-17T00:00:00.000Z', u'item_id': 2039, u'start_date': u'2000-03-08T00:00:00.000Z', u'metric_id': 2100031},
#                   {u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2000-04-02T00:00:00.000Z', u'input_unit_id': 2, u'frequency_name': u'weekly', u'value': 0.667947696387476, u'frequency_id': 2, u'available_date': u'2018-09-17T00:00:00.000Z', u'item_id': 2039, u'start_date': u'2000-03-09T00:00:00.000Z', u'metric_id': 2100031},
#                   {u'input_unit_scale': 1, u'region_id': 136969, u'end_date': u'2000-04-09T00:00:00.000Z', u'input_unit_id': 2, u'frequency_name': u'weekly', u'value': 0.748982814649028, u'frequency_id': 2, u'available_date': u'2018-09-17T00:00:00.000Z', u'item_id': 2039, u'start_date': u'2000-04-12T00:00:00.000Z', u'metric_id': 2100031}
#                   ]

# print _impute(no_of_points, period_length_days, start_datetime, pulled_dataset)
