try:
    # Python 3.3+
    from unittest.mock import MagicMock
except ImportError:
    # Python 2.7
    from mock import MagicMock

import pytest
from api.client.gro_client import GroClient

MOCK_HOST = 'pytest.groclient.url'
MOCK_TOKEN = 'pytest.groclient.token'

client = GroClient(MOCK_HOST, MOCK_TOKEN)


def mock_test_units(entity_type, entity_id):
    if entity_type == 'units' and entity_id == 10:
        return {
            'id': 10,
            'name': 'kilogram',
            'baseConvFactor': {'factor': 1},
            'convType': 0
        }
    elif entity_type == 'units' and entity_id == 14:
        return {
            'id': 14,
            'name': 'tonne',
            'baseConvFactor': {'factor': 1000},
            'convType': 0
        }
    elif entity_type == 'units' and entity_id == 36:
        return {
            'id': 36,
            'name': 'Celsius',
            'baseConvFactor': {'factor': 1, 'offset': 273},
            'convType': 1
        }
    elif entity_type == 'units' and entity_id == 37:
        return {
            'id': 37,
            'name': 'Fahrenheit',
            'baseConvFactor': {
                'factor': 0.5,
                'offset': 255
            },
            'convType': 1
        }
    elif entity_type == 'units' and entity_id == 43:
        return {
            'id': 43,
            'name': 'US Dollar (constant 2010)',
            'baseConvFactor': {'factor': None},
            'convType': 0
        }
    else:
        raise '{} {} not mocked'.format(entity_type, entity_id)


client.lookup = MagicMock(
    side_effect=mock_test_units
)


def test_convert_unit():
    assert client.convert_unit({'value': 1, 'unit_id': 10}, 10) == {
        'value': 1,
        'unit_id': 10
    }
    assert client.convert_unit({'value': 1, 'unit_id': 10}, 14) == {
        'value': 0.001,
        'unit_id': 14
    }
    assert client.convert_unit({'value': 3, 'unit_id': 36}, 37) == {
        'value': 42,
        'unit_id': 37
    }
    assert client.convert_unit({'value': 1, 'unit_id': 37}, 36) == {
        'value': -17.5,
        'unit_id': 36
    }

    assert client.convert_unit({}, 36) == {}

    with pytest.raises(Exception):
        assert client.convert_unit({'value': 1, 'unit_id': 10}, 43)
