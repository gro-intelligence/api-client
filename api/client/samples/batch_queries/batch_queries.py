import os
from api.client.batch_client import BatchClient

# set up the Batch Client, same as normal Client
""" API Config """
API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

api_client = BatchClient(API_HOST, ACCESS_TOKEN)

# specify everything except region_id 
selection = {
    'metric_id': 860032, 
    'item_id': 274, 
    'source_id': 25, 
    'frequency_id': 9,
    'start_date': '1998-01-01T00:00:00.000Z',
    'end_date': '1998-01-01T00:00:00.000Z'
}

# make a list of this query for every region_id in Mississippi
mississippi_county_ids = api_client.search_and_lookup("regions", "Mississippi").next()["contains"]

selections = []
for region_id in mississippi_county_ids:
    selection_temp = dict(selection)
    selection_temp["region_id"] = region_id
    selections.append(selection_temp)

# make the request in a batch, asynchronous way
output = api_client.batch_async_get_data_points(selections)

# the output data is in the same order as the input queries. 
for county_id, data in zip(mississippi_county_ids, output):
    if len(data) > 0: #mississippi contains some special regions which don't have data
        print("county_idx=%i produced %.0f tonnes of corn in 1998" % (county_id, data[0]["value"]))
    else:
        print("county_idx=%i has no data for 1998" % county_id)
