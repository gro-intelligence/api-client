"""Sample API requests for various Gro data series.

This is a very simple collection of Gro API data pulls, designed to
show a sample of the various types of information available and
some syntactical hints for new API users.

The various entity IDs are all aliased to global variable names
in the first section so that the queries themselves read more
intuitively.

After this script runs, the 12 series will be combined in a single data frame
and a preview is printed to the console.

They hold different data as per the comments above each query.

1.International Cocoa Organization (ICCO)
2.International Coffee Organization (ICO)
3.Brazilian Sugarcane Industry Association (UNICA)
4.Center for Advanced Studies on Applied Economics (CEPEA)
5.GIMMS MODIS NDVI
6.MOD11 Land Surface Temperature
7.FEWS NET Daily Evapotranspiration
8.FEWS NET Monthly Actual Evapotranspiration
9.GlobCover Land Cover
10.Soil Moisture and Ocean Salinity Mission (SMOS) Soil Moisture
11.National Farmers Information System (NAFIS) Kenya
12.Gro Yield Model
"""

import os
from groclient import GroClient

# GRO GLOBAL VARIABLES
API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

# METRIC_ID GLOBALS
YIELD = 170037
HARV_AREA = 570001
TEMPERATURE = 2540047
VEG_ANOMALIES = 431132
ETA_PCT = 15852239
PRODUCER_PRICE = 2290065
GRINDINGS = 5380032
COMPOSITE_PRICES = 2270065
ET_VALUE = 4660031
LAND_COVER = 15852316
SOIL_AVAIL = 15531082
WHOLESALE_PX = 2310065

# ITEM_ID GLOBALS
NDVI_DIFF_10YR_MEAN = 321
ETA_PCT_MEDIAN = 4395
LST = 3457
SOIL_MOISTURE = 7382
SOYBEANS = 270
COFFEE = 225
COCOA = 211
COTTON_LINT = 152
SUGARCANE = 538
CASSAVA = 237
BRAZ_ARABICA = 5157
POTENT_ETA = 5072
RAINFED_CROPLAND = 4090
MOISTURE = 7382
AVOCADOS = 127


# REGION_ID GLOBALS
WORLD = 0
BRAZIL = 1029
KENYA_NAIROBI = 13474
UNITED_STATES = 1215
SAO_PAULO = 10408
MATO_GROSSO = 10417

# SOURCE_ID GLOBALS
ICCO = 13
ICO = 9
UNICA = 47
CEPEA = 74
GIMMS_MODIS = 3
LST_SRC = 26
FEWSNET1D = 44
FEWSNET1M = 18
GLOBCOVER = 53
SMOS = 43
NAFIS = 12
GROYM = 32

# FREQUENCY_ID GLOBALS
DAILY = 1
WEEKLY = 2
EIGHTDAY = 3
SIXTEENDAY = 5
MONTHLY = 6
QUARTERLY = 7
ANNUAL = 9
POINT_IN_TIME = 15

# Set up gro API

client = GroClient(API_HOST, ACCESS_TOKEN)

# BRAZIL COCOA GRINDINGS FROM ICCO (1)
client.add_single_data_series({'metric_id': GRINDINGS,
                               'item_id': COCOA,
                               'region_id': BRAZIL,
                               'frequency_id': ANNUAL,
                               'source_id': ICCO})

# BRAZIL ARABICA COMPOSITE PRICES (2)
client.add_single_data_series({'metric_id': COMPOSITE_PRICES,
                               'item_id': BRAZ_ARABICA,
                               'region_id': WORLD,
                               'frequency_id': DAILY,
                               'source_id': ICO})

# SAO PAULO SUGAR AREA FROM UNICA (3)
client.add_single_data_series({'metric_id': HARV_AREA,
                               'item_id': SUGARCANE,
                               'region_id': SAO_PAULO,
                               'frequency_id': ANNUAL,
                               'source_id': UNICA})

# SAO PAULO CASSAVA PRICES FROM CEPEA (4)
client.add_single_data_series({'metric_id': PRODUCER_PRICE,
                               'item_id': CASSAVA,
                               'region_id': SAO_PAULO,
                               'frequency_id': WEEKLY,
                               'source_id': CEPEA})

# NDVI ANOMALY SAO_PAULO (5)
client.add_single_data_series({'metric_id': VEG_ANOMALIES,
                               'item_id': NDVI_DIFF_10YR_MEAN,
                               'region_id': SAO_PAULO,
                               'frequency_id': SIXTEENDAY,
                               'source_id': GIMMS_MODIS})

# LAND SURFACE TEMPERATURE SAO PAULO (6)
client.add_single_data_series({'metric_id': TEMPERATURE,
                               'item_id': LST,
                               'region_id': SAO_PAULO,
                               'frequency_id': DAILY,
                               'source_id': LST_SRC})

# DAILY EVAPOTRANSPIRATION SAO PAULO (7)
client.add_single_data_series({'metric_id': ET_VALUE,
                               'item_id': POTENT_ETA,
                               'region_id': SAO_PAULO,
                               'frequency_id': DAILY,
                               'source_id': FEWSNET1D})

# MONTHLY EVAPOTRANSPIRATION ANOMALY SAO_PAULO (8)
client.add_single_data_series({'metric_id': ETA_PCT,
                               'item_id': ETA_PCT_MEDIAN,
                               'region_id': SAO_PAULO,
                               'frequency_id': MONTHLY,
                               'source_id': FEWSNET1M})

# GLOBCOVER RAINFED CROPLAND SAO_PAULO (9)
client.add_single_data_series({'metric_id': LAND_COVER,
                               'item_id': RAINFED_CROPLAND,
                               'region_id': SAO_PAULO,
                               'frequency_id': POINT_IN_TIME,
                               'source_id': GLOBCOVER})

# SOIL MOISTURE SAO_PAULO (10)
client.add_single_data_series({'metric_id': SOIL_AVAIL,
                               'item_id': MOISTURE,
                               'region_id': SAO_PAULO,
                               'frequency_id': DAILY,
                               'source_id': SMOS})

# NAFIS KENYA AVOCADO PRICE (11)
client.add_single_data_series({'metric_id': WHOLESALE_PX,
                               'item_id': AVOCADOS,
                               'region_id': KENYA_NAIROBI,
                               'frequency_id': DAILY,
                               'source_id': NAFIS})

# GRO US SOYBEAN YIELD (12)
client.add_single_data_series({'metric_id': YIELD,
                               'item_id': SOYBEANS,
                               'region_id': UNITED_STATES,
                               'frequency_id': ANNUAL,
                               'source_id': GROYM})

print(client.get_df())
