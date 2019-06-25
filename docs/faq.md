# FAQ

##Exploring What's Available

### Q: How do I figure out what an id refers to?
Most of our API inputs and outputs are in terms of unique entity ids, paired with a "type" (metrics/items/regions/frequencies/sources/units).

To look up information about an entity programmatically, you can use the `client.lookup(type, id)` function to find more information about the given entity, including its name, a definition if relevant, a region level if it's a region, a conversion factor if it's a unit, what other entities this entity contains if it is a group, etc.

For example:
`client.lookup('regions', 12545)`

Returns:
```{'contains': [132146,
  132151,
  ...
  132143,
  132155],
 'id': 12545,
 'latitude': -28.7101,
 'level': 4,
 'longitude': 30.7255,
 'name': 'KwaZulu-Natal',
 'rankingScore': 1}
 ```

You can also get it by going to the URL of the dictionary entry for individual entities in the Gro ontology, e.g. https://app.gro-intelligence.com/#/dictionary/items/270 or https://app.gro-intelligence.com/#/dictionary/regions/13094

### Q: How do I know which ids to use?
You can use the `client.search(type, search_terms)` function to enter in the name of what you're interested in and find relevant ids. Search words across items, metrics, regions and sources.

### Q: How do I get data series?
Use `client.get_data_series(selections)` and provide at least one id you've already identified you're interested in to narrow down what combinations of possible data series are available for the given selection(s).

For example, if you wanted to see what data series are available from UKRSTAT (`'source_id': 93`) for Ukraine (`'region_id': 1210`), you could query:
```client.get_data_series(**{
	'region_id': 1210,
	'source_id': 93})
```

Alternatively, the recommended method is to use the web application at app.gro-intelligence.com to explore what data is available and use the API Code Snippets found in the "More Information" panel of any result or completed chart to export the id(s) into your code. This provides the same info you could get programmatically using `client.search()` and `client.get_data_series()`, but it can be easier to explore graphically what combinations are available.

### Q: Why is it that when I use client.search() to find metrics/items/regions I'm interested in, sometimes client.get_data_series() doesn't have any data for those metrics/items/regions?
`client.search()` provides a way to search across everything we have identified and defined in our ontology. Sometimes, data doesn't exist for a particular result for a number of reasons, most commonly because we may have defined new entries in preparation for an incoming source which is undergoing testing. `client.get_data_series()` will tell you what data is actually available. You can intersect the results from those two functions to find things programmatically, or you can use the web application at app.gro-intelligence.com to explore what data is available, intersected already.

### Q: Is it possible to find out how entities are related to each other? Like Missouri is a province of the US, Buenos Aires belongs to Argentina, Corn is a Cereal, etc.?
Yes. Our ontology is defined in terms of a graph, with metrics/items/regions containing others. In each case, you can see the `'contains'` property in the output of `client.lookup(type, id)`. For example:

```client.lookup('items', 10009)['contains']``` 
will return a list of items ids for items that are cereals: `[..., 274, 422, ...]`. Once you have those IDs, you can use the `client.lookup()` function on each one to find more info, like their names, e.g.: `client.lookup('items', 274)['name']` will return `Corn`.

Similarly, for regions, `client.lookup('regions', 1215)['contains']` will return a list of region ids for regions that are in the US: `[13100, 13061, 13053, 13099, ....]`. And each of those can be further looked up e.g. `client.lookup('regions', 13100)` will return `{'name': 'Wisconsin', 'level': 4, 'contains': [139839, 139857, 139863, ...]`

If you want to go the other way and find "what entities contain the given entity?" there is a helper function, `client.lookup_belongs(type, child_id)` to do just that. For example:

```client.lookup_belongs('regions', 1215)```
will return `[{id: 15, name: 'North America', contains: [1215, 1037, ...], level: 2}, ...]`

### Q: Is there a shortcut to get all the countries in a continent, or the districts in a country?
For the special case of traversing regions, there's a shortcut function that does it more directly and gives the option of filtering by region level

provinces_of_brazil = client.get_descendant_regions(1029, 4)
districts_of_brazil = client.get_descendant_regions(1029, 5)
This will recursively lookup all descendants of region 1029 (Brazil) that are of level 4 (provinces) i.e. all the provinces of Brazil, and level 5, i.e. all the districts in all the provinces of Brazil.

### Q: What does 'sourceLag' mean when I use client.lookup() to inspect a source's details?
Source lag is defined as the worst normal case scenario in regards to how long a source might report data after a point's end date. In other words, a source lag of 1 month would mean that an annual source might report the 01/01/2017-12/31/2017 data point on 02/01/2018 at the latest. Occasional extraordinary delays do occur from time to time, such as in a government shutdown or satellite data center malfunctions, but in general the data is expected to be updated by the endDate of the point + the sourceLag.

## Data Retrieval

### Q: How do I see previous values for a time-series point to see how the value changed over time?
You can add 'show_revisions': True to your client.get_data_points() input object. Now, if the source provides revisions, you may see multiple different points for the same start_date and end_date which have different reporting_dates. Without the show_revisions: True flag, only the point with the latest reporting_date is returned.

### Q: I specified an end_date when calling get_data_points(), but I am getting points with other end_dates:
start_date and end_date behave as ranges. Specifying end_date is interpreted as "all points with an end date prior to this date" and start_date is "all points with a start_date later than this date." Both can be specified to narrow down the range.

### Q: How do I know what unit the data is in?
Please see the "input_unit_id" and "input_unit_scale" sections on the Data Point Field Definitions page for more information.

## Account
Q: I tried using my Gro username and login but am getting a 401 Unauthorized error
A Gro account gives you access to the web application at app.gro-intelligence.com. API access is sold as an add-on product you need to be activated for. To learn more about getting an API account, contact our sales team using the link at gro-intelligence.com/products/gro-api

## Gro Models
### Q: Do your predictive models only run during the crop season?
We provide predictions year around (always for the current market year, so for US it is also always the current calendar year). Take the US for an example: before planting ends (Jan to May) we predict at country level with long term trend. Between planting and harvesting (May to Oct) we predict at district level with daily updates. After harvesting until the end of the year, we only adjust the previous predictions if there is any adjustment from the sources that we used for the in-season predictions.