import pandas as pd

from typing import Dict, List

from groclient.client import GroClient
from groclient import lib
from groclient.constants import V2_DATA_DESCRIPTION_PREFIX, V2_DATA_DESCRIPTION_ATTRS

class Experimental(GroClient):
    """The experimental client will introduce a range of experimental functions with better user experience.
    While you will be able to access better performance and new features at an early stage,
    you should be aware that things might change (e.g response format)."""

    def get_data_points(self, **selections: Dict) -> List[Dict]:
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

                [
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
                ]
        """
        data_stream_list = lib.get_data_points_v2_prime(
            self.access_token, self.api_host, **selections
        )

        # due to the issue in javascript when dealing with 'int64'
        # here we would manually convert timestamp from str to int
        for data_stream in data_stream_list:
            for data_point in data_stream['data_points']:
                data_point['start_timestamp'] = int(data_point['start_timestamp'])
                data_point['end_timestamp'] = int(data_point['end_timestamp'])

        return data_stream_list


    def get_data_points_df(self, **selections: Dict) -> pd.DataFrame:
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

            Returns::

                       value start_timestamp end_timestamp metric_id item_id  region_id partner_region_id frequency_id source_id unit_id
                0  33.204651      2021-12-20    2021-12-21   2540047    3457  100023971               NaN            1        26      36
                1  32.734329      2021-12-20    2021-12-21   2540047    3457  100023990               NaN            1        26      36
        """
        res = lib.get_data_points_v2_prime(
            self.access_token, self.api_host, **selections
        )

        v2_data_description_meta = [
            [V2_DATA_DESCRIPTION_PREFIX, x] for x in V2_DATA_DESCRIPTION_ATTRS
        ]
        df = pd.json_normalize(
            res, record_path=['data_points'], meta=v2_data_description_meta, errors='ignore'
        )

        if not df.empty:
            ts_cols = ["start_timestamp", "end_timestamp"]
            df[ts_cols] = df[ts_cols].apply(pd.to_datetime, unit="s")

            df.columns = df.columns.str.replace('series_description.', '')
            df[V2_DATA_DESCRIPTION_ATTRS] = df[V2_DATA_DESCRIPTION_ATTRS].apply(pd.to_numeric)

        return df
