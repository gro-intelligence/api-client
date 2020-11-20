### This file describes the metric to be used when doing region similarity computation.

# metric_properties mostly gives information needed for data download.
# In it, "api_data" are API parameters (metric_id, item_id, etc.) needed to uniquely identify data for Gro API.
#
# For time series, it is recommended to provide start_date set to the start of calendar year (XXXX-01-01)
# and end_date set to the end of year (YYYY-12-31) fully within data availability for particular item.
# Otherwise data might become biased towards particular part of the year.
# This is especially important when searching is expected to include regions in both Northern and Southern hemispheres.
#
# "properties" are:
#    type (required) : can be timeseries or pit (point-in-time)
#    norm (optional) : normalization constant. Data is DIVIDED by it. If not given, each value will be divided by this item's data std.
# It is recommended to provide normalization constants, ideally the std of corresponding item over the entire world
# or other region of primary interest. Otherwise data will be re-normalized differently for runs with different search regions,
# which might result in counter-intuitive reordering of similar regions.

# metric_instance is a item:weight dictionary specifying the particular collection of items and their weights
# to be used in contructig similar_region object. It should be a subset of metric_properties
# Each data point belonging to an item will be MULTIPLIED by sqrt of the weight

# Full calculation before applying the distance measure is therefore sqrt(weight)*data/norm.
# Note that taking sqrt of user-provided weights here assumes user wants something like
# dist^2 = \sum w_user_i*(x_i - y_i)^2 (note non-squared w_user_i here)
# which is usual specification in weighted L2 norm (least squares)


# Just an example. This is intended to be define in the user code
# Here soil properties are down-weighted so that
# the seven of them together have the same weight as one of the time series

metric_weights = {
    'soil_moisture': 1.0,
    'rainfall': 1.0,
    'land_surface_temperature': 1.0,
    'cation_exchange_30cm': 1.0/7,
    'ph_h2o_30cm': 1.0/7,
    'sand_30cm': 1.0/7,
    'silt_30cm': 1.0/7,
    'clay_30cm': 1.0/7,
    'organic_carbon_content_fine_earth_30cm': 1.0/7,
    'soil_water_capacity_100cm': 1.0/7
}

metric_properties = {
    "soil_moisture": {
        "api_data": {
            'metric_id': 15531082,
            'item_id': 7382,
            'frequency_id': 1,
            'start_date': '2010-01-01',
            'end_date': '2019-12-31',
            'source_id': 43
        },
        "properties": {
            "type": "timeseries",
            "norm": 0.10392425811824436 #world
            #"norm": 0.08935901636262628 #US
        }
    },
    "land_surface_temperature": {
        "api_data": {
            'metric_id': 2540047,
            'item_id': 3457,
            'frequency_id': 1,
            'start_date': '2001-01-01',
            'end_date': '2019-12-31',
            'source_id': 26
        },
        "properties": {
            "type": "timeseries",
            "norm": 10.522910434012786 #world
            #"norm": 11.554893163498669 #US
        }
    },
    "rainfall": {
        "api_data": {
            'metric_id': 2100031,
            'item_id': 2039,
            'frequency_id': 1,
            'start_date': '2001-01-01',
            'end_date': '2019-12-31',
            'source_id': 126 # GPM (35 is TRMM)
        },
        "properties": {
            "type": "timeseries",
            "norm": 3.251061054865164 #world
            #"norm": 2.00482856056347 #US
        }
    },
    "cation_exchange_30cm": {
        "api_data": {
            'metric_id': 15531092, 
            'item_id': 9131, 
            'source_id': 89, 
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 7.419505220035897 #world
            #"norm": 6.1499586913258355 #US
        }
    },
    "ph_h2o_30cm": {
        "api_data": {
            'metric_id': 15760040,
            'item_id': 9164,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 0.8919784420863497 #world
            #"norm": 0.8745867514473281 #US
        }
    },
    "sand_30cm": {
        "api_data": {
            'metric_id': 15750042,
            'item_id': 9185,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 12.81336485840269 #world
            #"norm": 15.2055807988559 #US
        }
    },
    "silt_30cm": {
        "api_data": {
            'metric_id': 15750042,
            'item_id': 9178,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 10.336593832774641 #world
            #"norm": 11.954774036762778 #US
        }
    },
    "clay_30cm": {
        "api_data": {
            'metric_id': 15750042,
            'item_id': 9138,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 8.910422270950244 #world
            #"norm": 6.608225017877747 #US
        }
    },
    "organic_carbon_content_fine_earth_30cm": {
        "api_data": {
            'metric_id': 15531050,
            'item_id': 9157,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 18.61997475158847 #world
            #"norm": 11.22620194126804 #US
        }
    },
    "soil_water_capacity_100cm": {
        "api_data": {
            'metric_id': 15531082,
            'item_id': 9194,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "norm": 4.079056361486918 #world
            #"norm": 3.4756080460089667 #US
        }
    }
}
