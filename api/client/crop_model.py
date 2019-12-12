from __future__ import division
from builtins import map
from builtins import zip
import pandas
import math

from api.client.gro_client import GroClient


class CropModel(GroClient):
    def compute_weights(self, crop_name, metric_name, regions):
        """Compute a vector of 'weights' that can be used for crop-weighted average across regions.

        For each region, the weight of is the mean value over time, of
        the given metric for the given crop, normalized so the sum
        across all regions is 1.0.

        For example: say we have a `region_list = [{'id': 1, 'name':
        'Province1'}, {'id': 2, 'name': 'Province2'}]`. This could
        be a list returned by client.search_and_lookup() or
        client.get_descendant_regions() for example.  Now say
        `model.compute_weights('soybeans', 'land cover area',
        region_list)` returns `[0.6, 0.4]`, that means Province1
        has 60% and province2 has 40% of the total area planted across
        the two regions, when averaged across all time.

        Parameters
        ----------
        crop_name : string
        metric_name : string
        regions : list of dicts
            Each entry is a region with id and name

        Returns
        -------
        list of floats
           weights corresponding to the regions.

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
            return df[(df['item_id'] == entities['item_id']) &
                      (df['metric_id'] == entities['metric_id']) &
                      (df['region_id'] == region['id'])]['value'].mean(skipna=True)
        means = list(map(mapper, regions))
        self._logger.debug('Means = {}'.format(
            list(zip([region['name'] for region in regions], means))))
        # Normalize into weights
        total = math.fsum([x for x in means if not math.isnan(x)])
        return [float(mean)/total for mean in means]

    def compute_crop_weighted_series(self, weighting_crop_name, weighting_metric_name,
                                     item_name, metric_name, regions):
        """Compute the 'crop-weighted average' of the given item and metric's series across regions.

        The weight of a region is the fraction of the value of the weighting series represented by
        that region as explained in compute_weights().

        For example: say we have a `region_list = [{'id': 1, 'name':
        'Province1'}, {'id': 2, 'name': 'Province2'}]`. This could
        be a list returned by client.search_and_lookup() or
        client.get_descendant_regions for example.  Now
        `model.compute_crop_weighted_series('soybeans', 'land cover
        area', 'vegetation ndvi', 'vegetation indices index',
        region_list)` will return a dataframe where the NDVI of each
        province is multiplied by the fraction of total soybeans
        area is accounted for by that province. Thus taking the sum
        across provinces will give a crop weighted average of NDVI.

        Parameters
        ----------
        weighting_crop_name : string
        weighting_metric_name : string
        item_name : string
        metric_name : string
        regions : list of dicts
            Each entry is a region with id and name

        Returns
        -------
        pandas.DataFrame
            contains the data series for the given item_name, metric_name,
            for each region in regions, with values adjusted
            by the crop weight for that region.

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
            series = df[(df['item_id'] == entities['item_id']) &
                        (df['metric_id'] == entities['metric_id']) &
                        (df['region_id'] == region['id'])].copy()
            series.loc[:, 'value'] = series['value']*weight
            # TODO: change metric to reflect it is weighted in this copy
            series_list.append(series)
        return pandas.concat(series_list)
