"""Search example

Use case: "What data does Gro have available for x?"

This example shows how to query the API for sources matching a search term and
discover what data series are available for a selected source.

Note that the search functions work with any of the following entity types:
 - metrics
 - items
 - regions
 - sources (shown here)

See Also
--------
groclient.GroClient.search()
groclient.GroClient.search_and_lookup()
groclient.GroClient.get_data_series()
https://github.com/gro-intelligence/api-client/wiki/Entities-Definition
https://github.com/gro-intelligence/api-client/wiki/Data-Series-Definition

"""

import os
from groclient import GroClient

API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

def main():
    client = GroClient(API_HOST, ACCESS_TOKEN)

    # ===================
    # | client.search() |
    # ===================
    # Returns a list of ids, ordered by relevance to your given search term
    # Note that you can search across metrics, items, regions, and sources.

    print('client.search()')
    print(client.search('metrics', 'Exports')[0]) # { 'id': 125 }
    print(client.search('items', 'Wheat')[0]) # { 'id': 95 }
    print(client.search('regions', 'India')[0]) # { 'id': 1094 }
    print(client.search('sources', 'USDA NASS')[0]) # { 'id': 29 }

    # ==============================
    # | client.search_and_lookup() |
    # ==============================
    # Helper function to use the client.lookup() function on each search result
    # and see more details about the result.
    # Returns a generator, which yields one search result at a time. Use the
    # next() method to get the first result:
    print('\nclient.search_and_lookup()')
    print(next(client.search_and_lookup('metrics', 'Export Value')))
    # {'id': 10000, 'contains': [10065, 11078], 'name': 'Export Value',
    #  'definition': 'The value of exports, or goods that have been sent to a \
    #  foreign country for sale. Data is mostly reported as free-on-board, \
    #  which includes the cost of delivering the goods to a designated \
    #  delivery vessel; exports of a good may not necessarily equal imports \
    #  for the partner region, since imports and exports are measured \
    #  differently by different governments.'}

    print(next(client.search_and_lookup('items', 'Wheat')))
    # {'id': 95, 'contains': [3595, 5772], 'name': 'Wheat',
    #  'definition': "Cereals within the genus <i>Triticum</i>, which is one \
    #  of the world's most popular and widely cultivated grain crops. Data \
    #  primarily covers common and durum wheat, as well as spelt."}

    print(next(client.search_and_lookup('regions', 'India')))
    # {'id': 1094, 'contains': [11187, 11190, 11174, 11197, 11188, 11200,
    #  11204, 11186, 11180, 11177, 11207, 11201, 11173, 11178, 11195, 11194,
    #  11183, 11199, 11203, 11202, 11193, 11181, 13475, 11196, 11185, 11175,
    #  11198, 11192, 11179, 11191, 11189, 11176, 11182, 11205, 11184, 11206],
    #  'name': 'India', 'level': 3, 'latitude': 22.8838, 'longitude': 79.6201}

    print(next(client.search_and_lookup('sources', 'USDA NASS')))
    # {'id': 29, 'name': 'USDA NASS Animals', 'longName': 'USDA National \
    #  Agricultural Statistics Database', 'metaType': 'data_series',
    #  'sourceLag': {'annual': '4m15d', 'weekly': '4d', 'monthly': '1m10d'},
    #  'historicalStartDate': '1866-12-01T00:00:00.000Z',
    #  'description': 'The National Agricultural Statistics Service is an arm \
    #  of the USDA and one of its primary intelligence- and data-gathering \
    #  units. The database provides updates almost daily on livestock, crops, \
    #  demographics, economics, and environmental indicators. Metrics covered \
    #  include production, yield, area harvested, price, inputs, stocks, etc. \
    #  The granularity is mostly internal US data and goes back as far as \
    #  1850.', 'resolution': 'District', 'regionalCoverage': 'United States',
    #  'language': 'English', 'fileFormat': 'CSV'}

    # ==========================
    # | client.get_data_series |
    # ==========================
    # Once you have identified one or more entities of interest, you can see
    # what data series are available for those entities using the
    # client.get_data_series() function.

    # The normal process of data discovery using the API would be to look up
    # items and/or regions of interest first. i.e. if you know you are
    # interested in United States Corn data. Then you can see what metrics are
    # available for that item and region: production, exports, prices, etc.
    # For example:
    print('\nclient.get_data_series() Part 1: Search by item/region')
    # First look up the item/region of interest as seen in the above examples.
    # We just need the id number, so we will use search(). search_and_lookup()
    # would also work.
    corn = client.search('items', 'corn')[0]
    united_states = client.search('regions', 'united states')[0]
    # Now we can use client.get_data_series() to see what data series exist:
    data_series_list = client.get_data_series(**{
        'item_id': corn['id'],
        'region_id': united_states['id']
    })
    print('There are', len(data_series_list), 'different US Corn data series')
    unique_metrics = set(data_series['metric_name'] for data_series in data_series_list)
    print('Unique metrics:', len(unique_metrics))
    unique_sources = set(data_series['source_name'] for data_series in data_series_list)
    print('Unique sources:', len(unique_sources))

    # If you are interested in a particular source, you can also start there
    # and see what data series exist for it. One frequently asked question is
    # how to see what items/regions Gro publishes yield models for. Here is how
    # one would find out programmatically:
    print('\nclient.get_data_series() Part 2: search by source')
    # Gro publishes its own yield model values under the "Gro Yield Model"
    # source, which is treated as its own source just like any other, and you
    # can find it in the same manner:
    gro_yield_model = client.search('sources', 'Gro Yield Model')[0]
    # Now we can use client.get_data_series() to see what data series exist
    # under that source.
    data_series_list = client.get_data_series(**{
        'source_id': gro_yield_model['id']
    })
    print('There are', len(data_series_list), 'different Gro Yield Model data series')
    # There are thousands of data series in data_series_list since there are
    # many different regions. Let's just check the unique items there are yield
    # models for:
    unique_items = set(data_series['item_name'] for data_series in data_series_list)
    for item in unique_items:
        print(item)
    # Winter wheat
    # Soybeans
    # Hard red winter wheat
    # Corn
    # Wheat

if __name__ == "__main__":
    main()