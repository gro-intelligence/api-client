from builtins import object
from api.client import lib


class Client(object):

    """API client with stateful authentication for lib functions."""

    def __init__(self, api_host, access_token):
        self.api_host = api_host
        self.access_token = access_token

    def get_available(self, entity_type):
        return lib.get_available(self.access_token, self.api_host, entity_type)

    def list_available(self, selected_entities):
        return lib.list_available(self.access_token, self.api_host, selected_entities)

    def lookup(self, entity_type, entity_id):
        return lib.lookup(self.access_token, self.api_host, entity_type, entity_id)

    def lookup_unit_abbreviation(self, unit_id):
        return self.lookup('units', unit_id)['abbreviation']

    def get_data_series(self, **selection):
        return lib.get_data_series(self.access_token, self.api_host, **selection)

    def get_data_points(self, **selection):
        return lib.get_data_points(self.access_token, self.api_host, **selection)

    def search(self, entity_type, search_terms):
        return lib.search(self.access_token, self.api_host,
                          entity_type, search_terms)

    def search_and_lookup(self, entity_type, search_terms):
        return lib.search_and_lookup(self.access_token, self.api_host,
                                     entity_type, search_terms)

    def lookup_belongs(self, entity_type, entity_id):
        return lib.lookup_belongs(self.access_token, self.api_host,
                                  entity_type, entity_id)

    def rank_series_by_source(self, series_list):
        return lib.rank_series_by_source(self.access_token, self.api_host,
                                         series_list)

    def get_geo_centre(self, region_id):
        return lib.get_geo_centre(self.access_token, self.api_host, region_id)

    def get_geojson(self, region_id):
        return lib.get_geojson(self.access_token, self.api_host, region_id)

    def get_descendant_regions(self, region_id, descendant_level=None, include_historical=True):
        return lib.get_descendant_regions(self.access_token, self.api_host,
                                          region_id, descendant_level, include_historical)
