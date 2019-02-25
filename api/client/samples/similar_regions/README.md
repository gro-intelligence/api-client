## Similar Regions

Gro's expansive data covers regions across the entire world. This depth of data enables powerful comparisons and contrasts between individual districts or even entire countries. This Similar Regions application offers a simple approach for quickly computing similarities between selected regions.

Calling two regions “similar” is, of course, a fuzzy term and presupposes a lot of assumptions about what can be considered similar. Working in the context of agriculture, key factors affecting similarity between two regions can commonly be recognized as temperature, rainfall, and soil moisture, among many others.

To showcase one such approach, suppose you were interested in finding all the “similar” regions to a given region `a`. This Similar Regions application will evaluate how similar `a` is to each region in a given set of regions `B`. The application will then return an ordered list of `B`. The properties used to compare `a` with `B` are by default temperature, soil moisture, and rainfall but these can be changed to any of the available metrics in Gro.

### Implementation/Technical Details:

For a general technical overview of the approach taken, please take a read through the blog post available here: [TODO: insert blog post link]. 

### Usage:

#### Interactively:

To use in the Python REPL:

```
>>> from api.client.samples.similar_regions.region_properties import region_properties
>>> from api.client.samples.similar_regions.similar_region import SimilarRegion
>>> USA_STATES = [13100, 13061, 13053, 13099, 13069, 13091, 13076, 13064, 13060, 13101, 13057, 13067, 13077, 13056, 13065, 13093, 13097, 13059, 13054, 13062, 13070, 13055, 13071, 13080, 13052, 13079, 13089, 13075, 13058, 13072, 13051, 13087, 13082, 13088, 13092, 13074, 13068, 13095, 13085, 13078, 13066, 13090, 13063, 13086, 13084, 13083, 13098, 13081, 13096, 13094, 13073]
>>> sim = SimilarRegion(region_properties, regions_to_compare=USA_STATES)
>>> for result in sim.similar_to(13100, 5, 4):
        print(result)
```

The fourth line (constructing the SimilarRegion object) will take some time depending on the amount of cached data and the number of regions you’ve specified. The output should show you that the closest state to Wisconsin is of course, Wisconsin, and then a number of other similar states. 

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
