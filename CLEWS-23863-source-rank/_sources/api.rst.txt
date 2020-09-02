API Reference
#############

.. contents:: Table of Contents
  :local:

=================
Basic Exploration
=================

.. automethod:: groclient.GroClient.lookup

.. automethod:: groclient.GroClient.search

.. automethod:: groclient.GroClient.search_and_lookup

.. automethod:: groclient.GroClient.search_for_entity

.. automethod:: groclient.GroClient.get_data_series

.. automethod:: groclient.GroClient.find_data_series

==============
Data Retrieval
==============

.. automethod:: groclient.GroClient.get_data_points

==========
Geographic
==========

.. automethod:: groclient.GroClient.get_geojson

.. automethod:: groclient.GroClient.get_descendant_regions

.. automethod:: groclient.GroClient.get_provinces

====================
Advanced Exploration
====================

.. automethod:: groclient.GroClient.lookup_belongs

.. automethod:: groclient.GroClient.rank_series_by_source

.. automethod:: groclient.GroClient.get_available_timefrequency

.. automethod:: groclient.GroClient.get_top

============
Pandas Utils
============

.. automethod:: groclient.GroClient.get_df

.. automethod:: groclient.GroClient.add_data_series

.. automethod:: groclient.GroClient.add_single_data_series

.. automethod:: groclient.GroClient.get_data_series_list

=============
Crop Modeling
=============

.. automethod:: groclient.CropModel.compute_weights

.. automethod:: groclient.CropModel.compute_crop_weighted_series

.. automethod:: groclient.CropModel.compute_gdd

.. automethod:: groclient.CropModel.growing_degree_days
