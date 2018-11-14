# If you're running the first time, run these three lines. Alternatively download the pre-computed version from
# here:
from api.client.similar_regions.nearest_region import SimilarRegion

testCase = SimilarRegion(["soil_moisture", "rainfall", "land_surface_temperature"])
# testCase._cache_regions()

# Otherwise, comment the three lines above and uncomment this line
testCase.state.load()

# If you want to modify weights, uncomment below
testCase.state.metric_weights = {
    "soil_moisture": 1.0,
    "rainfall": 1.0,
    "land_surface_temperature": 1.0
}

testCase.similar_to(11193, number_of_regions=150, requested_level=5, csv_output=True)
