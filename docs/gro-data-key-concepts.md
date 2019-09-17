# Gro Data: Key Concepts

1. [Gro Ontology](#gro-ontology)
2. [Data Series Definition](#data-series-definition)
3. [Data Point Definition](#data-point-definition)

## Gro Ontology
Gro has brought the world of agricultural data into a single ontology. This ontology classifies all data into a limited set of entities. 

The entity types around which the data is organized in Gro are:

* items -- what the data is about (e.g., Rice, Sugar, Rainfall, etc.).
* metrics -- how the data is measured (e.g., Production, Precipitation, etc.).
* regions -- where the data is from/about (e.g., a country, a weather station, a city etc.). Some data such as trade flows might have a partner region.
* frequencies -- e.g., daily, weekly etc.
* sources -- the organization or sub-organization that generates the data (e.g., USDA PS&D).
* units -- the units in which the data is presented (e.g., tonnes, liters, etc.).

### Entity fields
Each specific entity will have an `id`, `name`, and various other properties. For example, "Soybeans" is a specific item with `id = 270` and the following information
```py
{'allowedAggregations': None,
 'contains': [1737,
  7401,
  7578,
  7579,
  5136,
  5021,
  5135,
  5137,
  12418,
  5776,
  5777,
  3035,
  3036,
  9312,
  9284,
  6330,
  7577,
  12728,
  12729,
  12730,
  12731,
  12732,
  12733,
  12734,
  12735,
  12736,
  12737,
  10134],
 'definition': 'The seeds and harvested crops of plants belonging to the species <i>Glycine max</i> that are used in the production of oil and both human and livestock consumption.',
 'id': 270,
 'name': 'Soybeans',
 'rankingScore': 2.204}
```
IDs are unique within a particular entity type, i.e., there's only one item with id = 270.

The above information can be retrieved using the client.search function:
```client.lookup('items', 270)```

[See this Getting Started section for help on finding entities by name or by id.](../docs/getting-started.html#look-up)

### Entity Relationships: Contains
Items, metrics, and regions have a property called `contains`, which is an array of the other entities that it contains, or that belong to it. For example, the item "Cereals" contains the items "Wheat," "Corn," etc.

Variations of the `client.lookup(type, id)` function can help you understand what a given entity contains or belongs to. For example:
```client.lookup('items', 10009)['contains']```
Will return a list of items that are contained within the item "Cereals" (item_id: 10009).

```client.lookup_belongs('regions', 13055)```
Will return a list of regions to which "California" (region_id: 13055) belongs.

[See this Getting Started section for navigation of relationships between entities.](../docs/getting-started.html#lookup-contains)

### Special Properties for Regions
The following properties exist for regions only:

#### `level`
Region level corresponds to the administrative level of the region:

* level 1: world
* level 2: continent
* level 3: country
* level 4: provinces
* level 5: districts
* level 6: city
* level 7: market
* level 8: other arbitrary regions
* level 9: point-location

#### `latitude` and `longitude`
For point-locations (i.e., region level 9), these properties correspond to the location's coordinates. More generally for other regions, these properties are optional, but if specified, they correspond to the coordinates of the geographic center of the region.

## Data Series Definition
Gro defines a "data series" as a series of data points over time.
Each data series is defined by a unique selection of:

* `item`
* `metric`
* `region`
* `partner_region` (optional)
* `frequency`
* `source`

For example, if you select `item=Wheat`, `metric=Production Quantity (mass)`, `region=India`, `frequency=Annual`, `source=FAO`, that would be one data series. Partner_region is optional and used only in series that represent a flow between two places, e.g. if the metric is exports, the region would be the exporter and the partner_region would be the importer.

To get all the available data series for a given selection of entities, use the `get_data_series` function as described in the [FAQ](../docs/faqs.md###Q:-how-do-I-get-data-series?).

## Data Point Definition
Gro defines a "data point" as a discrete result produced by our API. When using the `get_data_points()` function, you are returned an array of points, each of which is a Python dictionary object that looks something like:
```py
{
  u'input_unit_scale': 1,
  u'region_id': 1038,
  u'end_date': u'2000-12-31T00:00:00.000Z',
  u'input_unit_id': 17,
  u'value': 0.2623,
  u'frequency_id': 9,
  u'item_id': 5187,
  u'reporting_date': None,
  u'start_date': u'2000-01-01T00:00:00.000Z',
  u'metric_id': 5590032
}
```

For example, if you requested NDVI for Bureau county, Illinois, for a particular 8-day time period, the Gro API would yield a single response that would count as a single data point. Even though the value is computed from tens of thousands of underlying pixels, the API response counts as a single point because we are returning the value at the county (aka district) level.

Another example is if you get weekly precipitation data for a given region in a given week, you will get a single point. On the other hand, if you get daily precipitation for a given region for a period of a week, you will get seven data points.

Below are some explanations of what each of those fields represent:

* `start_date`: beginning of the period this point represents
* `end_date`: end of the period this point represents
* `reporting_date`: date the source reported this value (only included when source provides reporting date)
* `value`: the value, typically a number. In some cases, the value may be non-numeric. E.g., when the metric is Crop Calendar, a value of "planting," represents the fact that the planting period is from `start_date` to `end_date`.
* `unit_id`: this is a Gro unit id you can look up the name/abbreviation/etc. of using the `client.lookup('units', unit_id)` function. There's also a helper function of which you can see an example in the [quickstart](https://github.com/gro-intelligence/api-client/blob/9c2c17642980b5415b8a8167a28276b77e34915c/api/client/samples/quick_start.py#L30) for getting just the abbreviation from the unit id, `client.lookup_unit_abbreviation(point['unit_id'])`, which is the common case you probably want
* `metric_id`: unique id for the metric (i.e. "Export Value (currency)") you selected - get more details (name, definition, ...) using `client.lookup('metrics', metric_id)`
* `item_id`: unique id for the item (i.e., "Corn") you selected - get more details (name, definition, ...) using `client.lookup('items', item_id)`
* `region_id`: unique id for the region (i.e., "United States") you selected - get more details (name, administrative level, ...) using `client.lookup('regions', region_id)`
* `frequency_id`: unique id for the frequency (i.e., "annual") you selected - get more details (name, abbreviation, period length, ...) using `client.lookup('frequencies', frequency_id)`
