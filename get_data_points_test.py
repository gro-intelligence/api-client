# -*-coding: utf-8 -*-
import argparse
import api.client.lib


def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--token")
    parser.add_argument("--api_host", default='api.gro-intelligence.com')
    args = parser.parse_args()

    for selection in [
            {'item_id': 4, 'source_id': 2, 'frequency_id': 9, 'metric_id': 11078, 'region_id': 1098},
            {'item_id': 4, 'metric_id': 11078, 'region_id': 1098},
            {'item_id': 4, 'source_id': 2, 'frequency_id': 9, 'metric_id': 11111078, 'region_id': 1098},
            {'item_id': 4, 'metric_id': 11078, 'region_id': 1}]:
        try: 
            print len(filter(lambda x: x, api.client.lib.get_data_points(args.token, args.api_host, **selection))), " data points"
        except Exception as e:
            print e
        

if __name__ == "__main__":
    main()
