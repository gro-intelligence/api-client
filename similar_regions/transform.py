"""
Numpy data transforms for API data.

This file contains a library of Transformer classes that expand sklearn transformation functionality
http://scikit-learn.org/stable/data_transforms.html, and necessary utilities.

Each transformer class has a fit method (generic in most cases) and a transform method.
The transform methods return a transformed numpy array, sometimes with a list of features,
if the transformed dataframe has different columns as the original one.

Eventually these could be incorporated into the API to reduce client side complexity for customers.
"""
from itertools import groupby
import heapq

import dateparser
import numpy as np
from sklearn.base import TransformerMixin
from scipy.fftpack import fft, ifft
from datetime import date, time, datetime, timedelta

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


class FourierCoef(Transformer):

    def __init__(self, features=100):

        """
        Initialize the fourier transform.
        :param features: Number of coefficients to output. Gives the n lowest frequency coefficients.
        pass -1 for all coefficients.
        """
        self.features = features
        pass

    def transform(self, time_series):
        """
        Return the coefficients of the data.
        :param timeseries:
        :param phase_dependant: should the output transformation be dependant of the phase of that signal.
        :return: The coefficients after the linear shift.
        """

        # FFT by default computes over the last axis.
        fft_time_series = fft(time_series)[0:self.features] if self.features != -1 else fft(time_series)

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

        # This supposedly computes the argmax_bphase(correlation(a,b))

        correlation_max_index = np.argmax(ifft(np.conj(fft(timeseries_a)) * fft(timeseries_b))[0:period_in_samples])
        return correlation_max_index




class Imputation(Transformer):
    """
    Fill in missing time using interpolation and backfill
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

def _post_process_timeseries(no_of_points, start_datetime, time_series):

    pulled_dataset = time_series

    dataset = _fill_in_blank_days(no_of_points, start_datetime, pulled_dataset)

    try:
        imputer = Imputation()
        dataset_imputed = imputer.transform(dataset)
    except Exception as e:
        print(len(pulled_dataset))
        print(start_datetime)
        print(no_of_points)
        print(e)

    fourier = FourierCoef()
    coefs = fourier.transform(dataset_imputed)

    return coefs

def _fill_in_blank_days(no_of_points, start_datetime, pulled_dataset):
    dataset = np.zeros(no_of_points)

    ptr_idx_incomplete_list = 0

    their_start_date = dateparser.parse(pulled_dataset[0]["start_date"])

    date_delta = 0

    if their_start_date.date() < start_datetime.date():
        date_delta = (start_datetime.date() - their_start_date.date()).days

    ptr_idx_incomplete_list += date_delta

    for day_idx in range(0, no_of_points):
        curr_idx_date = (start_datetime + timedelta(days=day_idx)).isoformat() + ".000Z"

        if ptr_idx_incomplete_list >= len(pulled_dataset) or pulled_dataset[ptr_idx_incomplete_list][
            "start_date"] != curr_idx_date:
            # add null entry at this point for later imputation.
            dataset[day_idx] = float('NaN')
        else:
            dataset[day_idx] = pulled_dataset[ptr_idx_incomplete_list]["value"]
            ptr_idx_incomplete_list += 1

    return dataset
