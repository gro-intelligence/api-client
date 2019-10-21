### These are the data series we should use when doing a similar regions similarity computation.

region_properties = {
    "soil_moisture": {
        "selected_entities": {
            'metric_id': 15531082,
            'item_id': 7382,
            'frequency_id': 1,
            'source_id': 43
        },
        "properties": {
            "type": "timeseries_fourier",
            "num_features": 150,
            "longest_period_feature_period": 365,
            "weight": 0.7,
            "weight_slope": True
        }
    },
    "land_surface_temperature": {
        "selected_entities": {
            'metric_id': 2540047,
            'item_id': 3457,
            'frequency_id': 1,
            'source_id': 26
        },
        "properties": {
            "type": "timeseries_fourier",
            "num_features": 150,
            "longest_period_feature_period": 365,
            "weight": 0.7,
            "weight_slope": False
        }
    },
    "rainfall": {
        "selected_entities": {
            'metric_id': 2100031,
            'item_id': 2039,
            'frequency_id': 1,
            'source_id': 35
        },
        "properties": {
            "type": "timeseries_fourier",
            "num_features": 150,
            "longest_period_feature_period": 365,
            "weight": 0.7,
            "weight_slope": True
        }
    },
    "cation_exchange_30cm": {
        "selected_entities": {
            'metric_id': 15531092, 
            'item_id': 9131, 
            'source_id': 89, 
            'frequency_id': 15
        },
        "properties": {
            "type": "pit", 
            "num_features": 1,
            "weight": 0.7
        }
    },
    "ph_h2o_30cm": {
        "selected_entities": {
            'metric_id': 15760040,
            'item_id': 9164,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "num_features": 1,
            "weight": 0.7
        }
    },
    "sand_30cm": {
        "selected_entities": {
            'metric_id': 15750042,
            'item_id': 9185,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "num_features": 1,
            "weight": 0.7
        }
    },
    "silt_30cm": {
        "selected_entities": {
            'metric_id': 15750042,
            'item_id': 9178,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "num_features": 1,
            "weight": 0.7
        }
    },
    "clay_30cm": {
        "selected_entities": {
            'metric_id': 15750042,
            'item_id': 9138,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "num_features": 1,
            "weight": 0.7
        }
    },
    "organic_carbon_content_fine_earth_30cm": {
        "selected_entities": {
            'metric_id': 15531050,
            'item_id': 9157,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "num_features": 1,
            "weight": 0.7
        }
    },
    "soil_water_capacity_100cm": {
        "selected_entities": {
            'metric_id': 15531082,
            'item_id': 9194,
            'source_id': 89,
            'frequency_id': 15
        },
        "properties": {
            "type": "pit",
            "num_features": 1,
            "weight": 0.7
        }
    }
}
