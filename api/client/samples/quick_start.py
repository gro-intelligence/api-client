import os
import unicodecsv
import api.client.lib


API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN=os.environ['GROAPI_TOKEN']

def main():
    client = api.client.Client(API_HOST, ACCESS_TOKEN)
    selected_entities = {u'region_id': 1038, u'region_name': u'Cape Verde',
                         u'item_name': u'Management of donkey manure', u'item_id': 5187,
                         u'metric_name': u'Total Emissions Quantity (mass)', u'metric_id': 5590032}
    writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))
    data_series_list = client.get_data_series(**selected_entities)
    for data_series in data_series_list:
        for point in client.get_data_points(**data_series):
            writer.writerow([point['start_date'], point['end_date'],
                             point['value'] * point['input_unit_scale'],
                             client.lookup_unit_abbreviation(point['input_unit_id'])])


if __name__ == "__main__":
    main()
