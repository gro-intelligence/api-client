import os
import unicodecsv
import api.client.lib

API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN=os.environ['GROAPI_TOKEN']

def main():
    client = api.client.Client(API_HOST, ACCESS_TOKEN)
    selected_entities = { u'region_id': 1038,
                          u'item_id': 5187,
                          u'metric_id': 5590032,
                          u'source_id': 2,
                          u'frequency_id': 9,
                          u'start_date': '2000-01-01',
                          u'end_date': '2016-12-31' }
    writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))
    for point in client.get_data_points(**selected_entities):
        writer.writerow([
            point['start_date'],
            point['end_date'],
            point['value'],
            client.lookup_unit_abbreviation(point['input_unit_id'])
        ])


if __name__ == "__main__":
    main()
