"""Constants about the Gro ontology that can be imported and re-used anywhere."""

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
