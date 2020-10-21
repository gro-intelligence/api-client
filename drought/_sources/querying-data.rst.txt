#############
Querying Data
#############

.. contents:: Table of Contents
  :local:

Once you've identified the data you want, you'll want to start retrieving it and putting it to use. The following methods should help you get the data in the format that you want.

All of the examples in this page refer to a client object, which can
be initialized as follows:

.. code-block:: python

  from groclient import GroClient

  client = GroClient('api.gro-intelligence.com', '<YOUR_TOKEN>')


Get data points
===============

:code:`get_data_points(**selection)` is the most basic method for retrieving data. The `code snippets <searching-data#code-snippets>`_ feature covered earlier provides you with a fully completed `get_data_points()` query, such as:

.. code-block:: python

  # Wheat - Area Harvested (area) - India (USDA PS&D)
  client.get_data_points(**{
      'metric_id': 570001,
      'item_id': 95,
      'region_id': 1094,
      'source_id': 14,
      'frequency_id': 9
  })

The above query has completed fields for :code:`metric_id`, :code:`item_id`, :code:`region_id`, :code:`source_id`, and :code:`frequency_id`. However, :meth:`groclient.GroClient.get_data_points` can also accept fields to further narrow your data series of interest: :code:`partner_region_id` (used only in series that represent a flow between two places), :code:`start_date`, :code:`end_date`, :code:`show_revions`, :code:`insert_null`, and :code:`at_time`.

Making your query more specific will speed up your query by limiting the amount of data requested.

Get data frame
==============

`Pandas data frames <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html>`_ are a popular format for processing large amounts of data. The :code:`GroClient` class' :code:`get_df()` method offers you the ability to access multiple data series in a single data frame. This approach is convenient for modeling or analysis using many different data series.

:code:`get_df()` is a stateful method, so you must first save one or more series into your client object.

The easiest way to do that is to use :code:`add_data_series()`, e.g.:

.. code-block:: python

  client.add_data_series(**{
      'metric': 'area harvested',
      'item': 'wheat',
      'region': 'India'
  })

  client.add_data_series(**{
      'metric': 'production quantity',
      'item': 'wheat',
      'region': 'India'
  })

  df = client.get_df()


Note that :code:`add_data_series()` combines searching for combinations of entities by name, finding the best possible data series for that combination, and adding it to the client. In the above example, each :code:`add_data_series()` call finds several possible series (5 series for area harvested and 6 for production quantity respectively), and adds the highest ranked one for each.  For more information on how series are ranked see :meth:`groclient.GroClient.rank_series_by_source`.

If you want to directly control the series selection, you can also take a specific selection - discovered, perhaps, via `code snippets <./searching-data.html#code-snippets>`_, or using :meth:`groclient.GroClient.find_data_series` and then add that series directly with the
:code:`add_single_data_series()` method, e.g.:

.. code-block:: python

  client.add_single_data_series({
       'metric_id': 570001,
       'item_id': 95,
       'region_id': 1094,
       'source_id': 14,
       'frequency_id': 9
  })

  client.add_single_data_series({
       'metric_id': 860032,
       'item_id': 95,
       'region_id': 1094,
       'source_id': 50
       'frequency_id': 9,
  })

  df = client.get_df()


Note that in the second example, we choose to get the first series from the source with id 14 which is `USDA PS&D <https://app.gro-intelligence.com/dictionary/sources/14>`_, and the second series from source with id 50, which is `IDAC <https://app.gro-intelligence.com/dictionary/sources/50>`_. The two sources may differ in historical time range or their data release schedule.

Show revisions
==============

Sometimes looking at the most recent data point doesn't tell you the whole story. You may want to see if there have been any revisions to data, especially if the data is a forecast value. This standard `get_data_points` query will return the annual values for soybean yield in Argentina since 2017:

.. code-block:: python

  # Soybeans - Yield (mass/area) - Argentina (USDA PS&D)
  client.get_data_points(**{
      'metric_id': 170037,
      'item_id': 270,
      'region_id': 1010,
      'source_id': 14,
      'frequency_id': 9,
      'start_date': '2017-01-01'
  })


But the USDA begins forecasting the yield well before harvest time, and will continue to update its estimate for many months after the harvest is over. In order to see how the forecasts and estimates for each year have changed, you can include the `show_revisions` field as follows:

.. code-block:: python

  # Soybeans - Yield (mass/area) - Argentina (USDA PS&D)
  client.get_data_points(**{
      'metric_id': 170037,
      'item_id': 270,
      'region_id': 1010,
      'source_id': 14,
      'frequency_id': 9,
      'start_date': '2017-01-01',
      'show_revisions': True
  })
