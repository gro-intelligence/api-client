<p align="center"><img width=8% src="https://gro-intelligence.com/images/logo.jpg"></p>

# Prevent Plant Model for US Corn and Soybeans Using Gro

## Goal & Process
Basic Model Description: The prevent plant model endeavors to forecast prevent plant area for corn and soybeans at the county level. Using datasets in Gro, the model will examine the overall wetness across all Corn and Soybean Belt counties using soil moisture, rainfall, planting progress reports, and historical prevented plant area. 

Prevented plant is the area farmers intended to plant, but were unable to, typically because of extreme weather. Farmers are entitled to a payout from revenue-insurance contracts if the ground remains unplanted (for more information see https://www.rma.usda.gov/Topics/Prevented-Planting)

## Model Inputs
__Corn Prevent Plant Model Inputs:__ 

[SMOS Soil Moisture](https://app.gro-intelligence.com/dictionary/sources/43)
* __Model Specific Data:__ Weekly averages for soil moisture by county for the US Corn Belt. 

[Tropical Rainfall Measuring Mission (TRMM)](https://app.gro-intelligence.com/dictionary/sources/35)
* __Model Specific Data:__ Weekly cumulative precipitation by county for the US Corn Belt. 

[USDA NASS](https://app.gro-intelligence.com/dictionary/sources/25)
* __Model Specific Data:__ The weekly progress report for corn planted for the US Corn Belt. The report measures area planted as a percentage of the intended area. Data is measured on a state level and applied to each county in the model. 

[USDA FSA](https://app.gro-intelligence.com/dictionary/sources/100)
* __Model Specific Data:__ “Area prevented, non-irrigated” data to determine acres that have not been planted in the current crop year due to an inability to plant the crop. The final prevent plant number, released by the FSA in January, is what the model is predicting. 
Latitude and Longitude 
* County level locations for relevant counties being modeled, which can be found using an API function in Gro.

__Soybean Prevent Plant Model Inputs:__ 

*Note, in addition to inputs used for the corn model, the soybean model includes the following:*

Corn Prevent Plant Model Output
* __Model Specific Data:__ The corn model output provides the amount of acreage prevented in a given area, which influences the decision to plant soybeans.  

[Gridded Soil Survey Geographic Database (gSSURGO)](https://app.gro-intelligence.com/dictionary/sources/87)
* __Model Specific Data:__ Soil characteristics such as soil water storage, soil organic carbon stock, crop productivity index for corn and soybeans.

## Methodology
__Corn Model Methodology:__
* Compute weekly averages for soil moisture and weekly cumulative precipitation by county across the Corn Belt.
* Test cumulative soil moisture and weekly precipitation signals from week 14 (beginning of April) to the current week along with planting progress using XGBoost or Grandient Boosting regressor. Weeks are defined by the planting progress date. 
* Backtest the signals from 2011-2018, which covers available prevented planting data.
* Latitude and longitude are used to measure the exact location of each county modeled using an API function in Gro.

__Soybean Model Methodology:__

*Note, in addition to the corn model methodology, the soybean model includes the following:* 

* Test weekly soil moisture (average) and precipitation (cumulative) from week 16 (second half of April) to the current week along with planting progress and soil characteristics using XGBoost or Grandient Boosting regressor. 
* Incorporation of soil characteristics such as soil water storage, soil organic carbon stock, crop productivity index for corn and soybeans.

## Future Improvements
*The current model primarily utilizes realized weather to make a prediction about a very complicated decision to take prevented plant insurance.*
* GFS weather forecasts are being tested to enhance predictive power for a given point in the season.
* Non-weather based factors, such as crop and input economics, should be tested and included.
