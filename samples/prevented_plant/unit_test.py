import os
from api.client.gro_client import GroClient

API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

client = GroClient(API_HOST, ACCESS_TOKEN)

state_ids = {
    u'Arkansas': 13054,
    u'Illinois': 13064,
    u'Indiana': 13065,
    u'Iowa': 13066,
    u'Kansas': 13067,
    u'Kentucky': 13068,
    u'Louisiana': 13069,
    u'Michigan': 13073,
    u'Minnesota': 13074,
    u'Mississippi': 13075,
    u'Missouri': 13076,
    u'Nebraska': 13078,
    u'North Carolina': 13084,
    u'North Dakota': 13085,
    u'Ohio': 13086,
    u'South Dakota': 13092,
    u'Tennessee': 13093,
    u'Wisconsin': 13100
}

county_ids = {
    state_id: [county["id"] for county in client.get_descendant_regions(state_id, 5)]
    for state_id in state_ids.values()
}

print(county_ids)

for state_id in state_ids.values():
    for county_id in county_ids[state_id]:
        print(client.get_data_points(**{
            'metric_id': 2580001,  # planted area
            'item_id': 270,  # corn or soy
            'region_id': county_id,
            'source_id': 25,  # nass
            'frequency_id': 9,  # yearly
            # 'unit_id': 41, # acre
        }))
        print(client.get_data_points(**{
            'metric_id': 2580001,  # planted area
            'item_id': 270,  # corn or soy
            'region_id': county_id,
            'source_id': 25,  # nass
            'frequency_id': 9,  # yearly
            'unit_id': 41,  # acre
        }))
        os.system('clear')  # for unix users
