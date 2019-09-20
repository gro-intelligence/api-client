<p align="center"><img width=8% src="https://gro-intelligence.com/images/logo.jpg"></p>

# Brazil Soybean Crop Model: Basic Yield Forecasting Using Gro

## Goal & Process
Basic Model Description: The Brazil soybean crop model offers a simple framework for forecasting yield that uses a relatively small number of inputs and produces reasonably accurate estimates (1% in-sample error rate).

Using historical yield, production quantity, and NDVI data from within Gro, this model develops a weighting of national soybean production by each province, and weighted national NDVI by each province, to build a basic picture of soybean crop health.

## Model Inputs
[GIMMS MODIS NDVI](https://app.gro-intelligence.com/dictionary/sources/3)
* __Model Specific Data:__ 8-day averages for soil moisture by county for Brazil’s corn-producing areas.

[FAO](https://app.gro-intelligence.com/dictionary/sources/2), [PS&D](https://app.gro-intelligence.com/dictionary/sources/14), and [IGC](https://app.gro-intelligence.com/dictionary/sources/19)
* __Model Specific Data:__ Annual soybean yields at the national level.

[IBGE](https://app.gro-intelligence.com/dictionary/sources/114) and [CONAB](https://app.gro-intelligence.com/dictionary/sources/73)
* __Model Specific Data:__ May be used to determine weighting of each province’s contribution to national soybean production.

## Methodology
* Generate a full history of national-level soybean yield for Brazil.
* Compute the “weight” of each province as the average fraction of soybean production.
* Train a regression model to fit the crop-weighted average of NDVI  to national crop yield.
* Based on the results of the previous steps, use current-season NDVI values to forecast yield.
