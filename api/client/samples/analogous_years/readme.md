# Analogous Years

The Analogous Years application enables users to compare events from a set period of time, to those of the same date range in other years. The application will compute ranks of similarity between the specified period, and the same period from previous or future years. Multiple different inputs can be used in determining the ranks, but to compute these ranks, a user must provide:

1. One or multiple Gro data series.
2. A time period determined by `initial_date` and `final_date` such that they are within a year of
each other.

## 1. Working Example In Shell Using Python

To get started with `Analogous Years`, users have to install `Gro API Client` as detailed [here](https://developers.gro-intelligence.com/installation.html) as well as the additional dependencies listed in the [requirements.txt](./requirements.txt) of this project. Assuming that the user has saved the Gro API authentication token as an environment variable named `GROAPI_TOKEN`, `analogous_years` can be accessed using shell.

Multiple different inputs can be used in determining the ranks (refer to the appendix), but to compute these ranks, a user must provide:

### 1.1 Gro Data Series

Single or multiple Gro Data Series defined by `metric_id`, `item_id`, `source_id`, `frequency_id` for a particular region given by a `region_id`.

### 1.2 Time Period

A time period determined by an `initial_date` and a `final_date`. The two dates must be within 1 year of each other and in the `YYYY-MM-DD` format.

### Example

As an example, if the user wants to know which period of time is most similar to the time period between 1<sup>st</sup> January 2019 and 31<sup>st</sup> October 2019 in the [US Corn Belt States (region_id=100000100)](https://app.gro-intelligence.com/dictionary/regions/100000100) with respect to the
following [Gro Data Series](https://app.gro-intelligence.com/displays/za9MlQYRM):

1. Rainfall, TRMM ([metric_id=2100031](https://app.gro-intelligence.com/dictionary/metrics/2100031), [item_id=2039](https://app.gro-intelligence.com/dictionary/items/2039), [source_id=35](https://app.gro-intelligence.com/dictionary/sources/35), frequency_id=1)
2. Land Temperature, MODIS ([metric_id=2540047](https://app.gro-intelligence.com/dictionary/metrics/2540047), [item_id=3457](https://app.gro-intelligence.com/dictionary/items/3457), [source_id=26](https://app.gro-intelligence.com/dictionary/sources/26), frequency_id=1)
3. Soil moisture, SMOS ([metric_id=15531082](https://app.gro-intelligence.com/dictionary/metrics/15531082), [item_id=7382](https://app.gro-intelligence.com/dictionary/items/7382), [source_id=43](https://app.gro-intelligence.com/dictionary/sources/43), frequency_id=1)

Then, from the `api-client/api/client/samples/analogous_years` directory they may run the following command:

```sh
$ python run_analogous_years.py -m 2100031 2540047 15531082 -i 2039 3457 7382 -r 100000100 -s 35 26 43 -f 1 1 1 --initial_date 2019-01-01 --final_date 2019-10-31
```

The ranks will be saved as a csv file in a subdirectory in the same directory.

## 2. Appendix

### 2.1 Methods of rank calculation

The analogy score between two different time periods can be measured in multiple ways. Here, the program can calculate ranks based on 2 primary approaches:

1. Ranks based on differences between extracted features:
    1. Distance between cumulative sums.
    2. Distance between more features extracted from time series.
    Note: For the purpose of this package we have used `tsfresh` package to extract data from time series.
2. Point wise differences:
    1. Euclidean distance between stacked time periods.
    2. Dynamic Time Warping distance between stacked time periods.

Finally, the program will return an ensemble rank by default based on the default (`cumulative`, `euclidean`, `ts-features`) methods or user specified methods.

Note:

1. `frequency_id: 1` gives us daily values. In absence of daily values, the application up-samples to daily frequency(ies).
2. `initial_date` and `final_date` must be strings in YYYY-MM-DD format.
3. **Warning**: The program is not meant to work when the selected Gro-item split into sub-items when fetching corresponding metric and region.

### 2.2 Additional Options

1. Methods: Users have an option to choose from the following methods for distance computation`cumulative, euclidean, ts-features, dtw`. The default methods for rank generation are `cumulative, euclidean, ts-features`. `dtw` method is intentionally left out of the default setting as it is computationally expensive to run dynamic time warping algorithm on one `item-metric` tuple and in many situations `dtw` ranks are highly correlated with the `euclidean` ranks.
2. All Ranks: Users have an option to output multiple individual ranks or an ensemble rank based on their methods list. By default only the ensemble rank will be generated.
3. Multivariate El Niño Southern Oscillation (ENSO) index can also be included in the rank computation, along with the weight that the user wants to give for the ENSO index. The weight of ENSO index is set to 1 by default.
4. Start Date: Users have an option to exclude time periods before a specified date. By default the earliest date from which data is available for all entities will be used to compute ranks.

### 2.3 Report

1. Report: A correlation matrix as a csv file together with a png file of pairwise scatter plots between ranks, for the selected methods, can be generated and saved in the same folder where the ranks in csv format is saved whenever users opt to generate multiple ranks.
2. Location: Users have an option to choose a directory where results and reports can be saved. By default they will be saved in a subdirectory under the present working directory.

## 3. Detailed Example

A more detailed example with all the options in shell may look like

```sh
$ python run_analogous_years.py -m 2100031 2540047 15531082 -i 2039 3457 7382 -r 100000100 -s 35 26 43 -f 1 1 1 --weights 0.2 0.3 0.4 --initial_date 2019-01-01 --final_date 2019-10-31 --groapi_token <Enter GroAccessToken> --output_dir <output director location> --report True --methods cumulative euclidean ts-features dtw --ENSO --ENSO-weight 0.5 --all_ranks --start_date 2015-01-01
```

## 4. Working Example In Python

If users want to incorporate the package in there own python script, then users may follow the associated [notebook](./get_started_with_analogous_years.ipynb).
