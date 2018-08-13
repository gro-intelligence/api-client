import itertools
import pandas
import unicodecsv

import api.client.lib


class CropModel(api.client.Client):

    _logger = api.client.lib.get_default_logger()
    _data_series_list = []
    _data_frame = None

    def get_df(self):
        """Get the content of all data series in a Pandas frame."""
        if self._data_frame is None:
            self._data_frame = pandas.concat(
                pandas.DataFrame(data=self.get_data_points(**series))
                for series in self._data_series_list)
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
        return self._data_series_list

    def add_single_data_series(self, data_series):
        self._data_series_list.append(data_series)
        self._logger.info("Added {}".format(data_series))
        self._data_frame = None
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
            entities = dict(zip(keys, [entity['id'] for entity in comb]))
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
        provinces = []
        for region in self.search_and_lookup('regions', country_name):
            if region['level'] == 3: # country
                for member_id in region['contains']:
                    member = self.lookup('regions', member_id)
                    if member['level'] == 4: # province
                        provinces.append(member)
                break
        return provinces

    def add_production_by_province(self, crop_name, country_name):
        entities = {
            'item_id': self.search_for_entity('items', crop_name),
            'metric_id': self.search_for_entity(
                'metrics', "Production Quantity (mass)")}
        for province in self.get_provinces(country_name):
            entities['region_id'] = province['id']
            for data_series in self.get_data_series(**entities):
                self.add_single_data_series(data_series)
                break
