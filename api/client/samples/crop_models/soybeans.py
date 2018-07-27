# Sample Gro API client that retrieves data series for Brazil soybeans
# yield from multiple sources.
#
# Usage example: If you have saved GROAPI_TOKEN environment variable,
#
#   python soybeans.py
#
# If you haven't saved the token, you can pass it via cmd line
#
#   python soybeans.py --token ...
#
# Ref https://app.gro-intelligence.com/#/displays/25894

import argparse
import os
import sys

import api.client.lib
from api.client.samples.crop_models.crop_model import CropModel


def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--token", default=os.environ['GROAPI_TOKEN'])
    args = parser.parse_args()

    model = CropModel('api.gro-intelligence.com', args.token)
    entities = {}
    # Search for item and metric by name, and use the top result
    entities['item_id'] =  model.search_for_entity('items', "soybeans")
    entities['metric_id'] = model.search_for_entity('metrics', "yield")
    # Search for region by name, but we don't use the top result,
    # instead we use the one of level 3 (the country -- there are many
    # regions with "brazil" in the name, level = 3 is the country
    for region in model.search_and_lookup('regions', "brazil"):
        if region['level'] == 3:
            entities['region_id'] = region['id']
    data_series_list = model.get_data_series(**entities)
    print "There are {} data series for {}.".format(len(data_series_list), entities)
    for data_series in data_series_list:
        # Look up the name of the source based on the source_id
        source_name = model.lookup('sources', data_series['source_id']).get('longName')
        print "{}: {} to {}".format(source_name,
                                    data_series['start_date'], data_series['end_date'])
        model.add_single_data_series(data_series)

    data_frame = model.get_df()
    print "Loaded data frame of shape {}, columns: {}".format(data_frame.shape, data_frame.columns)


if __name__ == "__main__":
    main()
