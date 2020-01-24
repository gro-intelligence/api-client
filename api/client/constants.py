"""Importable by lib or Client classes."""

REGION_LEVELS = {
    'world': 1,
    'continent': 2,
    'country': 3,
    'province': 4,  # Equivalent to state in the United States
    'district': 5,  # Equivalent to county in the United States
    'city': 6,
    'market': 7,
    'other': 8,
    'coordinate': 9
}

ENTITY_TYPES_PLURAL = ['metrics', 'items', 'regions', 'frequencies', 'sources', 'units']
DATA_SERIES_UNIQUE_TYPES_ID = [
    'metric_id',
    'item_id',
    'region_id',
    'partner_region_id',
    'frequency_id',
    'source_id'
]
DATA_POINTS_UNIQUE_COLS = DATA_SERIES_UNIQUE_TYPES_ID + [
    'reporting_date',
    'start_date',
    'end_date'
]

ENTITY_PROPERTIES = {
    'metrics': {
        'allowedAggregations': 'allowed-aggregations',
        'allowNegative': 'allow-negative',
        'belongsTo': 'belongs-to',
        'contains': 'contains',
        'definition': 'definitions',
        'name': 'names'
    },
    'items': {
        'belongsTo': 'belongs-to',
        'contains': 'contains',
        'definition': 'definitions',
        'name': 'names'
    },
    'regions': {
        'belongsTo': 'belongs-to',
        'contains': 'contains',
        'definition': 'definitions',
        'historical': 'historical',  # TODO: does this exist?
        'latitude': 'latitudes',
        'level': 'levels',
        'longitude': 'longitudes',
        'name': 'names'
    },
    'frequencies': {
        'abbrev': 'abbreviations',
        'name': 'names',
        'periodLength': 'periods'
    },
    'sources': {
        'description': 'descriptions',
        'fileFormat': 'file-format',  # TODO: plural endpoint
        'historicalStartDate': 'historical-start-dates',
        'language': 'language',  # TODO: plural endpoint
        'longName': 'long-names',
        'name': 'names',
        'regionalCoverage': 'regional-coverages',
        'resolution': 'resolutions',
        'sourceLag': 'lags'
    },
    'units': {
        'abbreviation': 'abbreviations',
        'baseConvFactor': 'conversions',
        'convType': 'conversion-types',
        'namePlural': 'plural-names',
        'name': 'names'
    }
}