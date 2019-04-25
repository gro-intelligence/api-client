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

    # See what sources match the "Gro" search term
    for source in client.search_and_lookup('sources', 'Gro'):
        print(source)

    # Take the best-matching source for "Gro Yield Model"
    source = client.search('sources', 'Gro Yield Model')[0]

    # See what data series are available for that source
    for data_series in client.get_data_series(**{'source_id': source['id']}):
        print(data_series)

if __name__ == "__main__":
    main()