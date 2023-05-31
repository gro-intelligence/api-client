from groclient.client import GroClient
from groclient import lib
import pandas as pd


class Experimental(GroClient):
    """The experimental client will introduce a range of experimental functions with better user experience.
    While you will be able to access better performance and new features at an early stage,
    you should be aware that things might change (e.g response format)."""

    def get_data_points(self, **selections):
        """This function is a mirror of existing :meth:`~groclient.GroClient.get_data_points`, but with limited scope.

        For example:

        - "Gro derived on-the-fly" is under development.

        - Many sources are still under migration (please refer to internal confluence page for source migration timeline)

        Parameters
        ----------
        metric_id : integer
            How something is measured. e.g. "Export Value" or "Area Harvested"
        item_ids : integer or list of integers
            What is being measured. e.g. "Corn" or "Rainfall"
        region_ids : integer or list of integers
            Where something is being measured e.g. "United States Corn Belt" or "China"
        partner_region_ids : integer or list of integers, optional
            partner_region refers to an interaction between two regions, like trade or
            transportation. For example, for an Export metric, the "region" would be the exporter
            and the "partner_region" would be the importer. For most series, this can be excluded
            or set to 0 ("World") by default.
        source_id : integer
        frequency_id : integer
        unit_id : integer, optional
        start_date : string, optional
            All data points with end dates after this date.
        end_date : string, optional
            All data points with start dates before this date.
        coverage_threshold : float, optional
            Custom threshold on the coverage of geospatial data. Value should be between 0 and 1.

        Returns
        -------
        dict
            dictionary containing list of data_points and series_description

            Example::

                from groclient.experimental import Experimental

                exp_client = Experimental(access_token="your_token_here")
                exp_client.get_data_points(
                    **{
                        'metric_id': 2540047,
                        'item_ids': [3457],
                        'region_ids': [100023971, 100023990],
                        'frequency_id': 1,
                        'source_id': 26,
                        'start_date': '2021-12-20',
                        'end_date': '2021-12-21',
                    }
                )

            Returns::

                {
                    "data_series": [
                        {
                            "data_points": [
                                {
                                    "value": 33.20465087890625,
                                    "start_timestamp": "1639958400",
                                    "end_timestamp": "1640044800"
                                }
                            ],
                            "series_description": {
                                "source_id": 26,
                                "item_id": 3457,
                                "metric_id": 2540047,
                                "frequency_id": 1,
                                "region_id": 100023971,
                                "unit_id": 36
                            }
                        },
                        {
                            "data_points": [
                                {
                                    "value": 32.73432922363281,
                                    "start_timestamp": "1639958400",
                                    "end_timestamp": "1640044800"
                                }
                            ],
                            "series_description": {
                                "source_id": 26,
                                "item_id": 3457,
                                "metric_id": 2540047,
                                "frequency_id": 1,
                                "region_id": 100023990,
                                "unit_id": 36
                            }
                        }
                    ],
                    "meta": {
                        "version": "v1.266.0",
                        "copyright": "Copyright (c) Gro Intelligence",
                        "timestamp": "Wed, 19 Apr 2023 14:34:05 GMT"
                    }
                }
        """
        data_stream_list = lib.get_data_points_v2_prime(
            self.access_token, self.api_host, **selections
        )

        # due to the issue in javascript when dealing with 'int64'
        # here we would manually convert timestamp from str to int
        for data_stream in data_stream_list:
            for data_point in data_stream['data_points']:
                data_point['start_timestamp'] = int(data_point['start_timestamp'])
                data_point['end_timestamp'] = int(data_point['start_timestamp'])

        return data_stream_list


    def get_data_points_df(self, **selections):
        """Call :meth:`~groclient.Experimental.get_data_points` and return as a combined
        dataframe.

        Parameters
        ----------
        metric_id : integer
            How something is measured. e.g. "Export Value" or "Area Harvested"
        item_ids : integer or list of integers
            What is being measured. e.g. "Corn" or "Rainfall"
        region_ids : integer or list of integers
            Where something is being measured e.g. "United States Corn Belt" or "China"
        partner_region_ids : integer or list of integers, optional
            partner_region refers to an interaction between two regions, like trade or
            transportation. For example, for an Export metric, the "region" would be the exporter
            and the "partner_region" would be the importer. For most series, this can be excluded
            or set to 0 ("World") by default.
        source_id : integer
        frequency_id : integer
        unit_id : integer, optional
        start_date : string, optional
            All data points with end dates after this date.
        end_date : string, optional
            All data points with start dates before this date.
        coverage_threshold : float, optional
            Custom threshold on the coverage of geospatial data. Value should be between 0 and 1.

        Returns
        -------
        pandas.DataFrame
            The results from :meth:`~groclient.Experimental.get_data_points`, appended together
            into a single dataframe.
            Data point attributes in timestamp format (e.g `start_timestamp`, `end_timestamp`)
            will be converted into human readable format (`YYYY-MM-DD`), and renamed as
            `start_date` and `end_date`

            Example::

                from groclient.experimental import Experimental

                exp_client = Experimental(access_token="your_token_here")
                exp_client.get_data_points_df(
                                        **{
                                            'metric_id': 2540047,
                                            'item_ids': [3457],
                                            'region_ids': [100023971, 100023990],
                                            'frequency_id': 1,
                                            'source_id': 26,
                                            'start_date': '2021-12-20',
                                            'end_date': '2021-12-21',
                                        }
                                    )
        """
        res = lib.get_data_points_v2_prime(
            self.access_token, self.api_host, **selections
        )

        if len(res) == 0:
            return pd.DataFrame()

        dfs = []
        for data_series in res:
            data_points = data_series["data_points"]
            series_description = data_series["series_description"]
            df = pd.DataFrame(data_points)
            series_df = pd.json_normalize(series_description)
            series_df = pd.concat([series_df] * len(df), ignore_index=True)
            df = pd.concat([df, series_df], axis=1)
            df["start_timestamp"] = pd.to_datetime(df["start_timestamp"], unit="s")
            df["end_timestamp"] = pd.to_datetime(df["end_timestamp"], unit="s")
            dfs.append(df)

        conbined_df = pd.concat(dfs, ignore_index=True)
        conbined_df.rename(
            columns={"start_timestamp": "start_date", "end_timestamp": "end_date"},
            inplace=True,
        )

        return conbined_df
