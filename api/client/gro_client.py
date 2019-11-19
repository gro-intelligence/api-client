from __future__ import print_function
from builtins import zip
from builtins import str
from random import random
import argparse
import getpass
import itertools
import functools
import math
import os
import pandas
import sys
import unicodecsv
from api.client import cfg, lib, Client


API_HOST = 'api.gro-intelligence.com'
OUTPUT_FILENAME = 'gro_client_output.csv'

DATA_POINTS_UNIQUE_COLS = ['item_id', 'metric_id',
                           'region_id', 'partner_region_id',
                           'frequency_id', 'source_id',
                           'reporting_date', 'start_date', 'end_date']


class GroClient(Client):
    """An extension of the Client class with extra convenience methods for some common operations.

    Extra functionality includes:
    - Automatic conversion of units
    - Finding data series using entity names rather than ids
    - Exploration shortcuts for filling in partial selections
    - Saving data series in a data frame for repeated use

    """

    def __init__(self, api_host, access_token):
        super(GroClient, self).__init__(api_host, access_token)
        self._logger = lib.get_default_logger()
        self._data_series_list = []  # all that have been added
        self._data_series_queue = []  # added but not loaded in data frame
        self._data_frame = None

    def get_logger(self):
        return self._logger

    ###
    # Finding, indexing and loading multiple data series into a data frame
    ###
    def get_df(self):
        """Get the content of all data series in a Pandas frame."""
        while self._data_series_queue:
            data_series = self._data_series_queue.pop()
            tmp = pandas.DataFrame(
                data=self.get_data_points(**data_series))
            # get_data_points response doesn't include the
            # source_id. We add it as a column, in case we have
            # several selections series which differ only by source id.
            tmp['source_id'] = data_series['source_id']
            if 'end_date' in tmp.columns:
                tmp.end_date = pandas.to_datetime(tmp.end_date)
            if 'start_date' in tmp.columns:
                tmp.start_date = pandas.to_datetime(tmp.start_date)
            if 'reporting_date' in tmp.columns:
                tmp.reporting_date = pandas.to_datetime(tmp.reporting_date)
            if self._data_frame is None:
                self._data_frame = tmp
                self._data_frame.set_index([col for col in DATA_POINTS_UNIQUE_COLS if col in tmp.columns])
            else:
                self._data_frame = self._data_frame.merge(tmp, how='outer')
        return self._data_frame

    def get_data_points(self, **selections):
        """Extend the Client's get_data_points method to add unit conversion.

        Parameters
        ----------
        selections : dict
            See lib.py get_data_points() for the base list of inputs
            This extended version may additionally include 'unit_id' which is
            the unit you wish to convert all points to.

        Returns
        -------
        list of dicts
            Unchanged output format from lib.py get_data_points()

        """
        data_points = super(GroClient, self).get_data_points(**selections)
        # Apply unit conversion if a unit is specified
        if 'unit_id' in selections:
            return list(map(functools.partial(self.convert_unit, target_unit_id=selections['unit_id']), data_points))
        # Return data points in input units if not unit is specified
        return data_points

    def get_data_series_list(self):
        return list(self._data_series_list)

    def add_single_data_series(self, data_series):
        self._data_series_list.append(data_series)
        self._data_series_queue.append(data_series)
        self._logger.info("Added {}".format(data_series))
        return

    def find_data_series(self, **kwargs):
        """Search for entities matching the given names, find data series for
        the given combination.

        Returns
        -------
        dict
           A data series, same output format as lib.py get_data_series().
        """
        search_results = []
        keys = []
        if kwargs.get('item'):
            search_results.append(
                self.search('items', kwargs['item'])[:cfg.MAX_RESULT_COMBINATION_DEPTH])
            keys.append('item_id')
        if kwargs.get('metric'):
            search_results.append(
                self.search('metrics', kwargs['metric'])[:cfg.MAX_RESULT_COMBINATION_DEPTH])
            keys.append('metric_id')
        if kwargs.get('region'):
            search_results.append(
                self.search('regions', kwargs['region'])[:cfg.MAX_RESULT_COMBINATION_DEPTH])
            keys.append('region_id')
        if kwargs.get('partner_region'):
            search_results.append(
                self.search('regions', kwargs['partner_region'])[:cfg.MAX_RESULT_COMBINATION_DEPTH])
            keys.append('partner_region_id')
        all_data_series = []
        for comb in itertools.product(*search_results):
            entities = dict(list(zip(keys, [entity['id'] for entity in comb])))
            data_series_list = self.get_data_series(**entities)
            self._logger.debug("Found {} distinct data series for {}".format(
                len(data_series_list), entities))
            # temporal coverage affects ranking so add time range if specified.
            for data_series in data_series_list:
                if kwargs.get('start_date'):
                    data_series['start_date'] = kwargs['start_date']
                if kwargs.get('end_date'):
                    data_series['end_date'] = kwargs['end_date']
            all_data_series += data_series_list
        self._logger.warning("Found {} distinct data series total for {}".format(
            len(all_data_series), kwargs))
        for data_series in self.rank_series_by_source(all_data_series):
            yield data_series

    def add_data_series(self, **kwargs):
        """Search for entities matching the given names, find data series for
        the given combination, and add them to this objects list of
        series."""
        for the_data_series in self.find_data_series(**kwargs):
            self.add_single_data_series(the_data_series)
            return
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
            if region['level'] == lib.REGION_LEVELS['country']:
                provinces = self.get_descendant_regions(region['id'], lib.REGION_LEVELS['province'])
                self._logger.debug("Provinces of {}: {}".format(country_name, provinces))
                return provinces
        return None

    ###
    # Convenience methods that automatically fill in partial selections with random entities
    ###
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

    # TODO: rename function to "write_..." rather than "print_..."
    def print_one_data_series(self, data_series, filename):
        """Output a data series to a CSV file."""
        self._logger.info("Using data series: {}".format(str(data_series)))
        self._logger.info("Outputing to file: {}".format(filename))
        writer = unicodecsv.writer(open(filename, 'wb'))
        for point in self.get_data_points(**data_series):
            writer.writerow([point['start_date'], point['end_date'],
                             point['value'] * point['input_unit_scale'],
                             self.lookup_unit_abbreviation(point['input_unit_id'])])

    def convert_unit(self, point, target_unit_id):
        """Convert the data point from one unit to another unit.

        If original or target unit is non-convertible, throw an error.

        Parameters
        ----------
        point : dict
            { value: float, unit_id: integer, ... }
        target_unit_id : integer

        Returns
        -------
        dict
            { value: float, unit_id: integer, ... }
            unit_id is changed to the target, and value is converted to use the
            new unit_id. Other properties are unchanged.

        """
        if point.get('unit_id') is None or point.get('unit_id') == target_unit_id:
            return point
        from_convert_factor = self.lookup(
            'units', point['unit_id']
        ).get('baseConvFactor')
        if not from_convert_factor.get('factor'):
            raise Exception(
                'unit_id {} is not convertible'.format(point['unit_id'])
            )
        to_convert_factor = self.lookup(
            'units', target_unit_id
        ).get('baseConvFactor')
        if not to_convert_factor.get('factor'):
            raise Exception(
                'unit_id {} is not convertible'.format(target_unit_id)
            )
        if point.get('value') is not None:
            value_in_base_unit = (
                point['value'] * from_convert_factor.get('factor')
            ) + from_convert_factor.get('offset', 0)
            point['value'] = float(
                value_in_base_unit - to_convert_factor.get('offset', 0)
            ) / to_convert_factor.get('factor')
        point['unit_id'] = target_unit_id
        return point


"""Basic Gro API command line interface.

Note that results are chosen randomly from matching selections, and so results are not deterministic. This tool is useful for simple queries, but anything more complex should be done using the provided Python packages.

Usage examples:
    gro_client --item=soybeans  --region=brazil --partner_region china --metric export
    gro_client --item=sesame --region=ethiopia
    gro_client --user_email=john.doe@example.com  --print_token
For more information use --help
"""
def main():
    parser = argparse.ArgumentParser(description="Gro API command line interface")
    parser.add_argument("--user_email")
    parser.add_argument("--user_password")
    parser.add_argument("--item")
    parser.add_argument("--metric")
    parser.add_argument("--region")
    parser.add_argument("--partner_region")
    parser.add_argument("--print_token", action='store_true',
                        help="Ouput API access token for the given user email and password. "
                        "Save it in GROAPI_TOKEN environment variable.")
    parser.add_argument("--token", default=os.environ.get('GROAPI_TOKEN'),
                        help="Defaults to GROAPI_TOKEN environment variable.")
    args = parser.parse_args()

    assert args.user_email or args.token, "Need --token, or --user_email, or $GROAPI_TOKEN"
    access_token = None

    if args.token:
        access_token = args.token
    else:
        if not args.user_password:
            args.user_password = getpass.getpass()
        access_token = lib.get_access_token(API_HOST, args.user_email, args.user_password)
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


def get_df(client, **selected_entities):
    """Deprecated: use the corresponding method in GroClient instead."""
    return pandas.DataFrame(client.get_data_points(**selected_entities))


def search_for_entity(client, entity_type, keywords):
    """Deprecated: use the corresponding method in GroClient instead."""
    return client.search_for_entity(entity_type, keywords)


def pick_random_entities(client):
    """Deprecated: use the corresponding method in GroClient instead."""
    return client.pick_random_entities()


def print_random_data_series(client, selected_entities):
    """Example which prints out a CSV of a random data series that
    satisfies the (optional) given selection.
    """
    return client.print_one_data_series(
        client.pick_random_data_series(selected_entities),
        OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
