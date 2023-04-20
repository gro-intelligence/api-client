from groclient.client import GroClient
from groclient import lib


class Experimental(GroClient):
    """The experimental client will introduce a range of experimental functions with better user experience.
    While you will be able to access better performance and new features at an early stage,
    you should be aware that things might change (e.g response format)."""

    def get_data_points(self, **selections):
        """This function is a mirror of existing :meth:`~groclient.GroClient.get_data_points`, but with limited scope.

        For example:

        - Ontology expansion is under development.

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
        coverage_threshold: float, optional
            Custom threshold on the coverage of geospatial data. Value should be between 0 and 1.

        Returns
        -------
            dict
                dictionary containing list of data_points and series_description

        Example::

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
        return lib.get_data_points_v2_prime(
            self.access_token, self.api_host, **selections
        )
