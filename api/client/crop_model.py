from __future__ import division
from builtins import map
from builtins import zip
from datetime import datetime
import math
import pandas
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


    def growing_degree_days(self, region_name, base_temperature,
                            start_date, end_date, min_temporal_coverage=0.5):
        """Get Growing Degree Days (GDD) for a region.

        Growing degree days (GDD) are a weather-based indicator that
        allows for assessing crop phenology and crop development,
        based on heat accumulation. GDD for one day is defined as
        [T_mean - T_base], where T_mean is the average temperature of
        that day if available. Typically T_mean is approximated as
        (T_max + T_min)/2.

        The GDD over a longer time interval is the sum of the GDD over
        all days in the interval. Days where the data is missing
        contribute 0 GDDs, i.e. are treated as if T_mean = T_base.
        Use the temporal coverage threshold to avoid computing GDD
        with too little data.

        The threshold and the base temperature should be carefuly
        selected based on fundamental understanding of the crops and
        region of interest.

        The region can be any region of the Gro regions, from a point
        location to a district, province etc. This will use the best
        available data series for T_max and T_min for the given region
        and time period, using "find_data_series". 

        In the simplest case, if the given region is a weather station
        location which has data for the time period, then that will be
        used. If it's a district or other region, the underlying data
        could be from one or more weather stations and/or satellite.

        Parameters
        ----------
        region_name: string, required
        base_temperature: number, required
        start_date: '%Y-%m-%d' string, required
        end_date: '%Y-%m-%d' string, required
        min_temporal_coverage: float, optional

        """
        for tmax in self.find_data_series(
                item='Temperature max', metric='Temperature',
                region=region_name, start_date=start_date, end_date=end_date):
            self.add_single_data_series(tmax)
            break
        for tmin in self.find_data_series(
                item='Temperature min', metric='Temperature',
                region=region_name, start_date=start_date, end_date=end_date):
            self.add_single_data_series(tmin)
            break
        df = self.get_df()
        if df is None or df.empty:
            raise Exception("Insufficient data for GDD in region {}".format(
                region_name))
        # For each day we want (t_min + t_max)/2, or more generally,
        # the average temperature for that day.
        tmean = df.loc[(df.item_id == tmax['item_id']) | \
                       (df.item_id == tmin['item_id'])].groupby(
                           ['region_id', 'metric_id', 'frequency_id',
                            'start_date', 'end_date']).mean()
        duration = datetime.strptime(end_date, '%Y-%m-%d') - \
                   datetime.strptime(start_date, '%Y-%m-%d')
        coverage_threshold = min_temporal_coverage * duration.days
        if tmean.value.size < coverage_threshold:
            raise Exception("Insufficient temporal coverage for GDD, " + \
                            "{} < {} data points available".format(
                                tmean.value.size, coverage_threshold))
        gdd_values = tmean.value - base_temperature
        # TODO: group by freq and normalize in case not daily
        return gdd_values.sum()
