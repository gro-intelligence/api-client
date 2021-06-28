# TODO: move mocks into conftest.py

mock_entities = {
    "metrics": {
        860032: {
            "id": 860032,
            "name": "Production Quantity",
            "contains": [],
            "belongsTo": [119],
        },
        860033: {
            "id": 3341078,
            "name": "Production Value",
            "contains": [],
            "belongsTo": [119],
        }
    },
    "items": {
        274: {
            "id": 274,
            "name": "Corn",
            "contains": [],
            "belongsTo": []
        }
    },
    "regions": {
        0: {"id": 0, "level": 1, "name": "World", "contains": [1215], "belongsTo": []},
        1215: {
            "id": 1215,
            "level": 3,
            "name": "United States",
            "contains": [12345],
            "belongsTo": [0],
        },
        12345: {
            "id": 12345,
            "level": 4,
            "name": "Minnesota",
            "contains": [],
            "belongsTo": [1215],
        },
    },
    "frequencies": {
        9: {
            "id": 9,
            "name": "Annual",
        },
    },
    "sources": {
        2: {
            "id": 2,
            "name": "FAO",
        }
    },
    "units": {
        10: {
            "id": 10,
            "abbreviation": "kg",
            "name": "kilogram",
            "baseConvFactor": {"factor": 1},
            "convType": 0,
        },
        14: {
            "id": 14,
            "name": "tonne",
            "baseConvFactor": {"factor": 1000},
            "convType": 0,
        },
        36: {
            "id": 36,
            "name": "Celsius",
            "baseConvFactor": {"factor": 1, "offset": 273},
            "convType": 1,
        },
        37: {
            "id": 37,
            "name": "Fahrenheit",
            "baseConvFactor": {"factor": 0.5, "offset": 255},
            "convType": 1,
        },
        43: {
            "id": 43,
            "name": "US Dollar (constant 2010)",
            "baseConvFactor": {"factor": None},
            "convType": 0,
        },
    },
}

mock_data_series = [
    {
        "metric_id": 860032,  # TODO: add names
        "item_id": 274,
        "region_id": 1215,
        "partner_region_id": 0,
        "frequency_id": 9,
        "source_id": 2,
    },
    {
        "metric_id": 860032,  # TODO: add names
        "item_id": 274,
        "region_id": 1216,
        "partner_region_id": 0,
        "frequency_id": 9,
        "source_id": 2,
    },
]

mock_list_of_series_points = [
    {
        "series": {
            "metricId": 860032,
            "itemId": 274,
            "regionId": 1215,
            "partnerRegionId": 0,
            "frequencyId": 9,
            # "sourceId": 2,
            "unitId": 14,
            "belongsTo": {
                "metricId": 860032,
                "itemId": 274,
                "regionId": 1215,
                "frequencyId": 9,
                "sourceId": 2,
            },
        },
        "data": [
            [
                "2017-01-01T00:00:00.000Z",
                "2017-12-31T00:00:00.000Z",
                40891,
                None,
                14,
                {},
            ],
            [
                "2018-01-01T00:00:00.000Z",
                "2018-12-31T00:00:00.000Z",
                56789,
                "2019-03-14T00:00:00.000Z",
                10,
                {},
            ],
        ],
    }
]

mock_data_points = [
    {
        "start_date": "2017-01-01T00:00:00.000Z",
        "end_date": "2017-12-31T00:00:00.000Z",
        "value": 40891,
        "unit_id": 14,
        "reporting_date": "2018-01-01T00:00:00.000Z",
        "available_date": "2018-01-31T00:00:00.000Z",
        "metric_id": 860032,
        "item_id": 274,
        "region_id": 1215,
        "partner_region_id": 0,
        "frequency_id": 9,
        # "source_id": 2,
        "belongs_to": {
            "metric_id": 860032,
            "item_id": 274,
            "region_id": 1215,
            "frequency_id": 9,
            "source_id": 2,
        },
    },
    {
        "start_date": "2017-01-01T00:00:00.000Z",
        "end_date": "2017-12-31T00:00:00.000Z",
        "value": 56789,
        "unit_id": 10,
        "reporting_date": "2018-01-01T00:00:00.000Z",
        "available_date": "2017-12-31T00:00:00.000Z",
        "metric_id": 860032,
        "item_id": 274,
        "region_id": 1216,
        "partner_region_id": 0,
        "frequency_id": 9,
        # "source_id": 2,
        "belongs_to": {
            "metric_id": 860032,
            "item_id": 274,
            "region_id": 1216,
            "frequency_id": 9,
            "source_id": 2,
        },
    },
]

mock_error_selection = {
    "metric_id": 1,
    "item_id": -15,
    "region_id": 3,
    "frequency_id": 4,
    "source_id": 5,
}
