# Sample Gro API client for sugar model crop model
#
# Usage example:
#
#   export PYTHONPATH=/your/path/to/gro
#
#   python gro/api/client/sample/sugar.py --user_email ... --user_password ...
#
#   OR
#
#   python gro/api/client/gro_client.py  --user_email ... --user_password ... --print_token
#   python gro/api/client/gro_client.py --token=$GROAPI_TOKEN
#
# Ref: https://app.gro-intelligence.com/#/displays/23713
#

import argparse
import sys
import api.client.lib
from api.client.samples.crop_models.crop_model import CropModel

def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--print_token", action='store_true')
    parser.add_argument("--token")
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


if __name__ == "__main__":
    main()
