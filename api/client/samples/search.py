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
api.client.lib.search()
api.client.lib.search_and_lookup()
api.client.lib.get_data_series()
https://github.com/gro-intelligence/api-client/wiki/Entities-Definition
https://github.com/gro-intelligence/api-client/wiki/Data-Series-Definition

"""

import os
from api.client.gro_client import GroClient

API_HOST = 'api.gro-intelligence.com'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']

def main():
    client = GroClient(API_HOST, ACCESS_TOKEN)

    # We can search for metrics, items, regions, or sources by name. Let's
    # say we're interested in finding more information about the source
    # CASDE (China Agricultural Supply and Demand Estimates). We can search
    # for it by name to find its id, description, historical start date, etc.
    for source in client.search_and_lookup('sources', 'CASDE'):
        print(source)

    # Now, let's say we are interested in seeing what metrics/items/regions
    # Gro publishes its own yield model values for. "Gro Yield Model" is
    # treated as its own source just like any external source, and you can find
    # it in the same manner. This time we are using the `search` function
    # instead of `search_and_lookup()` since we only need the id and none of
    # that extra information mentioned above.
    # Search results are returned in order of relevance, so here we will take
    # the first one that is returned:
    source = client.search('sources', 'Gro Yield Model')[0]

    # Now we can see what data series are available for that source:
    for data_series in client.get_data_series(**{'source_id': source['id']}):
        print(data_series)

if __name__ == "__main__":
    main()