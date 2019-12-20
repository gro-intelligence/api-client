# Analogous Years
The Analogous Years application enables users to compare events from a set period of time, 
to those of the same date range in other years. The application will compute ranks of similarity 
between the specified period, and the same period from previous or future years. Multiple different 
inputs can be used in determining the ranks, but to compute these ranks, a user must provide::

1. A time period determined by `initial_date` and `final_date` such that they are within a year of
each other.
2. Gro-entity(ies) and corresponding weights to compare the time periods.

## Working Example Using Python
To get started with `Analogous Years`, users have to install `Gro API Client`
as detailed [here](https://developers.gro-intelligence.com/installation.html). 

If the user wants to know which period of time is is most similar to the time period 
between 1<sup>st</sup> January 2019 and 31<sup>st</sup> October 2019 with respect to the
following Gro-entities -
1. Rainfall, TRMM (metric_id=2100031, item_id=2039, source_id=35, frequency_id=1)
2. Land Temperature, MODIS (metric_id=2540047, item_id=3457, source_id=26, frequency_id=1)
3. Soil moisture, SMOS (metric_id=15531082, item_id=7382, source_id=43, frequency_id=1)

in the US Corn Belt (region_id=100000100) with equal weights given (by default) to 
rainfall, temperature and soil moisture, users can use the following code in their python 
IDE. The following blocks of code assumes that you have saved the Gro API authentication 
token as an environment variable as `GROAPI_TOKEN`. 

```python
# Set up environment for accessing Gro API and the access token
import os
from api.client.gro_client import GroClient
API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']
client = GroClient(API_HOST, ACCESS_TOKEN)

# Import Analogous Years
from api.client.samples.analogous_years import run_analogous_years
from api.client.samples.analogous_years.lib import final_ranks_computation, 
    get_transform_data

# Input (Gro Entities)

# Rainfall (modeled) - Precipitation Quantity - 
# US Corn Belt States (NASA TRMM 3B42RT)
entity_1 = {'metric_id': 2100031, 
             'item_id': 2039, 
             'region_id': 100000100, 
             'partner_region_id': 0, 
             'source_id': 35, 
             'frequency_id': 1, 
             'unit_id': 2}
# Land temperature (daytime, modeled) - Temperature - 
# US Corn Belt States (NASA MODIS MOD11 LST)
entity_2 = {'metric_id': 2540047, 
             'item_id': 3457, 
             'region_id': 100000100, 
             'partner_region_id': 0, 
             'source_id': 26, 
             'frequency_id': 1,
             'unit_id': 36}
# Soil moisture - Availability in soil (volume/volume) - 
# US Corn Belt States (ESA SMOS CLF33D)
entity_3 = {'metric_id': 15531082, 
            'item_id': 7382, 
            'region_id': 100000100, 
            'partner_region_id': 0, 
            'source_id': 43, 
            'frequency_id': 1}

# Combine entities to make a list of entities
entities = [entity_1, entity_2, entity_3]

# Input (Date Range)
initial_date = '2019-01-01'
final_date = '2019-10-31'

# Output (Ranks)
file_name, result = 
        final_ranks_computation.combined_items_final_ranks(
        client, entities, initial_date, final_date)
print(result)
```
### Working Example Using Shell
To access ranks for the same inputs using command line users may run the following code 
in the command line from the `/api-client/api/client/samples/analogous_years` directory: 
```shell script
analogous_years $ python run_analogous_years.py -m 2100031 2540047 15531082 -i 2039 3457 7382 -r 100000100 -s 35 26 43 -f 1 1 1 --initial_date 2019-01-01 --final_date 2019-10-31
```
The ranks will be saved as a csv file in the same directory.

## Appendix
### Methods of rank calculation
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



Note:
1. `frequency_id`: 1 gives us daily values. In absence of daily values, 
the application up-samples to daily frequency(ies).
2. `initial_date` and `final_date` must be strings in YYYY-MM-DD format.
3. **Warning**: The program is not meant to work when the selected Gro-item 
split into sub-items when fetching corresponding metric and region.

### Additional Options
1. Methods: Users have an option to choose from the following methods for distance 
computation`cumulative, euclidean, ts-features, dtw`. The default methods for rank 
generation are `cumulative, euclidean, ts-features`. `dtw` method is intentionally 
left out of the default setting as it may take up-to 40 minutes to run dynamic time warping 
algorithm on one `item-metric` tuple and in many situations `dtw` ranks are highly 
correlated with the `euclidean` ranks.

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

6. Start Date: Users have an option to include time periods after a specified date. By 
default the earliest date from which data is available for all entities will be used to 
compute ranks

## Detailed Example
A more detailed example with all the options in python may look like:
```python
# Output (Ranks)
file_name, result = final_ranks_computation.combined_items_final_ranks(
        client, entities, initial_date, final_date, 
        methods_list=[`cumulative, euclidean, ts-features, dtw`], 
        all_ranks=True, weights=[0.2, 0.3, 0.4], enso=True,
        enso_weight=0.1, provided_start_date='2015-01-01')
print(result)
logger = client.get_logger()
store_result = final_ranks_computation.save_to_csv(
        (file_name, result), logger, all_ranks=True, report=True, 
        output_dir=<output directory location>)
```
The same example in shell may look like
```shell script
analogous_years $ python run_analogous_years.py -m 2100031 2540047 15531082 -i 2039 3457 7382 -r 100000100 -s 35 26 43 -f 1 1 1 --weights 0.2 0.3 0.4 --initial_date 2019-01-01 --final_date 2019-10-31 --groapi_token <Enter GroAccessToken> --output_dir <output director location> --report True --methods cumulative euclidean ts-features dtw --ENSO --ENSO-weight 0.5 --all_ranks --start_date 2015-01-01
```