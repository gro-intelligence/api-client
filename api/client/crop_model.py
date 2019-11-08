from __future__ import division
from builtins import map
from builtins import zip
import pandas
import math

from api.client.gro_client import GroClient


class CropModel(GroClient):
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
            return df[(df['item_id'] == entities['item_id']) & \
                      (df['metric_id'] == entities['metric_id']) & \
                      (df['region_id'] == region['id'])]['value'].mean(skipna=True)
        means = list(map(mapper, regions))
        self._logger.debug('Means = {}'.format(
            list(zip([region['name'] for region in regions], means))))
        # Normalize into weights
        total = math.fsum([x for x in means if not math.isnan(x)])
        return [float(mean)/total for mean in means]

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
