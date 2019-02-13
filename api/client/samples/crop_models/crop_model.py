from __future__ import division
from builtins import map
from builtins import str
from builtins import zip
from past.utils import old_div
import itertools
import pandas
import math
import unicodecsv

import api.client.lib


class CropModel(api.client.Client):
    """A Client with methods to find and add data series related to a crop
    and country. When added, data series are stored for future
    reference, and can be retrieved as a list of series, or a Pandas
    data frame containing all the points.
    """

    _logger = api.client.lib.get_default_logger()
    _data_series_list = []  # all that have been added
    _data_series_queue = []  # added but not loaded in data frame
    _data_frame = None

    def get_df(self):
        """Get the content of all data series in a Pandas frame."""
        frames = [self._data_frame]
        while self._data_series_queue:
            frames.append(pandas.DataFrame(data=self.get_data_points(
                **self._data_series_queue.pop())))
        if len(frames) > 1:
            self._data_frame = pandas.concat(frames)
        return self._data_frame

    def print_one_data_series(self, data_series, filename):
        self._logger.info("Using data series: {}".format(str(data_series)))
        self._logger.info("Outputing to file: {}".format(filename))
        writer = unicodecsv.writer(open(filename, 'wb'))
        for point in self.get_data_points(**data_series):
            writer.writerow([point['start_date'], point['end_date'],
                             point['value'] * point['input_unit_scale'],
                             self.lookup_unit_abbreviation(point['input_unit_id'])])

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

    def compute_weights(self, crop_name, metric_name, regions):
        """Add the weighting data series to this model. Compute the weights,
        which is the mean value for each region in regions, normalized
        to add up to 1.0 across regions. Returns a list of weights
        corresponding to the regions.
        """
        # Get the weighting series
        entities = {
            'item_id': self.search_for_entity('items', crop_name),
            'metric_id': self.search_for_entity('metrics', metric_name)
        }
        for region in regions:
            entities['region_id'] = region['id']
            for data_series in self.get_data_series(**entities):
                self.add_single_data_series(data_series)
                break
        # Compute the average over time for reach region
        df = self.get_df()
        
        def mapper(region):
            return df[(df['metric_id'] == entities['metric_id']) & \
                      (df['region_id'] == region['id'])]['value'].mean(skipna=True)
        means = list(map(mapper, regions))
        self._logger.debug('Means = {}'.format(
            list(zip([region['name'] for region in regions], means))))
        # Normalize into weights
        total = math.fsum([x for x in means if not math.isnan(x)])
        return [old_div(mean,total) for mean in means]

    def compute_crop_weighted_series(self,
                                     weighting_crop_name, weighting_metric_name,
                                     item_name, metric_name, regions):
        """Add the data series for the given item_name and metric_name to this
        model. Compute the weighted version of the series for each
        region in regions. The weight of a region is the fraction of
        the value of the weighting series represented by that region.
        """
        weights = self.compute_weights(weighting_crop_name, weighting_metric_name,
                                       regions)
        entities = {
            'item_id': self.search_for_entity('items', item_name),
            'metric_id': self.search_for_entity('metrics', metric_name)
        }
        for region in regions:
            entities['region_id'] = region['id']
            for data_series in self.get_data_series(**entities):
                self.add_single_data_series(data_series)
                break
        df = self.get_df()
        series_list = []
        for (region, weight) in zip(regions, weights):
            self._logger.info(u'Computing {}_{}_{} x {}'.format(
                item_name, metric_name,  region['name'], weight))
            series = df[(df['item_id'] == entities['item_id']) & \
                        (df['metric_id'] == entities['metric_id']) & \
                        (df['region_id'] == region['id'])].copy()
            series.loc[:, 'value'] = series['value']*weight
            # TODO: change metric to reflect it is weighted in this copy
            series_list.append(series)
        return pandas.concat(series_list)
