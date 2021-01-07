from random import random
import argparse
import getpass
import os
import sys
import unicodecsv

import groclient.lib
import groclient.cfg
from groclient import GroClient


def pick_random_data_series(client):  # pragma: no cover
    """Pick a random available data series."""
    data_series_list = client.get_data_series()
    random_data_series = data_series_list[int(len(data_series_list) * random())]
    return random_data_series


def print_one_data_series(client, data_series):  # pragma: no cover
    """Output the data points of a data series to stdout."""
    # Print the "name" of the series:
    print('{} {} of {} in {}:'.format(data_series['frequency_name'],
                                      data_series['metric_name'],
                                      data_series['item_name'],
                                      data_series['region_name']))
    # Print the data points:
    for point in client.get_data_points(**data_series):
        print('{}-{}: {} {}'.format(point["start_date"],
                                    point["end_date"],
                                    point["value"],
                                    client.lookup_unit_abbreviation(point["unit_id"])))


def write_one_data_series(client, data_series, filename):  # pragma: no cover
    """Output the data points of a data series to a CSV file."""
    client.get_logger().warning("Using data series: {}".format(str(data_series)))
    client.get_logger().warning("Outputing to file: {}".format(filename))
    writer = unicodecsv.writer(open(filename, "wb"))
    for point in client.get_data_points(**data_series):
        writer.writerow(
            [
                point["start_date"],
                point["end_date"],
                point["value"],
                client.lookup_unit_abbreviation(point["unit_id"]),
            ]
        )


def main():  # pragma: no cover
    """Basic Gro API command line interface.

    Note that results are chosen randomly from matching selections, and so results are not
    deterministic. This tool is useful for simple queries, but anything more complex should be done
    using the provided Python packages.

    Usage examples:
        gro_client --item=soybeans  --region=brazil --partner_region china --metric export
        gro_client --item=sesame --region=ethiopia
        gro_client --user_email=john.doe@example.com  --print_token
    For more information use --help
    """
    parser = argparse.ArgumentParser(description="Gro API command line interface")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--item")
    parser.add_argument("--metric")
    parser.add_argument("--region")
    parser.add_argument("--partner_region")
    parser.add_argument("--file")
    parser.add_argument(
        "--print_token",
        action="store_true",
        help="Output API access token for the given user email and password. "
        "Save it in GROAPI_TOKEN environment variable.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GROAPI_TOKEN"),
        help="Defaults to GROAPI_TOKEN environment variable.",
    )
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(groclient.lib.get_version_info().get('api-client-version'))
        return

    assert (
        args.user_email or args.token
    ), "Need --token, or --user_email, or $GROAPI_TOKEN"
    access_token = None

    if args.token:
        access_token = args.token
    else:
        if not args.user_password:
            args.user_password = getpass.getpass()
        access_token = groclient.lib.get_access_token(
            groclient.cfg.API_HOST, args.user_email, args.user_password
        )

    if args.print_token:
        print(access_token)
        return

    client = GroClient(groclient.cfg.API_HOST, access_token)

    if (
        not args.metric
        and not args.item
        and not args.region
        and not args.partner_region
    ):
        data_series = pick_random_data_series(client)
    else:
        data_series = next(
            client.find_data_series(
                item=args.item,
                metric=args.metric,
                region=args.region,
                partner_region=args.partner_region,
            ),
            None
        )

    if data_series is None:
        print("No data series found.")
        return

    if args.file is not None:
        write_one_data_series(client, data_series, args.file)
    else:
        print_one_data_series(client, data_series)
