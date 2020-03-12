###
FAQ
###

.. contents:: Table of Contents
  :local:

Exploring What's Available
==========================

Why is it that when I use client.search() to find metrics/items/regions I'm interested in, sometimes client.get_data_series() doesn't have any data for those metrics/items/regions?
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

:code:`client.search()` provides a way to search across everything we have identified and defined in our ontology. Sometimes data doesn't exist for a particular result for a number of reasons, most commonly because we may have defined new entries in preparation for an incoming source which is undergoing testing. `client.get_data_series()` will tell you what data is actually available. You can intersect the results from those two functions to find things programmatically, or you can use the web application at https://app.gro-intelligence.com to explore what data is available, intersected already.

What does 'sourceLag' mean when I use client.lookup() to inspect a source's details?
------------------------------------------------------------------------------------

Source lag is defined as the worst normal case scenario in regards to how long a source might report data after a point's end date. In other words, a source lag of one month would mean that an annual source might report the 01/01/2017-12/31/2017 data point on 02/01/2018 at the latest. Extraordinary delays do occur from time to time, such as in a government shutdown or satellite data center malfunctions, but in general the data is expected to be updated by the endDate of the point + the sourceLag.

Data Retrieval
==============

I specified an end_date when calling get_data_points(), but I am getting points with other end_dates
----------------------------------------------------------------------------------------------------

start_date and end_date specify a time interval. When retrieving a
series, it is interpreted *inclusively* i.e. it will include points
that are fully or partially in the desired interval. Thus if the start
and end dates selected are March 15 to May 15, and the data happens to
be monthly on calendar months, it will include points for [Mar 1, Mar
31], [Apr 1, Apr 30], [May 1, May 31]. 

Thus, when calling `get_data_points() <api.html#api.client.gro_client.GroClient.get_data_points>`_ specifying a start_date for the series restricts the query to any point where "point_end_date >= series_start_date," and a series end_date restricts it to any point where "point_start_date <= series_end_date".


Data Coverage
=============

Why is there no satellite rainfall data in northern latitudes sometimes?
------------------------------------------------------------------------

This is determined by the spatial extent of the satellites. For more information see `TRMM/GPM spatial extent <other#trmm-and-gpm-spatial-extents>`_. Note that this limitation is only for satellite data. Rainfall data from ground-based weather stations is also available in Gro, see `NOAA/NCDC GHCN <https://app.gro-intelligence.com/dictionary/sources/22>`_.

Why are there some gaps in the soil moisture data?
--------------------------------------------------

Radio Frequency Interferences (RFI) can limit the quality of remotely sensed data in some regions. For more information see `Radio Frequency Interference Effects On SMOS <other#radio-frequency-interference-effects-on-smos>`_.

What do warnings about 'historical' regions mean?
-------------------------------------------------------------------

`Historical regions <gro-ontology#historical>`_ behave just like other regions. Any data that exists can be accessed the same way as data for any region in Gro.  Generally historical regions will only have data corresponding to the time periods when they existed. But in some
cases, new regions can have data that extends into the past and overlaps with historical regions. 
Rather than always excluding the old regions in such cases, we allow the user to choose via the  :code:`include_historical` option in `get_data_points() <api.html#api.client.gro_client.GroClient.get_data_points>`_. This can be useful if for example you are analyzing historical temperatures at the district level in a country where the districts that exist today were only created 5 years ago and but you want 20 years of data. In that case, you can filter out the historical regions to avoid double counting.


Account
=======

How do I verify connectivity with Gro API?
------------------------------------------

To check your basic connectivity, e.g. whether your corporate firewall allows access to Gro API servers, you can using a Gro API client function that doesn't require authentication, such as lookup(). For example:
::

  from api.client.lib import lib
  lib.lookup('', 'api.gro-intelligence.com', 'items', 1)


How do I get authenticated access to Gro API?
---------------------------------------------

You must get an `authentication token <authentication#retrieving-a-token>`_ from your Gro account.

I tried using my Gro username and login but am getting a 401 Unauthorized error
-------------------------------------------------------------------------------

A Gro account gives you access to the web application at app.gro-intelligence.com. API access is sold as an add-on product you need to be activated for. To learn more about getting an API account, contact our sales team using the link at `gro-intelligence.com/products/gro-api <gro-intelligence.com/products/gro-api>`_

Gro Models
==========

Do your predictive models only run during the crop season?
----------------------------------------------------------

We provide predictions year around (always for the current market year, so for the US it is also always the current calendar year). Take the US, for example: before planting ends (Jan to May) we predict at the country level with the long-term trend. Between planting and harvesting (May to Oct) we predict at the district level with daily updates. After harvesting and until the end of the year, we only adjust the previous predictions if there is any adjustment from the sources that we used for the in-season predictions.
