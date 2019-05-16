# Sample Scripts

## Basic Functionality (GroClient)

If in doubt, use GroClient. Base class others extend.

1. quick_start.py
2. snippets.py
3. search.py

## Crop Models (CropModel)

Extension of GroClient which adds a crop_weighted function.

1. cash_crops.py (stateful)
2. france_corn.py (stateless)
3. soybeans.py (crop weighted)

## Batch Queries (BatchClient)

The BatchClient class uses concurrency to send queries simultaneously rather than one at a time.

1. batch_queries.py

## Similar Regions

See the Similar Regions [README](similar_regions/README.md).

1. find_similar_regions