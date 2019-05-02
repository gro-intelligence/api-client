from __future__ import print_function
import argparse
import getpass
import sys
import unicodecsv
import api.client.lib
import os
from api.client.samples.crop_models.crop_model import CropModel

API_HOST = 'api.gro-intelligence.com'

def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--print_token", action='store_true')
    parser.add_argument("--token", default=os.environ.get('GROAPI_TOKEN', None))
    args = parser.parse_args()
    assert args.user_email or args.token, \
        "Need --token or --user_email"
    access_token = None
    if args.token:
        access_token = args.token
    else:
        if not args.user_password:
            args.user_password = getpass.getpass()
        access_token = api.client.lib.get_access_token(API_HOST, args.user_email, args.user_password)
    if args.print_token:
        print(access_token)
        sys.exit(0)

    model = CropModel(API_HOST, access_token)
    model.add_data_series(item="pork, total", metric="domestic consumption", region="china")
    model.add_data_series(item="rainfall", metric="precipitation", region="ethiopia")
    model.add_data_series(item="corn", metric="yield", region="top 5 countries")
    model.add_data_series(item="banana", metric="production", region="top 5 countries")
    
    series_results = model.get_data_series_list()
    for data_series in series_results:
        filename = 'gro_{}_{}_{}.csv'.format(
            model.lookup('items', data_series['item_id']).get('name'),
            model.lookup('metrics', data_series['metric_id']).get('name'),
            model.lookup('regions', data_series['region_id']).get('name'))
        filename = filename.replace('/', ':')
        writer = unicodecsv.writer(open(filename, 'wb'))
        count = 0
        for point in model.get_data_points(**data_series):
            writer.writerow([point['start_date'], point['end_date'],
                             point['value'] * point['input_unit_scale'],
                             model.lookup_unit_abbreviation(point['input_unit_id'])])
            count += 1
        print("Output {} rows to {}".format(count, filename))

    if series_results:
        data_frame = model.get_df()
        print("Loaded data frame of shape {}, columns: {}".format(data_frame.shape, data_frame.columns))


if __name__ == "__main__":
    main()
