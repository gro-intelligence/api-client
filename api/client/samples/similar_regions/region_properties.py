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
            "num_features": 150,
            "longest_period_feature_period": 365,
            "weight": 0.7,
            "weight_slope": True
        }
    }
}
