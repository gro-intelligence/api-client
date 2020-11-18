import os
import unicodecsv
from groclient import GroClient

API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'
ACCESS_TOKEN = os.environ['GROAPI_TOKEN']


def main():
    client = GroClient(API_HOST, ACCESS_TOKEN)

    selected_entities = {'region_id': 1210,  # Ukraine
                         'item_id': 95,  # Wheat
                         'metric_id': 570001}  # Area Harvested (area)

    writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))

    # Get what possible series there are for that combination of selections
    for data_series in client.get_data_series(**selected_entities):

        # Add a time range restriction to your data request
        # (Optional - otherwise get all points)
        data_series['start_date'] = '2000-01-01'
        data_series['end_date'] = '2012-12-31'

        for point in client.get_data_points(**data_series):
            writer.writerow([
                point['start_date'],
                point['end_date'],
                point['value'],
                client.lookup_unit_abbreviation(point['unit_id'])
            ])


if __name__ == "__main__":
    main()
