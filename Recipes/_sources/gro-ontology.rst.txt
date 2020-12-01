############
Gro Ontology
############

.. contents:: Table of Contents
  :local:

Gro has brought the world of agricultural data into a single ontology. This ontology classifies all data into a limited set of entities.

The entity types around which the data is organized in Gro are:

* items -- what the data is about (e.g., Rice, Sugar, Rainfall, etc.).
* metrics -- how the data is measured (e.g., Production, Precipitation, etc.).
* regions -- where the data is from/about (e.g., a country, a weather station, a city etc.). Some data such as trade flows might have a partner region.
* frequencies -- e.g., daily, weekly etc.
* sources -- the organization or sub-organization that generates the data (e.g., USDA PS&D).
* units -- the units in which the data is presented (e.g., tonnes, liters, etc.).



Entity fields
=============
Each specific entity will have an `id`, `name`, and various other properties. For example, "Soybeans" is a specific item with `id = 270` and the following information

.. code-block:: python

  { 'contains': [1737, 7401, 7578, 7579, 5136, 5021, 5135, 5137, 12418, 5776, 5777, 3035, 3036, 9312, 9284, 6330, 7577, 12728, 12729, 12730, 12731, 12732, 12733, 12734, 12735, 12736, 12737, 10134],
    'definition': 'The seeds and harvested crops of plants belonging to the species <i>Glycine max</i> that are used in the production of oil and both human and livestock consumption.',
    'id': 270,
    'name': 'Soybeans' }

IDs are unique within a particular entity type, i.e., there's only one item with id = 270.

The above information can be retrieved using the :meth:`groclient.GroClient.lookup` function:

.. code-block:: python

  client.lookup('items', 270)

`See this Getting Started section for help on finding entities by name or by id. <understanding-data-responses#lookup>`_


Entity Relationships: Contains
==============================
Items, metrics, and regions have a property called `contains`, which is an array of the other entities that it contains, or that belong to it. For example, the item "Cereals" contains the items "Wheat," "Corn," etc.

Variations of the `client.lookup(type, id)` function can help you understand what a given entity contains or belongs to. For example, the following will return a list of items that are contained within the item "Cereals" (item_id: 10009):

.. code-block:: python

  client.lookup('items', 10009)['contains']

And, in the opposite direction, the following will return a list of regions "California" (region_id: 13055) belongs to.

.. code-block:: python

  client.lookup_belongs('regions', 13055)

`See this Getting Started section for navigation of relationships between entities. <searching-data#lookup-contains>`_


Special Properties for Regions
==============================

The following properties exist for regions only:

:code:`level`
-------------
Region level corresponds to the administrative level of the region:

* level 1: world
* level 2: continent
* level 3: country
* level 4: provinces
* level 5: districts
* level 6: city
* level 7: market
* level 8: other arbitrary regions
* level 9: point-location


:code:`latitude` and :code:`longitude`
--------------------------------------
For point-locations (i.e., region level 9), these properties correspond to the location's coordinates. More generally for other regions, these properties correspond to the coordinates of the geographic center of the region.

The :code:`lookup()` function will return the :code:`latitude` and :code:`longitude` of a region. For example, you can find the geographic center of Nairobi :code:`region_id=13474` with the following query:

.. code-block:: python

  client.lookup('regions', 13474)

Which has the result:

.. code-block:: python

  { 'contains': [ 142828, 142830, 1000272, 142836, 142831, 142834, 142838, 142833, 142837, 143105, 143103, 142829, 142835, 143104, 143102, 143106, 143101, 142832 ],
    'id': 13474,
    'latitude': -1.29359,
    'level': 4,
    'longitude': 36.8691,
    'name': 'Nairobi' }


:code:`historical`
------------------
Regions with :code:`historical` set to :code:`True` are administrative regions (e.g. countries, provinces, disricts) that no longer exist
adminstratively in the real world. However, data can be accessed for those regions like all regions. For example:
::

   client.lookup('regions',1262)

which has the result:
::

   {'contains': [1226, 1228],
    'id': 1262,
    'name': u'Serbia and Kosovo',
    'level': 3,
    'historical': True }
