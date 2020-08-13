from __future__ import division
from builtins import map
from builtins import zip
from datetime import datetime
import numpy
import pandas
from groclient.client import GroClient


class CropModel(GroClient):

    def compute_weights(self, crop_name, metric_name, regions):
        """Compute a vector of 'weights' that can be used for crop-weighted
        average across regions, as in :meth:`~.compute_crop_weighted_series`.

        For each region, the weight of is the mean value over time, of
        the given metric for the given crop, normalized so the sum
        across all regions is 1.0.

        For example: say we have a `region_list = [{'id': 1, 'name':
        'Province1'}, {'id': 2, 'name': 'Province2'}]`. This could
        be a list returned by :meth:`~.client.search_and_lookup` or
        :meth:`~.client.get_descendant_regions` for example.  Now say
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


        See also
        --------
        :meth:`~.compute_crop_weighted_series`

        """
        # Get the weighting series
        entities = { 'item_ids': set(), 'metric_ids': set() }
        for region in regions:
            series = self.add_data_series(
                item=crop_name, metric=metric_name, region=region['name'],
                result_filter=lambda x: 'region_id' not in x or \
                                        x['region_id'] == region['id'])
            if series:
                entities['item_ids'].add(series['item_id'])
                entities['metric_ids'].add(series['metric_id'])

        # Compute the average over time for reach region
        df = self.get_df()

        def mapper(region):
            return df[(df['item_id'].isin(entities['item_ids'])) &
                      (df['metric_id'].isin(entities['metric_ids'])) &
                      (df['region_id'] == region['id'])]['value'].mean(skipna=True)
        means = list(map(mapper, regions))
        self.get_logger().debug('Means = {}'.format(
            list(zip([region['name'] for region in regions], means))))
        # Normalize into weights
        total = numpy.nansum(means)
        if not numpy.isclose(total, 0.0):
            return [float(mean)/total for mean in means]
        self.get_logger().warning(
            'Cannot normalize {} {} data.'.format(crop_name, metric_name))
        return means


    def compute_crop_weighted_series(self, weighting_crop_name, weighting_metric_name,
                                     item_name, metric_name, regions,
                                     weighting_func=lambda w, v: w*v):
        """Compute the 'crop-weighted average' of the series for the given
        item and metric, across regions. The weight of a region is the
        fraction of the value of the weighting series represented by
        that region as explained in :meth:`~.compute_weights`.

        For example: say we have a `region_list = [{'id': 1, 'name':
        'Province1'}, {'id': 2, 'name': 'Province2'}]`. This could
        be a list returned by :meth:`~.client.search_and_lookup` or
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
        weighting_func: optional function
            A function of (weight, value) to apply. Default: weight*value

        Returns
        -------
        pandas.DataFrame
            contains the data series for the given item_name, metric_name,
            for each region in regions, with values adjusted
            by the crop weight for that region.

        """
        weights = self.compute_weights(
            weighting_crop_name, weighting_metric_name, regions)

        entities = { 'item_ids': set(), 'metric_ids': set() }
        for region in regions:
            series = self.add_data_series(
                item=item_name, metric=metric_name, region=region['name'],
                result_filter=lambda x: 'region_id' not in x or \
                                        x['region_id'] == region['id'])
            if series:
                entities['item_ids'].add(series['item_id'])
                entities['metric_ids'].add(series['metric_id'])

        df = self.get_df()
        series_list = []
        for (region, weight) in zip(regions, weights):
            self._logger.info(u'Computing {}_{}_{} x {}'.format(
                item_name, metric_name,  region['name'], weight))
            series = df[(df['item_id'].isin(entities['item_ids'])) &
                        (df['metric_id'].isin(entities['metric_ids'])) &
                        (df['region_id'] == region['id'])].copy()
            series.loc[:, 'value'] = weighting_func(weight, series['value'])
            # TODO: change metric to reflect it is weighted in this copy
            series_list.append(series)
        return pandas.concat(series_list)

    def compute_gdd(self, tmin_series, tmax_series, base_temperature,
                    start_date, end_date, min_temporal_coverage,
                    upper_temperature_cap):
        """Compute Growing Degree Days value from specific data series.

        This function performs the low-level computation used in :meth:`~.growing_degree_days`.

        Parameters
        ----------
        tmin_series : dict
            A data series object for min temperature
            e.g. {metric_id: 1, item_id: 2, region_id: 3, source_id: 4, frequency_id: 5}
        tmax_series : dict
            A data series object for max temperature
            e.g. {metric_id: 1, item_id: 2, region_id: 3, source_id: 4, frequency_id: 5}
        base_temperature : number
        start_date : string
            YYYY-MM-DD date
        end_date : string
            YYYY-MM-DD date
        min_temporal_coverage : float, optional
        upper_temperature_cap : number, optional

        Returns
        -------
        number
            The sum of the GDD over all days in the interval

        See also
        --------
        :meth:`~.growing_degree_days`
        """
        self.add_single_data_series(tmin_series)
        self.add_single_data_series(tmax_series)
        df = self.get_df()
        if df is None or df.empty:
            raise Exception("Insufficient data for GDD")
        # For each day we want (t_min + t_max)/2, or more generally,
        # the average temperature for that day.
        tmean = df.loc[(df.item_id == tmax_series['item_id']) | \
                       (df.item_id == tmin_series['item_id'])].groupby(
                           ['region_id', 'metric_id', 'frequency_id',
                            'start_date', 'end_date']).mean()
        duration = datetime.strptime(end_date, '%Y-%m-%d') - \
                   datetime.strptime(start_date, '%Y-%m-%d')
        if duration.days > 366:
            self.get_logger().warning(
                'GDD time range is more than 1 year {} - {}.'.format(
                    start_date, end_date))
        coverage_threshold = min_temporal_coverage * duration.days
        if tmean.value.size < coverage_threshold:
            raise Exception(
                "Insufficient coverage for GDD, {} < {} data points. ".format(
                    tmean.value.size, coverage_threshold) +
                "min_temporal_coverage is {}.".format(min_temporal_coverage))
        gdd_values = tmean.value.apply(
            lambda x: max(min(x, upper_temperature_cap) - base_temperature, 0))
        # TODO: group by freq and normalize in case not daily
        # TODO: add unit conversions in case future sources are in different units
        return gdd_values.sum()

    def growing_degree_days(self, region_name, base_temperature,
                            start_date, end_date, min_temporal_coverage=1.0,
                            upper_temperature_cap=float("Infinity")):
        """Get Growing Degree Days (GDD) for a region.

        Growing degree days (GDD) are a weather-based indicator that
        allows for assessing crop phenology and crop development,
        based on heat accumulation. GDD for one day is defined as
        max(T_mean - T_base, 0), where T_mean is the average
        temperature of that day if available. Typically T_mean is
        approximated as (T_max + T_min)/2. If upper_temperature_cap is
        specified, T_mean is capped to not exceed that value.

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
        and time period, using "find_data_series". In the simplest
        case, if the given region is a weather station location which
        has data for the time period, then that will be used. If it's
        a district or other region, the underlying data could be from
        one or more weather stations and/or satellite.  To by-pass the
        search for available series, use :meth:`~.compute_gdd` directly.

        Parameters
        ----------
        region_name : string
        base_temperature : number
        start_date : string
            YYYY-MM-DD date
        end_date : string
            YYYY-MM-DD date
        min_temporal_coverage : float, optional
        upper_temperature_cap : number, optional

        Returns
        -------
        number
            The sum of the GDD over all days in the interval

        """
        try:
            tmin_series = next(self.find_data_series(
                item='Temperature min', metric='Temperature', region=region_name,
                start_date=start_date, end_date=end_date))
            tmax_series = next(self.find_data_series(
                item='Temperature max', metric='Temperature', region=region_name,
                start_date=start_date, end_date=end_date))
            return self.compute_gdd(tmin_series, tmax_series, base_temperature,
                                    start_date, end_date, min_temporal_coverage,
                                    upper_temperature_cap)
        except StopIteration:
            raise Exception(
                "Can't find data series to compute GDD in region {}".format(
                    region_name))
