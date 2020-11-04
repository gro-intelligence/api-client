####
FAQs
####

.. contents:: Table of Contents
  :local:

Exploring What's Available
==========================

Why is it that when I use client.search() to find metrics/items/regions I'm interested in, sometimes client.get_data_series() doesn't have any data for those metrics/items/regions?
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

:code:`client.search()` provides a way to search across everything we have identified and defined in our ontology. Sometimes data doesn't exist for a particular result for a number of reasons, most commonly because we may have defined new entries in preparation for an incoming source which is undergoing testing. 
`find_data_series() <api.html#groclient.GroClient.find_data_series>`_
will tell you what data is actually available by performing searches for combinations of items, metrics and regions. You can intersect the results from those two functions to find things programmatically, or you can use the web application at https://app.gro-intelligence.com to explore what data is available, intersected already.

What does 'sourceLag' mean when I use client.lookup() to inspect a source's details?
------------------------------------------------------------------------------------

Source lag is defined as the worst normal case scenario in regards to how long a source might report data after a point's end date. In other words, a source lag of one month would mean that an annual source might report the 01/01/2017-12/31/2017 data point on 02/01/2018 at the latest. Extraordinary delays do occur from time to time, such as in a government shutdown or satellite data center malfunctions, but in general the data is expected to be updated by the endDate of the point + the sourceLag.

Data Retrieval
==============

I specified an end_date when calling get_data_points(). Why am I getting points with other end_dates?
----------------------------------------------------------------------------------------------------

start_date and end_date specify a time interval. When retrieving a
series, it is interpreted *inclusively* i.e. it will include points
that are fully or partially in the desired interval. Thus if the start
and end dates selected are March 15 to May 15, and the data happens to
be monthly on calendar months, it will include points for [Mar 1, Mar
31], [Apr 1, Apr 30], [May 1, May 31]. 

Thus, when calling `get_data_points() <api.html#groclient.GroClient.get_data_points>`_ specifying a start_date for the series restricts the query to any point where "point_end_date >= series_start_date," and a series end_date restricts it to any point where "point_start_date <= series_end_date".


Data Coverage
=============

Why is there no satellite rainfall data in northern latitudes sometimes?
------------------------------------------------------------------------

This is determined by the spatial extent of the satellites. For more information see `TRMM/GPM spatial extent <modeling-resources#trmm-and-gpm-spatial-extents>`_. Note that this limitation is only for satellite data. Rainfall data from ground-based weather stations is also available in Gro, see `NOAA/NCDC GHCN <https://app.gro-intelligence.com/dictionary/sources/22>`_.

Why are there some gaps in the soil moisture data?
--------------------------------------------------

Radio Frequency Interferences (RFI) can limit the quality of remotely sensed data in some regions. For more information see `Radio Frequency Interference Effects On SMOS <modeling-resources#radio-frequency-interference-effects-on-smos>`_.

What do warnings about 'historical' regions mean?
-------------------------------------------------------------------

`Historical regions <gro-ontology#historical>`_ behave just like other regions. Any data that exists can be accessed the same way as data for any region in Gro.  Generally historical regions will only have data corresponding to the time periods when they existed. But in some
cases, new regions can have data that extends into the past and overlaps with historical regions. 
Rather than always excluding the old regions in such cases, we allow the user to choose via the  :code:`include_historical` option in `get_data_points() <api.html#groclient.GroClient.get_data_points>`_. This can be useful if for example you are analyzing historical temperatures at the district level in a country where the districts that exist today were only created 5 years ago and but you want 20 years of data. In that case, you can filter out the historical regions to avoid double counting.

Why is daily NDVI changing so much from day to day? And why do some days have no NDVI coverage, especially in winter?
-----------------------------------------------------------------------------------------------------------------------

The Normalized Difference Vegetation Index (NDVI) relates satellite based observations to vegetation health and condition. However, in the presence of clouds, especially thin cirrus undetected by cloud algorithms, NDVI is artificially dampened. As a result, NDVI has  lower values on days with undetected thin clouds and higher values on days with no cloud cover. The satellite readings are also affected by snow and ice cover, which means NDVI coverage in the winter may be limited for some regions.

To avoid these day-to-day variations in the Sentinel-3A (S3A) and Sentinel-3B (S3B) daily NDVI dataset, Gro users can make use of the MODIS GIMMS 8-day NDVI product, which is based on selecting the maximum NDVI pixel value over an eight-day period. This is a more stable product that minimizes the cloud effect.
 
Why isn’t there 100% coverage every day for daily NDVI?
--------------------------------------------------------

We cannot achieve 100% global coverage daily because it takes, on average, 1.1 days (26.4 hours) for the S3A and S3B satellites to cover the globe. In addition, since cloud and snow covers are limiting factors, such areas are detected and assigned a “no data” value, further reducing the percentage of daily coverage.
 
Why a threshold and how is it computed to determine district mean?
-------------------------------------------------------------------

Passive sensors onboard the MODIS Terra and Aqua and S3A and S3B satellites collect a different number of pixels, or samples, each day due to the time it takes for global coverage (1.1 days are required to cover the globe for daily NDVI), processing issues, and/or cloud cover limiting observations. To better represent the signal mean for a district, we set a minimum number of samples, or threshold, that is needed. This is represented as a percentage of the total number of samples for a given day divided by the district area. Our production system will show “no data” when collected samples for a given day are below the threshold.

We compute the threshold by conducting a sensitivity analysis using NDVI data over various districts spread globally for different time frames, changing the number of pixels in a district and analyzing the impact this has on the district mean and associated error. We determined that a 20% threshold for S3A and S3B should be used to compute district mean, which represents a compromise between the need for NDVI global coverage that is significantly affected by cloud, and accuracy of the derived district mean computation. Using a 20% threshold yields an average error of 7%, as compared with NDVI estimate error from most satellite missions of about 5%.



Account
=======

How do I verify connectivity with Gro API?
------------------------------------------

To check your basic connectivity, e.g. whether your corporate firewall allows access to Gro API servers, you can using a Gro API client function that doesn't require authentication, such as lookup(). For example:
::

  from groclient.lib import lib
  lib.lookup('', 'api.gro-intelligence.com', 'items', 1)


How do I get authenticated access to Gro API?
---------------------------------------------

You must get an `authentication token <authentication#retrieving-a-token>`_ from your Gro account.

Why am I getting a 401 Unauthorized error when I try to use my Gro username and login?
-------------------------------------------------------------------------------

A Gro account gives you access to the web application at app.gro-intelligence.com. API access is sold as an add-on product you need to be activated for. To learn more about getting an API account, contact our sales team using the link at `gro-intelligence.com/products/gro-api <https://www.gro-intelligence.com/products/gro-api>`_

Gro Models
==========

Do your predictive models only run during the crop season?
----------------------------------------------------------

We provide predictions year around (always for the current market year, so for the US it is also always the current calendar year). Take the US, for example: before planting ends (Jan to May) we predict at the country level with the long-term trend. Between planting and harvesting (May to Oct) we predict at the district level with daily updates. After harvesting and until the end of the year, we only adjust the previous predictions if there is any adjustment from the sources that we used for the in-season predictions.
