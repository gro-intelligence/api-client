## Similar Regions

Gro's expansive data covers regions across the entire world. This depth of data enables powerful comparisons and contrasts between individual districts or even entire countries. This Similar Regions application offers a simple approach for quickly computing similarities between selected regions.

Calling two regions “similar” is, of course, a fuzzy term and presupposes a lot of assumptions about what can be considered similar. Working in the context of agriculture, key factors affecting similarity between two regions can commonly be recognized as temperature, rainfall, and soil moisture, among many others.

To showcase one such approach, suppose you were interested in finding all the “similar” regions to a given region `a`. This Similar Regions application will evaluate how similar `a` is to each region in a given set of regions `B`. The application will then return an ordered list of `B`. The properties used to compare `a` with `B` are by default temperature, soil moisture, and rainfall but these can be changed to any of the available metrics in Gro.

### Implementation/Technical Details:

For a general technical overview of the approach taken, please take a read through the blog post available here: [TODO: insert blog post link]. 

### Usage:

#### Interactively:

Suppose we want to get the 10 US states that are most similar to Wisconsin.  We will run SimilarRegions restricted to US states only. 

```
>>> from api.client.samples.similar_regions.region_properties import region_properties
>>> from api.client.samples.similar_regions.similar_region import SimilarRegion
>>>
>>> WISCONSIN_REGION_ID = client.search_for_entity('regions', 'Wisconsin')
>>> USA_REGION_ID = client.search_for_entity('regions', 'United States of America')
>>> US_STATES_IDS = [province['id'] for province in client.get_descendant_regions(USA_REGION_ID, 4)]
>>>
>>> sim = SimilarRegion(region_properties, regions_to_compare=US_STATES_IDS)
>>> for result in sim.similar_to(WISCONSIN_REGION_ID, number_of_regions=10, requested_level=4):
        print(result)
```

The fourth line (constructing the SimilarRegion object) will take some time depending on the amount of cached data and the number of regions you’ve specified. The output should show you that the region most similar to Wisconsin is of course, Wisconsin, and then a number of other similar states. 

Now suppose we wanted to expand our search to all provinces in the world. In that case, we just omit regions_to_compare, but we still leave the region level as `4`.  Constructing the SimilarRegion object will now take even longer since the model is getting data for the whole world.  

```
>>> sim = SimilarRegion(region_properties)
>>> for result in sim.similar_to(WISCONSIN_REGION_ID, 10, 4):
        print(result)
```

If we wanted to compare it to countries instead of provinces we would change the region_level from `4` to `3`, and for  districts we would use region level `5`. 

#### Programmatically:

Incorporate Similar Regions into your own python code with ease. Similarly to above, you simply must import the library and specify the region properties to be used in the comparison. Please take a look at the “find_similar_regions.py” file for an intuitive but simple example of such an integration, or run the following example:

`python find_similar_regions.py  --region_id=13101`

### Region Properties:

The file region_properties.py defines the properties we are using to compare the regions. It is by default defined to be Temperature, Rainfall and Soil Moisture. These three indices were picked because of their huge geographic availability (almost the entire world is covered). Feel free to explore other available item/metric combinations on the Gro web app and add these to the region_properties.py to have them be used. 

The format of a new property is as follows:

```
"property_name": {
   "selected_entities": {
       'metric_id': metric_id_of_property,
       'item_id': item_id_of_property,
       'frequency_id': frequency_of_property,
       'source_id': source_id_of_property
   },
   "properties": {
       "num_features": [0-n],
       "longest_period_feature_period": [0-length_of_series],
       "weight": [0-1],
       "weight_slope": Bool
   }
}
```

**num_features** defines the number of features to extract from the timeseries. Currently, a fourier transform extracts these features, so num_features defines the number of fourier coefficients to use in the comparison.

**longest_period_feature_period** defines what we think the longest period features we might see are. For most properties we expect these to have yearly trends at the lowest frequency. So if this is a daily property, this number should be set to 365 (the longest periodicity we expect in the data is 365 days).

**weight** defines the weight to assign this property in the similarity computation. If this value is 0, the property is ignored. If it’s 1, it’s at the maximum weighting. Changing this value will not invalidate the cache. 

**weight_slope** defines whether or not to weight later coefficients lower than earlier coefficients. The intuition behind this is that lower frequency signals (seasonal trends, for instance) will be more important in a similarity comparison than very high frequency signals (e.g. daily small temperature fluctuations). 
