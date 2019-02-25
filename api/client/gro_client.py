from __future__ import print_function
# Basic gro api client.
#
# Usage example:
#
#   export PYTHONPATH=./gro
#   python gro/api/client/gro_client.py --item soybeans  --region brazil --partner_region china --metric export --user_email ...
#   python gro/api/client/gro_client.py --item=sesame --region=ethiopia --user_email=...
from builtins import str
from random import random
import argparse
import getpass
import itertools
import math
import sys
import unicodecsv
import pandas
import api.client.lib
import os


API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'


class GroClient(api.client.Client):
    """A Client with methods to find, and manipulate data series related
    to a crop and/or region.

    This class offers convenience methods for some common scenarios

    - finding entities by name rather than ids
    - exploration shortcuts filling in partial selections
    - finding and saving data series for repeated use, including in a data frame

    """

    _logger = api.client.lib.get_default_logger()
    _data_series_list = []  # all that have been added
    _data_series_queue = []  # added but not loaded in data frame
    _data_frame = None

    ###
    # Finding, indexing and loading multiple data series into a data frame
    ###
    def get_df(self):
        """Get the content of all data series in a Pandas frame."""
        frames = [self._data_frame]
        while self._data_series_queue:
            frames.append(pandas.DataFrame(data=self.get_data_points(
                **self._data_series_queue.pop())))
        if len(frames) > 1:
            self._data_frame = pandas.concat(frames)
        return self._data_frame

    def get_data_series_list(self):
        return list(self._data_series_list)

    def add_single_data_series(self, data_series):
        self._data_series_list.append(data_series)
        self._data_series_queue.append(data_series)
        self._logger.info("Added {}".format(data_series))
        return

    def add_data_series(self, **kwargs):
        """Search for entities matching the given names, find data series for
        the given combination, and add them to this objects list of
        series."""
        MAX_RESULTS=3
        search_results = []
        keys = []
        if kwargs.get('item'):
            search_results.append(
                self.search('items', kwargs['item'])[:MAX_RESULTS])
            keys.append('item_id')
        if kwargs.get('metric'):
            search_results.append(
                self.search('metrics', kwargs['metric'])[:MAX_RESULTS])
            keys.append('metric_id')
        if kwargs.get('region'):
            search_results.append(
                self.search('regions', kwargs['region'])[:MAX_RESULTS])
            keys.append('region_id')
        if kwargs.get('partner_region'):
            search_results.append(
                self.search('regions', kwargs['partner_region'])[:MAX_RESULTS])
            keys.append('partner_region_id')
        for comb in itertools.product(*search_results):
            entities = dict(list(zip(keys, [entity['id'] for entity in comb])))
            data_series_list = self.get_data_series(**entities)
            self._logger.debug("Found {} distinct data series for {}".format(
                len(data_series_list), entities))
            for data_series in self.rank_series_by_source(data_series_list):
                self.add_single_data_series(data_series)
                return
    ###
    # Discovery shortcuts
    ###
    def search_for_entity(self, entity_type, keywords):
        """Returns the first result of entity_type (which is items, metrics or
        regions) that matches the given keywords.
        """
        results = self.search(entity_type, keywords)
        for result in results:
            self._logger.debug("First result, out of {} {}: {}".format(
                len(results), entity_type, result['id']))
            return result['id']

    def get_provinces(self, country_name):
        for region in self.search_and_lookup('regions', country_name):
            if region['level'] == 3: # country
                provinces =  self.get_descendant_regions(region['id'], 4) # provinces
                self._logger.debug("Provinces of {}: {}".format(country_name, provinces))
                return provinces
        return None

    # Convenience methods that automatically fill in partial selections with random entities
    def pick_random_entities(self):
        """Pick a random item that has some data associated with it, and a
        random metric and region pair for that item with data
        available.
        """
        item_list = self.get_available('items')
        num = 0
        while not num:
            item = item_list[int(len(item_list)*random())]
            selected_entities = {'itemId':  item['id']}
            entity_list = self.list_available(selected_entities)
            num = len(entity_list)
        entities = entity_list[int(num*random())]
        self._logger.info("Using randomly selected entities: {}".format(str(entities)))
        selected_entities.update(entities)
        return selected_entities

    def pick_random_data_series(self, selected_entities):
        """Given a selection of tentities, pick a random available data series
        the given selection of entities.
        """
        data_series_list = self.get_data_series(**selected_entities)
        if not data_series_list:
            raise Exception("No data series available for {}".format(
                selected_entities))
        selected_data_series = data_series_list[int(len(data_series_list)*random())]
        return selected_data_series

    def print_one_data_series(self, data_series, filename):
        self._logger.info("Using data series: {}".format(str(data_series)))
        self._logger.info("Outputing to file: {}".format(filename))
        writer = unicodecsv.writer(open(filename, 'wb'))
        for point in self.get_data_points(**data_series):
            writer.writerow([point['start_date'], point['end_date'],
                             point['value'] * point['input_unit_scale'],
                             self.lookup_unit_abbreviation(point['input_unit_id'])])


def main():
    parser = argparse.ArgumentParser(description="Gro api client")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--item")
    parser.add_argument("--metric")
    parser.add_argument("--region")
    parser.add_argument("--partner_region")
    parser.add_argument("--print_token", action='store_true')
    parser.add_argument("--token", default=os.environ.get('GROAPI_TOKEN'))
    args = parser.parse_args()

    assert args.user_email or args.token, "Need --token, or --user_email, or $GROAPI_TOKEN"
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
    client = GroClient(API_HOST, access_token)

    selected_entities = {}
    if args.item:
        selected_entities['item_id'] = client.search_for_entity('items', args.item)
    if args.metric:
        selected_entities['metric_id'] = client.search_for_entity('metrics', args.metric)
    if args.region:
        selected_entities['region_id'] = client.search_for_entity('regions', args.region)
    if args.partner_region:
        selected_entities['partner_region_id'] = client.search_for_entity('regions', args.partner_region)
    if not selected_entities:
        selected_entities = client.pick_random_entities()

    data_series = client.pick_random_data_series(selected_entities)
    print("Data series example:")
    client.print_one_data_series(data_series, OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
