import os
import re
from datetime import timedelta, datetime
from api.client.gro_client import GroClient

LAG_REGEX = re.compile(r'([-]*[1-9]\d*[ymdh])')
TIME_UNITS = {'d': 'days', 'm': 'months', 'y': 'years'}

def time_delta_from_lag(lag):
    """lag is of the form e.g. '1d', '1y8m', etc."""
    delta = timedelta(days = 0)
    for lag in re.split(LAG_REGEX, lag):
        if not lag:
            continue
        unit = lag[-1]
        value = int(lag[:-1])
        delta += timedelta(**{TIME_UNITS[unit]: value})
    return delta

data_series = {
    'metric_id': 2100031, 
    'item_id': 2039, 
    'region_id': 138612, 
    'partner_region_id': 0, 
    'source_id': 126, 
    'frequency_id': 1, 
    'unit_id': 2, 
}

client = GroClient('api.gro-intelligence.com', os.environ['GROAPI_TOKEN'])
source = client.lookup('sources', 126)
freq = client.lookup('frequencies', 1)
lag = source['sourceLag'][freq['name']]
dt = time_delta_from_lag(lag)

# if reporting_date not given, simulate it as end_date + lag
for point in client.get_data_points(**data_series):
    if not point['reporting_date']:
        point['reporting_date'] = datetime.strptime(point['end_date'], '%Y-%m-%dT%H:%M:%S.%fZ') + dt
    print(point)
