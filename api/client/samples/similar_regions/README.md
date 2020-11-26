# Similar Regions

Gro's expansive data covers regions across the entire world. This enables powerful comparisons and contrasts between regions at many levels of granularity. The Similar Regions application offers an approach for finding regions that are most similar to a particular seed region, in terms of agricultiral potential.

Suppose you are interested in finding regions “similar” to a given region `a`. For example `a` may be a district that is known to have success growing a particular crop, and you want to find regions that would be most suitable for the same crop in another part of the world.  You can use this application to evaluate how similar `a` is to each region in a another set of regions `B` and get a ranked list of the regions in `B`.

## Data and method

Calling two regions “similar” is, of course, a fuzzy term and presupposes a lot about what matters. Here we are interested in the fundamental agricultural potential of the land. Thus the comparisons use data related to the climate and the soil.

By default we use daily Land Surface Temperature, Rainfall, Soil Moisture and 7 static soil properties (acidity, organic carbon content, clay, silt, sand, water capacity, and cation exchange). This is specified in `metric_properties` and `metric_weights` dictionaries in [metric.py](metric.py). Feel free to explore other available item/metric combinations on the Gro web app and add them.

This data is used to place the regions in a high-dimensional metric space where the distance indicates similarity.  These distances are used for ranking region similarity, but should not be interpreted in a "physical" sense. In particular, no linearity of the underlying space should be assumed. For example, a pair of regions at double the distance compared to some other pair should not be interpreted as "twice less similar".

## Data volume and cache

This application may use a lot of data from the Gro API depending on the search area and granularity, e.g. up to ~1 billion data points when working at the district level for the whole world. Setting a persistent local cache via `data_dir` is highly recommended to avoid unnecessary repeat downloads from the Gro API. The cache will incrementally update on each run if additional data is needed for e.g. new regions or metrics. To force a re-download of all data, delete the files in data_dir or use a different directory.

## Usage

### Interactively

Suppose we want to get the 10 US states that are most similar to Wisconsin.  We will run SimilarRegions restricted to US states only.

```
>>> from api.client.samples.similar_regions.similar_region import SimilarRegion
>>> from api.client.samples.similar_regions.metric import metric_properties, metric_weights
>>>
>>> WISCONSIN_REGION_ID = client.search_for_entity('regions', 'Wisconsin')
>>> USA_REGION_ID = client.search_for_entity('regions', 'United States of America')
>>>
>>> sim = SimilarRegion(metric_properties, data_dir='/tmp/similar_region_cache', metric_weights=metric_weights)
>>> for result in sim.similar_to(WISCONSIN_REGION_ID, compare_to=USA_REGION_ID, number_of_regions=10, requested_level=4):
	print(result)
```

The call to `similar_to` will take some time depending on the amount of cached data and the number of regions you’ve specified. The output should show you that the region most similar to Wisconsin is of course, Wisconsin, and then a number of other similar states.

### Programmatically:

Incorporate Similar Regions into your own python code with ease. Similarly to above, you simply must import the library and specify the region properties to be used in the comparison. Please take a look at the “find_similar_regions.py” file for an intuitive but simple example of such an integration, or run the following example:

`python find_similar_regions.py  --region_id=13101 --compare_to=1215 --region_level=4 --data_dir=/tmp/similar_regions_cache`

## Specifying regions

Regions can be districts, provinces, countries, continents, or even the whole world. You can find region ids to use by browsing the [regions in the Gro dictionary](https://app.gro-intelligence.com/dictionary/regions/0) or by exploring data series in [Gro](https://app.gro-intelligence.com), the web app.  Besides region ids, you will also need to know the [region levels defined in the Gro ontology](https://developers.gro-intelligence.com/gro-ontology.html#special-properties-for-regions).

If we wanted to compare Wisconsin to provinces in [Europe](https://app.gro-intelligence.com/dictionary/regions/14) instead of the [USA](https://app.gro-intelligence.com/dictionary/regions/1215), we would use `compare_to=14`.

To expand our search to all provinces in the world, we would just omit compare_to, but we still leave the region level as `4`.  This will now take longer since the model is getting data for the ~3.5k provinces in the whole world (instead of just 50 states), which takes about 30 minutes on a ~100Mbps  internet connection.

If we wanted to compare it to countries instead of provinces we would change the region_level from `4` to `3`, and for districts we would use region level `5`.

If`compare_to=0` (the whole world), and `requested_level=5` (districts), it will get 20+ years of daily data for 3 data series, plus 7 static data series, for ~45k regions, which is approximately *1 billion data points*. This takes up to 3 hours on a ~100Mbps internet connection.


