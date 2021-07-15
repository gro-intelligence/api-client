##############
Searching Data
##############

.. contents:: Table of Contents
  :local:

To derive the insights you want from Gro's data, you will first want to find the data you're interested in. Below you will find some of the most useful tips on how to discover the data of greatest value to you.

Code snippets
=============

Users may find that the Gro API is at its most powerful when used in conjunction with the Gro web application. The web app provides the most convenient format for selecting the data series that is of most interest to you. In our Add Data Series window, you can select entities of interest, and then other entities for which no data is available based on your selection will be filtered out from the remaining options. For example, after selecting the item "Corn" only metrics and regions that have data for 'Corn' will remain selectable.

.. image:: ./_images/add-data-series-example.PNG
  :align: center
  :alt: Add data series example

Once you have created a chart with data that you want, you can take advantage of our Code Snippets feature to pull that data into your API client code.

Simply click on the Chart Dropdown Button, then select Export and API Client Code Snippets.

.. image:: ./_images/code-snippet-dropdown.PNG
  :align: center
  :alt: Code snippet dropdown
  
Every unique data series from your chart will now be available in a client.get_data_points function for easy copying and pasting into your code or command line.

.. image:: ./_images/code-snippet-copy-code.PNG
  :align: center
  :alt: Code snippet copy code

For charts that have multiple data series, you have the option to Select all unique data series, or to select the individual series that are of greatest interest to you.

.. image:: ./_images/code-snippet-select-all.PNG
  :align: center
  :alt: Code snippet select all
  
Search
======


As described in the `Data Series Definition <./data-series-definition>`_ page, a data series in Gro is a unique combination of the entities: item, metric, region, partner_region (optional), frequency, and source. To find the specific entity you would like to retrieve data for, you can use a variety of search methods. For example, :meth:`groclient.GroClient.search` will return a list of IDs that match your search term. If you want to understand the differences between various search results, you may find the :meth:`groclient.GroClient.search_and_lookup` method more helpful.

:code:`client.search_and_lookup('items','Corn')` will yield a list of all items that contain "corn" in their name, along with supporting information like id, name, and ids of other items contained by a given item.

Note: the above query will return a `generator <https://wiki.python.org/moin/Generators>`_ object. Running a query like the one below will print every result:


Get data series
===============

Instead of searching for all the individual entity IDs required to create a data series, the :meth:`groclient.GroClient.get_data_series` method will return a list of all the data series available for the filters you have supplied. For example, if you are interested in Russian Oats you could use the following code to find out all the available data series that have "Oats" (item_id = 327) as the item and "Russia" (region_id = 1168) as the region:

::

  client.get_data_series(item_id='327',region_id='1168')


Lookup contains
===============
Our ontology is defined in terms of a graph, with metrics/items/regions containing others. In each case, you can see the :code:`'contains'` property in the output of :code:`client.lookup(type, id)`. For example:
::

  client.lookup('items', 10009)['contains']

will return a list of items ids for items that are cereals (item_id = 10009): :code:`[..., 274, 422, ...]`. Once you have those ids, you can use the :meth:`groclient.GroClient.lookup` function on each one to find more info, like their names, e.g.: :code:`client.lookup('items', 274)['name']` will return `Corn`.


Get descendants
===============

Using the :code:`lookup()` method, you can get an entity's list of direct children (i.e. country→provinces). However, you may want all of the lower level regions that belong to a higher level region (i.e. country→provinces, districts, coordinates, etc.). To do this, there's a helper function which also gives the option of filtering by region level: :meth:`groclient.GroClient.get_descendant_regions`

To look up all descendants of region 1029 (Brazil) that are of level 4 (provinces):
::

  from groclient.lib import REGION_LEVELS
  provinces_of_brazil = client.get_descendant_regions(1029, REGION_LEVELS['province'])

To look up all descendants of region 1029 (Brazil) that are of level 5 (districts):
::

  from groclient.lib import REGION_LEVELS
  provinces_of_brazil = client.get_descendant_regions(1029, REGION_LEVELS['district'])

For more information on region levels, please refer to the `Special properties of regions <./gro-ontology#special-properties-for-regions>`_ section of `Gro Ontology <./gro-ontology>`_


Lookup belongs
==============

If you want to find "what entities contain the given entity?" there is a method, :meth:`groclient.GroClient.lookup_belongs` that just does that. For example:
::

  UNITED_STATES = 1215
  client.lookup_belongs('regions', UNITED_STATES)

will yield :code:`[{id: 15, name: 'North America', contains: [1215, 1037, ...], level: 2}, ...]`
