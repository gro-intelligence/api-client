# Data Point Definition

Gro defines a "data point" as a discrete result produced by our API. When using the `get_data_points()` function, you are returned an array of points, each of which is a Python dictionary object that looks something like:

```py
{ 'start_date': '2013-02-04T00:00:00.000Z',
  'end_date': '2013-02-04T00:00:00.000Z',
  'value': 0.131714797651,
  'unit_id': 851,
  'reporting_date': None,
  'metric_id': 15531082,
  'item_id': 7382,
  'region_id': 138295,
  'frequency_id': 1 }
```

For example, if you requested NDVI for Bureau county, Illinois, for a particular 8-day time period, the Gro API would yield a single response that would count as a single data point. Even though the value is computed from tens of thousands of underlying pixels, the API response counts as a single point because we are returning the value at the county (aka district) level.

Another example is if you get weekly precipitation data for a given region in a given week, you will get a single point. On the other hand, if you get daily precipitation for a given region for a period of a week, you will get seven data points.

Below are some explanations of what each of those fields represent:

* `start_date`: beginning of the period this point represents
* `end_date`: end of the period this point represents
* `value`: the value, typically a number. In some cases, the value may be non-numeric. E.g., when the metric is Crop Calendar, a value of "planting," represents the fact that the planting period is from `start_date` to `end_date`.
* `unit_id`: this is a Gro unit id you can look up the name/abbreviation/etc. of using the `client.lookup('units', unit_id)` function. There's also a helper function of which you can see an example in the [quickstart](https://github.com/gro-intelligence/api-client/blob/9c2c17642980b5415b8a8167a28276b77e34915c/api/client/samples/quick_start.py#L30) for getting just the abbreviation from the unit id, `client.lookup_unit_abbreviation(point['unit_id'])`, which is the common case you probably want
* `reporting_date`: date the source reported this value (only included when source provides reporting date)
* `metric_id`: unique id for the metric (i.e. "Export Value (currency)") you selected - get more details (name, definition, ...) using `client.lookup('metrics', metric_id)`
* `item_id`: unique id for the item (i.e., "Corn") you selected - get more details (name, definition, ...) using `client.lookup('items', item_id)`
* `region_id`: unique id for the region (i.e., "United States") you selected - get more details (name, administrative level, ...) using `client.lookup('regions', region_id)`
* `frequency_id`: unique id for the frequency (i.e., "annual") you selected - get more details (name, abbreviation, period length, ...) using `client.lookup('frequencies', frequency_id)`
