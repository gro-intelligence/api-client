import os
import unicodecsv
import api.client.lib

API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN=os.environ['GROAPI_TOKEN']

def main():
    client = api.client.Client(API_HOST, ACCESS_TOKEN)

    selected_entities = {u'frequency_id': 3,

            u'input_unit_id': 189,

            u'item_id': 321,

            u'metric_id': 70029,

            'region_id': 13074,

            u'show_revisions': False,

            u'source_id': 3,

            'start_date': '2018-12-10'}
    writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))

    # Get what possible series there are for that combination of selections
    for data_series in client.get_data_series(**selected_entities):

        # Add a time range restriction to your data request (Optional - otherwise get all points)
        # data_series['start_date'] = '2000-01-01'
        # data_series['end_date'] = '2012-12-31'

        for point in client.get_data_points(**data_series):
            writer.writerow([
                point['start_date'],
                point['end_date'],
                point['value'],
                client.lookup_unit_abbreviation(point['input_unit_id'])
            ])


if __name__ == "__main__":
    main()
