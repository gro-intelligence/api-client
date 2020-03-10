# FAQ

## Exploring What's Available

### Q: Why is it that when I use client.search() to find metrics/items/regions I'm interested in, sometimes client.get_data_series() doesn't have any data for those metrics/items/regions?
`client.search()` provides a way to search across everything we have identified and defined in our ontology. Sometimes data doesn't exist for a particular result for a number of reasons, most commonly because we may have defined new entries in preparation for an incoming source which is undergoing testing. `client.get_data_series()` will tell you what data is actually available. You can intersect the results from those two functions to find things programmatically, or you can use the web application at <app.gro-intelligence.com> to explore what data is available, intersected already.

### Q: What does 'sourceLag' mean when I use client.lookup() to inspect a source's details?
Source lag is defined as the worst normal case scenario in regards to how long a source might report data after a point's end date. In other words, a source lag of one month would mean that an annual source might report the 01/01/2017-12/31/2017 data point on 02/01/2018 at the latest. Extraordinary delays do occur from time to time, such as in a government shutdown or satellite data center malfunctions, but in general the data is expected to be updated by the endDate of the point + the sourceLag.

## Data Retrieval

### Q: I specified an end_date when calling get_data_points(), but I am getting points with other end_dates:
start_date and end_date behave as ranges. Specifying end_date is interpreted as "all points with an end date prior to this date" and start_date is "all points with a start_date later than this date." Both can be specified to narrow down the range.

## Account
### Q: I tried using my Gro username and login but am getting a 401 Unauthorized error
A Gro account gives you access to the web application at app.gro-intelligence.com. API access is sold as an add-on product you need to be activated for. To learn more about getting an API account, contact our sales team using the link at gro-intelligence.com/products/gro-api

## Gro Models
### Q: Do your predictive models only run during the crop season?
We provide predictions year around (always for the current market year, so for the US it is also always the current calendar year). Take the US, for example: before planting ends (Jan to May) we predict at the country level with the long-term trend. Between planting and harvesting (May to Oct) we predict at the district level with daily updates. After harvesting and until the end of the year, we only adjust the previous predictions if there is any adjustment from the sources that we used for the in-season predictions.
