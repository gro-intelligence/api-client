# Data Series Definition

Gro defines a "data series" as a series of data points over time.
Each data series is defined by a unique selection of:

* `metric`
* `item`
* `region`
* `partner_region` (optional)
* `frequency`
* `source`

For example, if you select `item=Wheat`, `metric=Production Quantity (mass)`, `region=India`, `frequency=Annual`, `source=FAO`, that would be one data series. Partner_region is optional and used only in series that represent a flow between two places, e.g. if the metric is exports, the region would be the exporter and the partner_region would be the importer.

To get all the available data series for a given selection of entities, use the `get_data_series` function as described in the [Searching Data](./searching-data.html#get-data-series) section.
