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

    def add_data_series(self, **kwargs):
        """Search for entities matching the given names, find data series for
        the given combination, and add them to this objects list of
        series."""
        entities = {}
        if kwargs.get('item'):
            entities['item_id'] = self.search_for_entity('items', kwargs['item'])
        if kwargs.get('metric'):
            entities['metric_id'] = self.search_for_entity('metrics', kwargs['metric'])
        if kwargs.get('region'):
            entities['region_id'] = self.search_for_entity('regions', kwargs['region'])
        if kwargs.get('partner_region'):
            entities['partner_region_id'] = self.search_for_entity(
                kwargs['partner_region'], partner_region)
        # TODO: add support for source and frequency and don't rank by source if specified
        data_series_list = self.get_data_series(**entities)
        self._logger.debug("Found {} distinct data series".format(len(data_series_list)))
        for data_series in self.rank_series_by_source(data_series_list):
            self._data_series_list.append(data_series)
            self._logger.info("Added {}".format(data_series))
            self._data_frame = None
            return
            
    def search_for_entity(self, entity_type, keywords):
        """Returns the first result of entity_type (which is items, metrics or
        regions) that matches the given keywords.
        """
        results = self.search(entity_type, keywords)
        for result in results:
            self._logger.debug("First result, out of {} {}: {}, {}".format(
                len(results), entity_type, result['id']))
            return result['id']
