API Reference
#############

.. contents:: Table of Contents
  :local:

=================
Basic Exploration
=================

.. automethod:: api.client.gro_client.GroClient.lookup

.. automethod:: api.client.gro_client.GroClient.search

.. automethod:: api.client.gro_client.GroClient.search_and_lookup

.. automethod:: api.client.gro_client.GroClient.search_for_entity

.. automethod:: api.client.gro_client.GroClient.get_data_series

.. automethod:: api.client.gro_client.GroClient.find_data_series

==============
Data Retrieval
==============

.. automethod:: api.client.gro_client.GroClient.get_data_points

==========
Geographic
==========

.. automethod:: api.client.gro_client.GroClient.get_geojson

.. automethod:: api.client.gro_client.GroClient.get_descendant_regions

.. automethod:: api.client.gro_client.GroClient.get_provinces

====================
Advanced Exploration
====================

.. automethod:: api.client.gro_client.GroClient.lookup_belongs

.. automethod:: api.client.gro_client.GroClient.rank_series_by_source

.. automethod:: api.client.gro_client.GroClient.get_available_timefrequency

============
Pandas Utils
============

.. automethod:: api.client.gro_client.GroClient.get_df

.. automethod:: api.client.gro_client.GroClient.add_data_series

.. automethod:: api.client.gro_client.GroClient.add_single_data_series

.. automethod:: api.client.gro_client.GroClient.get_data_series_list

=============
Crop Modeling
=============

.. automethod:: api.client.crop_model.CropModel.compute_weights

.. automethod:: api.client.crop_model.CropModel.compute_crop_weighted_series

.. automethod:: api.client.crop_model.CropModel.compute_gdd

.. automethod:: api.client.crop_model.CropModel.growing_degree_days
