# Getting Started
Below you will find code examples that demonstrate some of the useful methods available in the Gro API Client. This is followed by guidance on how you can best go about discovering, retrieving, and understanding data from our API Client. 

## Examples
Navigate to the [api/client/samples/](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples) folder and try executing the provided examples.

1. [quick_start.py](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/quick_start.py) is a simple script that creates an authenticated `GroClient` object and uses the `get_data_series()` and `get_data_points()` methods to find Area Harvested series for Ukrainian Wheat from a variety of different sources, and outputs the time series points to a CSV file. You will likely want to revisit this script as a starting point for building your own scripts.

Note that the script assumes you have your authentication token set to a `GROAPI_TOKEN` environment variable (see Saving your token as an environment variable). If you don't wish to use environment variables, you can modify the sample script to set `[ACCESS_TOKEN](..docs/setting-up-your-environment#retrieving-a-token)` in some other way.

```python quick_start.py```

If the API client is installed and your authentication token is set, a CSV file called `gro_client_output.csv` should be created in the directory where the script was run.

2. Try out [soybeans.py](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/crop_models/soybeans.py) to see the `CropModel` class and its `compute_crop_weighted_series()` method in action. In this example, NDVI ([normalized difference vegetation index](https://app.gro-intelligence.com/dictionary/items/321)) for provinces in Brazil is weighted against each province's historical soybean production to put the latest NDVI values into context. This information is put into a pandas dataframe, the description of which is printed to the console.

```python crop_models/soybeans.py```

3. See [brazil_soybeans.ipynb](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/crop_models/brazil_soybeans.ipynb) for a longer, more detailed demonstration of many of the API's capabilities in the form of a Jupyter notebook.

4. You can also use the included gro_client tool as a quick way to request a single data series right on the command line. Try the following:

```gro_client --metric="Production Quantity mass" --item="Corn" --region="United States" --user_email="email@example.com"```

The gro_client command line interface does a keyword search for the inputs and finds a random matching data series. It displays the data series it picked in the command line and writes the data points out to a file in the current directory called gro_client_output.csv. This tool is useful for simple queries, but anything more complex should be done using the Python packages.

Further documentation can be found in the api/client/ directory and on our wiki.

## Discovering Data
To derive the insights you want from Gro's data, you will first want to find the data you're interested in. Below you will find some of the most useful tips on how to discover the data of greatest value to you.

### Code snippets
Users may find that the Gro API is at its most powerful when used in conjunction with the Gro web application. The web app provides the most convenient format for selecting the data series that is of most interest to you. In our Add Data Series window, you can select entities of interest, and then other entities for which no data is available based on your selection will be filtered out from the remaining options. For example, after selecting the item "Corn" only metrics and regions that have data for 'Corn' will remain selectable.
![add-data-series-example](../media/add-data-series-example.png)

Once you have created a chart with data that you want, you can take advantage of our Code Snippets feature to pull that data into your API client code.

Simply click on the Chart Dropdown Button, then select Export and API Client Code Snippets. 
![code-snippet-dropdown](../media/code-snippet-dropdown.png)

Every unique data series from your chart will now be available in a client.get_data_points function for easy copying and pasting into your code or command line.
![code-snippet-copy-code](../media/code-snippet-copy-code.png)

For charts that have multiple data series, you have the option to Select all unique data series, or to select the individual series that are of greatest interest to you. 
![code-snippet-select-all](../media/code-snippet-select-all.png)

### Search
As described in the [Gro Data: Key Concepts](../docs/gro-data-key-concepts) page, a data series in Gro is a unique combination of the entities: item, metric, region, partner_region (optional), frequency, and source. To find the specific entity you would like to retrieve data for, you can use a variety of search methods. For example, `client.search` will return a list of IDs that match your search term. If you want to understand the differences between various search results, you may find the `client.search_and_lookup` method more helpful.

`client.search_and_lookup('items','Corn')` will return a list of all items that contain "corn" in their name, along with supporting information like id, name, and ids of other items contained by a given item.

Note: the above query will return a generator object. Running a query such as: 
```for result in client.search_and_lookup('items','corn'): print(result)```
should help produce a list of all the relevant information.

### Get data series
Instead of searching for all the individual entity IDs required to create a data series, the `client.get_data_series` method will return a list of all the data series available for the filters you have supplied. For example, if you are interested in Russian Oats you could use the following code to find out all the available data series that have "Oats" (item_id = 327) as the item and "Russia" (region_id = 1168) as the region:

```client.get_data_series(**{'item_id': 327, 'region_id': 1168})```

### Lookup contains
Our ontology is defined in terms of a graph, with metrics/items/regions containing others. In each case, you can see the `'contains'` property in the output of `client.lookup(type, id)`. For example:

```client.lookup('items', 10009)['contains'] ```

will return a list of items ids for items that are cereals (item_id = 10009): `[..., 274, 422, ...]`. Once you have those ids, you can use the `client.lookup()` function on each one to find more info, like their names, e.g.: `client.lookup('items', 274)['name']` will return `Corn`.

Similarly, for regions, `client.lookup('regions', 1215)[contains]` will return a list of region ids for regions that are in the US (region_id = 1215): `[13100, 13061, 13053, 13099, ....]`. And each of those can be further looked up e.g. `client.lookup('regions', 13100)` will return `{'name': 'Wisconsin', 'level': 4, 'contains': [139839, 139857, 139863, ...]}`.

### Get descendants
The Lookup Contains method can return a list of an entity's direct children. However, you may wish to discover all of the lower level regions that belong to a high level region. For this special case of traversing regions, there's a shortcut function that does it more directly and gives the option of filtering by region level: `get_descendant_regions(region_id, descendant_level)`.

Where:
```
provinces_of_brazil = client.get_descendant_regions(1029, 4)
```
will recursively look up all descendants of region 1029 (Brazil) that are of level 4 (provinces) i.e., all the provinces of Brazil. 

And: 
```
districts_of_brazil = client.get_descendant_regions(1029, 5)
```
will recursively look up all descendants of region 1029 (Brazil) that are of level 5 (districts), i.e., all the districts in all the provinces of Brazil.

For more information on region levels, please refer to the [Special properties for regions](../docs/gro-data-key-concepts#special-properties-for-regions) section of [Gro Data: Key Concepts]((../docs/gro-data-key-concepts)

### Lookup belongs
If you want to find "what entities contain the given entity?" there is a helper function, `client.lookup_belongs(type, child_id)` to does just that. For example:

`client.lookup_belongs('regions', 1215)`
will return `[{id: 15, name: 'North America', contains: [1215, 1037, ...], level: 2}, ...]`

## Retrieving Data
Once you've identified the data you want, you'll want to start retrieving it and putting it to use. The following methods should help you get the data in the format that you want.

### Get data points
`get_data_points(**selection)` is the primary method for retrieving data. The [code snippets](#code-snippets) feature covered earlier provides you with a fully completed `get_data_points` query, such as:
```# Wheat - Area Harvested (area) - India (USDA PS&D)
client.get_data_points(**{'metric_id': 570001, 'item_id': 95,'region_id': 1094, 'source_id': 14, 'frequency_id': 9})
```
The above query has completed fields for `metric_id`, `item_id`, `region_id`, `source_id`, and `frequency_id`. However, `get_data_points` can also accept fields to further narrow your data series of interest: `partner_region_id` (used only in series that represent a flow between two places), `start_date`, `end_date`, and [`show_revisions`](#show-revisions).

At a minimum, get_data_points must have a `metric_id` and a `source_id` specified. Omitting some of the default fields can help you retrieve greater amounts of data in a single query. For example, removing the `item_id` from the above query:
```client.get_data_points(**{'metric_id': 570001, 'region_id': 1094, 'source_id': 14, 'frequency_id': 9})```
Will return the Area Harvested series for all items in India as available from USDA PS&D.

Note that limiting the specificity of your selection can greatly increase the time it takes for a response to be returned.

### Data frame
Data frames are a popular format for viewing data responses, and our `gro_client` library offers you the ability to view your data series in a data frame. If you've imported the library into your file, as follows:
```
from api.client.gro_client import get_df
```
Then you can use the `get_df` method to return data in a data frame.

`get_df` is a stateful method, so you must first save the series into your client object. You can do this with the `add_single_data_series` method. 

The following code will return Wheat - Area Harvested (area) - India (USDA PS&D) in a data frame.
```
client.add_single_data_series({'metric_id': 570001, 'item_id': 95,'region_id': 1094, 'source_id': 14, 'frequency_id': 9, })
client.get_df()
```

### Show revisions
Sometimes looking at the most recent data point doesn't tell you the whole story. You may want to see if there have been any revisions to data, especially if the data is a forecast value. This standard `get_data_points` query will return the annual values for soybean yield in Argentina since 2017:
```
# Soybeans - Yield (mass/area) - Argentina (USDA PS&D)
client.get_data_points(**{'metric_id': 170037, 'item_id': 270, 'region_id': 1010, 'source_id': 14, 'frequency_id': 9, 'start_date': '2017-01-01T00:00:00.000Z'})
``` 
But the USDA begins forecasting the yield well before harvest time, and will continue to update its estimate for many months after the harvest is over. In order to see how the forecasts and estimates for each year have changed, you can include the `show_revisions` field as follows:
```
# Soybeans - Yield (mass/area) - Argentina (USDA PS&D)
client.get_data_points(**{'metric_id': 170037, 'item_id': 270, 'region_id': 1010, 'source_id': 14, 'frequency_id': 9, 'start_date': '2017-01-01T00:00:00.000Z', 'show_revisions': True})
```

## Understanding Data Responses

### Look up
If it is ever unclear what an id number represents, you can use `lookup` to get all the information you'd need. `lookup` works for any of the [data series selection entities]((../docs/gro-data-key-concepts#data-series-definition): `items`, `metrics`, `regions`, `frequencies`, `sources` and also `input_unit_id`. For example:
```client.lookup('frequencies','7')```
returns:
```{'abbrev': None, 'id': 7, 'name': 'quarterly', 'periodLength': {'months': 3}}```

```client.lookup('metrics','1480032')```
returns:
```
{'allowNegative': False,
 'allowedAggregations': '{sum,average}',
 'contains': [],
 'definition': 'The quantity of an item which has been consumed within a given country or region. Data generally refers to consumption as including any form of disappearance, such as waste, loss, and human consumption.',
 'id': 1480032,
 'name': 'Domestic Consumption (mass)',
 'rankingScore': 1}
 ```
 
```client.lookup('units', '10')```
returns:
```
{'abbreviation': 'kg',
 'baseConvFactor': {'factor': 1},
 'baseUnit': True,
 'convType': 0,
 'id': 10,
 'name': 'kilogram',
 'namePlural': 'kilograms'}
 ```
 
You can also get this information by going to the URL of the dictionary entry for individual entities in the Gro ontology, e.g. https://app.gro-intelligence.com/#/dictionary/items/270 or https://app.gro-intelligence.com/#/dictionary/regions/1309
