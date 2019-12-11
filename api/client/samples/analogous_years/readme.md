# Analogous Years
Users can find similarity based ranks between a time period and a list of time periods 
given by the time period ± 1 year, ± 2 years, ..., ± N years using `Analogous Years` application.
For rank computation a user must provide:

1. A time period determined by `initial_date` and `final_date` such that they are within a year of
each other.
2. Gro-entity(ies) and corresponding weights to compare the time periods.


## Methods of distance calculation
The analogy score between two different time periods can be measured in multiple ways. 
Here, the program can calculate ranks based on 2 primary approaches - 
1. Ranks based on differences between extracted features: 
    1. Distance between cumulative sums. 
    2. Distance between more features extracted from time series. 
    
    Note: For the purpose of this package we have used `tsfresh` package to 
    extract data from time series. 
2. Point wise differences: 
    1. Euclidean distance between stacked time periods. 
    2. Dynamic Time Warping distance between stacked time periods.
    
Finally, the program will return a composite rank by default based on the default 
(`cumulative`, `euclidean`, `ts-features`) methods or user specified methods.

## Usage:
### Example
If we want to know which period of time is closest to the time period 
between 4<sup>th</sup> April 2019 and 31<sup>st</sup> October 2019 
according to the composite ranking in terms of 
1. Rainfall (metric_id=2100031, item_id=2039, source_id=35, frequency_id=1) and;
2. Land Temperature (metric_id=2540047, item_id=3457, source_id=26, frequency_id=1) 

in the US Corn Belt (region_id=100000100) with equal weights given to rainfall and temperature
(by default), we will run the following code in the command line: 
`python run_analogous_years.py -m 2100031 2540047 -i 2039 3457 -r 100000100 -s 35 26 -f 1 1 
--initial_date 2019-04-01 --final_date 2019-10-31`

Note:
1. `frequency_id`: 1 gives us daily values. In absence of daily values, the application up-samples 
to daily frequency(ies).
2. `initial_date` and `final_date` must be strings in YYYY-MM-DD format.
3. **Warning**: The program is not meant to work when the selected Gro-item split into sub-items 
when fetching corresponding metric and region.

### Additional Options
1. Methods: Users have an option to choose from the following methods for distance computation
`cumulative, euclidean, ts-features, dtw`. The default methods for rank generation are 
`cumulative, euclidean, ts-features`. `dtw` method is intentionally left out of the default setting as
it may take up-to 40 minutes to run dynamic time warping algorithm on one `item-metric` tuple and
in many situations `dtw` ranks are highly correlated with the `euclidean` ranks.

2. All Ranks: Users have an option to generate separate individual ranks or composite rank
based on their methods list. By default only the composite rank will be generated.

3. Report: A correlation matrix as a csv file, together with a png file of pairwise scatter 
plots between ranks, for selected methods, are generated and saved in the same folder where the ranks 
in csv format is saved whenever users opt to generate multiple ranks.

4. Location: The `.csv` files containing the ranks (and possibly reports) are by default saved in your 
current directory unless a different location is stated.

5. Multivariate El Niño Southern Oscillation (ENSO) index can also be included in the 
rank computation, along with the weight that the user wants to give for the ENSO index. 
The weight of ENSO index is set to 1 by default.

A more detailed example with all the options may look like:
`python run_analogous_years.py --m 2100031 2540047 --item_id 2039 3457 --region_id 100000100
 --source_id 35 26 --frequency_id 1 1 --weights 1 1 --groapi_token <Enter GroAccessToken> 
 --initial_date 2016-02-02 --final_date 2016-02-10 --location <location of your directory here>
 --report False --methods cumulative euclidean ts-features dtw --ENSO --ENSO-weight 0.5 
 --all_ranks`