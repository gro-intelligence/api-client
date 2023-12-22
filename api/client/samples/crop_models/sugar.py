from __future__ import print_function

# Sample Gro API client for sugar crop model
#
# Usage example:
#
#   export PYTHONPATH=/your/path/to/gro
#   python sugar.py --token ...
#
# You can either save the gro api token in environment variable GROAPI_TOKEN and run:
#   python sugar.py
# OR use the token directly via command line argument:
#   python sugar.py --token YOUR_API_TOKEN_HERE
#
#
# Ref: https://app.gro-intelligence.com/#/displays/23713

import argparse
import unicodecsv
import os
from api.client.crop_model import CropModel

API_HOST = "api.gro-intelligence.com"


def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--token", default=os.environ.get("GROAPI_TOKEN", None))
    args = parser.parse_args()
    assert args.token, "Need --token or the token to be saved in GROAPI_TOKEN environment variable"

    model = CropModel(API_HOST, args.token)
    model.add_data_series(
        item="sugarcane", metric="production quantity", region="Brazil"
    )
    model.add_data_series(item="sugarcane", metric="yield", region="Brazil")
    series_results = model.get_data_series_list()
    for data_series in series_results:
        filename = "gro_{}_{}_{}.csv".format(
            model.lookup("items", data_series["item_id"]).get("name"),
            model.lookup("metrics", data_series["metric_id"]).get("name"),
            model.lookup("regions", data_series["region_id"]).get("name"),
        )
        filename = filename.replace("/", ":")
        writer = unicodecsv.writer(open(filename, "wb"))
        count = 0
        for point in model.get_data_points(**data_series):
            writer.writerow(
                [
                    point["start_date"],
                    point["end_date"],
                    point["value"],
                    model.lookup_unit_abbreviation(point["unit_id"]),
                ]
            )
            count += 1
        print("Output {} rows to {}".format(count, filename))

    if series_results:
        data_frame = model.get_df()
        print(
            "Loaded data frame of shape {}, columns: {}".format(
                data_frame.shape, data_frame.columns
            )
        )


if __name__ == "__main__":
    main()
