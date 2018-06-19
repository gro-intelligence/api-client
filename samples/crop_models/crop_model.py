import pandas
import unicodecsv

import api.client.lib


class CropModel(api.client.Client):

    _logger = api.client.lib.get_default_logger()
    _data_series_list = []
    _data_frame = None

    def get_df(self):
        """Get the content of all data series in a Pandas frame."""
        for series in self._data_series_list:
            df = pandas.DataFrame(self.get_data_points(**series))
            if not self._data_frame:
                self._data_frame = df
            else:
                self._data_frame.add(df)
        return _data_frame
    
    def print_one_data_series(self, data_series):
        self._logger.info("Using data series: {}".format(str(data_series)))
        self._logger.info("Outputing to file: {}".format(OUTPUT_FILENAME))
        writer = unicodecsv.writer(open(OUTPUT_FILENAME, 'wb'))
        for point in self.get_data_points(**data_series):
            writer.writerow([point['start_date'], point['end_date'],
                             point['value'] * point['input_unit_scale'],
                             self.lookup_unit_abbreviation(point['input_unit_id'])])

    def add_data_series(self, item, metric, region, partner_region=None):
        """Search for entities matching the given names, find data series for
        the given combination, and add them to this objects list of
        series."""
        entities = {}
        if item:
            entities['item_id'] = self.search_for_entity('items', item)
        if metric:
            entities['metric_id'] = self.search_for_entity('metrics', metric)
        if region:
            entities['region_id'] = self.search_for_entity('regions', region)
        if partner_region:
            entities['partner_region_id'] = self.search_for_entity(
                'regions', partner_region)
        data_series_list = self.get_data_series(**entities)
        self._logger.info("Found {} distinct data series".format(len(data_series_list)))
        for data_series in self.rank_series_by_source(data_series_list):
            self._data_series_list.append(data_series)
            self._logger.info("Added {}".format(data_series))
            
    def search_for_entity(self, entity_type, keywords):
        """Returns the first result of entity_type (which is items, metrics or
        regions) that matches the given keywords.
        """
        results = self.search(entity_type, keywords)
        for result in results[entity_type]:
            self._logger.info("First result, out of {} {}: {}, {}".format(
                len(results[entity_type]), entity_type, result['id'], result['name']))
            return result['id']
