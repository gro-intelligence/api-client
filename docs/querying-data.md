# Querying Data
Once you've identified the data you want, you'll want to start retrieving it and putting it to use. The following methods should help you get the data in the format that you want.

## Get data points
`get_data_points(**selection)` is the primary method for retrieving data. The [code snippets](./searching-data#code-snippets) feature covered earlier provides you with a fully completed `get_data_points()` query, such as:
```py
# Wheat - Area Harvested (area) - India (USDA PS&D)
client.get_data_points(**{
    'metric_id': 570001,
    'item_id': 95,
    'region_id': 1094, 
    'source_id': 14, 
    'frequency_id': 9
})
```
The above query has completed fields for `metric_id`, `item_id`, `region_id`, `source_id`, and `frequency_id`. However, `get_data_points()` can also accept fields to further narrow your data series of interest: `partner_region_id` (used only in series that represent a flow between two places), `start_date`, `end_date`, [`show_revisions`](#show-revisions), [`insert_null`](https://gro-intelligence.github.io/api-client/development/api.html#api.client.lib.get_data_points), and [`at_time`](https://gro-intelligence.github.io/api-client/development/api.html#api.client.lib.get_data_points).

Note that limiting the specificity of your selection can greatly increase the time it takes for a response to be returned.

## Get Data frame
Data frames are a popular format for viewing data responses, and our `gro_client` library offers you the ability to view your data series in a data frame. If you've imported the library into your file, as follows:
```py
from api.client.gro_client import GroClient
```
Then you can use the `get_df()` method to return data in a data frame.

`get_df()` is a stateful method, so you must first save the series into your client object. You can do this with the `add_single_data_series()` method. 

The following code will return Wheat - Area Harvested (area) - India (USDA PS&D) in a data frame.
```py
client.add_single_data_series({
     'metric_id': 570001, 
     'item_id': 95,
     'region_id': 1094, 
     'source_id': 14, 
     'frequency_id': 9
})
client.get_df()
```

## Show revisions
Sometimes looking at the most recent data point doesn't tell you the whole story. You may want to see if there have been any revisions to data, especially if the data is a forecast value. This standard `get_data_points` query will return the annual values for soybean yield in Argentina since 2017:
```py
# Soybeans - Yield (mass/area) - Argentina (USDA PS&D)
client.get_data_points(**{
    'metric_id': 170037, 
    'item_id': 270, 
    'region_id': 1010, 
    'source_id': 14, 
    'frequency_id': 9, 
    'start_date': '2017-01-01T00:00:00.000Z'
})
``` 
But the USDA begins forecasting the yield well before harvest time, and will continue to update its estimate for many months after the harvest is over. In order to see how the forecasts and estimates for each year have changed, you can include the `show_revisions` field as follows:
```py
# Soybeans - Yield (mass/area) - Argentina (USDA PS&D)
client.get_data_points(**{
    'metric_id': 170037, 
    'item_id': 270, 
    'region_id': 1010, 
    'source_id': 14, 
    'frequency_id': 9, 
    'start_date': '2017-01-01T00:00:00.000Z', 
    'show_revisions': True
})
```
