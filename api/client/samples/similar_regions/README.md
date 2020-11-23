## Similar Regions

Gro's expansive data covers regions across the entire world. This depth of data enables powerful comparisons and contrasts between individual districts or even entire countries. This Similar Regions application offers a simple approach for quickly computing similarities between selected regions.

Calling two regions “similar” is, of course, a fuzzy term and presupposes a lot of assumptions about what can be considered similar. Working in the context of agriculture, key factors affecting similarity between two regions can commonly be recognized as temperature, rainfall, and soil moisture, among many others.

To showcase one such approach, suppose you were interested in finding all the “similar” regions to a given region `a`. This Similar Regions application will evaluate how similar `a` is to each region in a given set of regions `B`. The application will then return an ordered list of `B`. The properties used to compare `a` with `B` are by default temperature, soil moisture, and rainfall and a number of soil properties, but these can be changed to any of the available metrics in Gro.

### Usage:

#### Interactively:

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

The fourth line (the call to similar_to) will take some time depending on the amount of cached data and the number of regions you’ve specified. The output should show you that the region most similar to Wisconsin is of course, Wisconsin, and then a number of other similar states.

If we wanted to compare Wisconsin to provinces in Europe instead of the USA, we would use `compare_to=14`.

To expand our search to all provinces in the world, we would just omit compare_to, but we still leave the region level as `4`.  This will now take longer since the model is getting data for the ~3.5k provinces in the whole world (instead of just 50 states), which takes about 30-45 minutes on a ~100Mbps  internet connection.

If we wanted to compare it to countries instead of provinces we would change the region_level from `4` to `3`, and for  districts we would use region level `5`.

If `compare_to=0` (the whole world), and `requested_level=5` (districts), it will get 20+ years of daily data for 3 data series, plus 7 static data series, for ~45k regions, which is approximately *1 billion data points*. This takes up to 3 hours on a ~100Mbps internet connection.


#### Programmatically:

Incorporate Similar Regions into your own python code with ease. Similarly to above, you simply must import the library and specify the region properties to be used in the comparison. Please take a look at the “find_similar_regions.py” file for an intuitive but simple example of such an integration, or run the following example:

`python find_similar_regions.py  --region_id=13101 --data_dir=/tmp/similar_regions_cache`

### Data used in the comparison:

The file metric.py defines the properties we are using to compare the regions, via the `metric_properties` and `metric_weights` dictionaries. By default we use daily Land Surface Temperature, Rainfall, Soil Moisture and 7 static soil properties  such as soil acidity, organic carbon content, etc. These were picked because they are fundamental properties relevant to the agricultural potential of the region. Feel free to explore other available item/metric combinations on the Gro web app and add these to metric.py.

### Data volume and cache:

This application uses a lot of data from the Gro API, up to ~1 billion data points in some cases as noted above. Setting a persistent local cache via `data_dir` is highly recommended to avoid unnecessary repeat downloads from the Gro API.