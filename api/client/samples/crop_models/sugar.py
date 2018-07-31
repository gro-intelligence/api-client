# Sample Gro API client for sugar crop model
#
# Usage example:
#
#   export PYTHONPATH=/your/path/to/gro
#   python sugar.py --user_email ... --user_password ...
#
# If you don't want to enter the password each time, print a token,
# save it and use as follows:
#
#   export GROAPI_TOKEN=`python sugar.py --user_email ... --user_password ... --print_token`
#   python sugar.py
#
# Or if you don't save the token, you can pass it via cmd line
#
#   python sugar.py --token ...
#
# Ref: https://app.gro-intelligence.com/#/displays/23713

import argparse
import sys
import api.client.lib
import os
from api.client.samples.crop_models.crop_model import CropModel

def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--print_token", action='store_true')
    parser.add_argument("--token", default=os.environ['GROAPI_TOKEN'])
    args = parser.parse_args()
    assert (args.user_email and args.user_password) or args.token, \
        "Need --token, or --user_email and --user_password"
    access_token = None
    if args.token:
        access_token = args.token
    else:
        access_token = api.client.lib.get_access_token(API_HOST, args.user_email, args.user_password)
    if args.print_token:
        print access_token
        sys.exit(0)

    model = CropModel('api.gro-intelligence.com', access_token)
    model.add_data_series(item="sugarcane", metric="production quantity", region="Brazil")
    # TODO: the following can/should be district level, instead of the whole country
    model.add_data_series(item="sugarcane", metric="yield", region="Brazil")
    model.add_data_series(item="land temperature", metric="temperature", region="Brazil")
    model.add_data_series(item="rainfall", metric="precipitation", region="Brazil")
    model.add_data_series(item="ETa percent of median", metric="Evapotranspiration anomalies", region="Brazil")
    model.add_data_series(item="Moisture", metric="soil moisture", region="Brazil")
    # TODO: maybe add prices
    # model.add_data_series(item="sugar", metric="price", region="World")
    data_frame = model.get_df()
    print "Loaded data frame of shape {}, columns: {}".format(data_frame.shape, data_frame.columns)


if __name__ == "__main__":
    main()
