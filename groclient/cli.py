import argparse
import getpass
import os
import sys

import groclient.lib
import groclient.cfg
from groclient import GroClient

OUTPUT_FILENAME = "gro_client_output.csv"


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
    parser.add_argument(
        "--print_token",
        action="store_true",
        help="Ouput API access token for the given user email and password. "
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
        ds = client.pick_random_data_series(client.pick_random_entities())
    else:
        ds = next(
            client.find_data_series(
                item=args.item,
                metric=args.metric,
                region=args.region,
                partner_region=args.partner_region,
            )
        )
    client.print_one_data_series(ds, OUTPUT_FILENAME)
