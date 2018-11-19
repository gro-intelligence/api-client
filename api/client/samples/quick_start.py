import os
import unicodecsv
import api.client.lib

API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN=os.environ['GROAPI_TOKEN']

def main():
    client = api.client.Client(API_HOST, ACCESS_TOKEN)

    # Requested data is not available at level (country) but is available at province-level
    selected_entities = { u'region_id': 1215,
                          u'item_id': 2636,
                          u'metric_id': 3040042,
                          u'source_id': 25,
                          u'frequency_id': 2 }

    # Get what possible series there are for that combination of selections
    data_series_list = list(client.get_data_series(**selected_entities))
    print(data_series_list)
    ranked_series = list(client.rank_series_by_source(data_series_list))
    print(ranked_series)
    print(list(client.get_data_points(**ranked_series[0])))

if __name__ == "__main__":
    main()
