from api.client import lib


class Client(object):

    """API client with stateful authentication for lib functions. """

    __unit_names = {}

    def __init__(self, api_host, access_token):
        self.api_host = api_host
        self.access_token = access_token

    def get_available(self, entity_type):
        return lib.get_available(self.access_token, self.api_host, entity_type)

    def batch_async_get_available(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_get_available(self.access_token, self.api_host, list_of_args,
                                             output_list=output_list, map_result=map_result)

    def list_available(self, selected_entities):
        return lib.list_available(self.access_token, self.api_host, selected_entities)

    def batch_async_list_available(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_list_available(self.access_token, self.api_host, list_of_args,
                                              output_list=output_list, map_result=map_result)

    def lookup(self, entity_type, entity_id):
        return lib.lookup(self.access_token, self.api_host, entity_type, entity_id)

    def batch_async_lookup(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_lookup(self.access_token, self.api_host, list_of_args,
                                              output_list=output_list, map_result=map_result)

    def lookup_unit_abbreviation(self, unit_id):
        """Wrapper to lookup unit names, with local cache to avoid repeated lookups."""
        if unit_id not in self.__unit_names:
            self.__unit_names[unit_id] = self.lookup('units', unit_id)['abbreviation']
        return self.__unit_names[unit_id]

    def get_data_series(self, **selection):
        return lib.get_data_series(self.access_token, self.api_host, **selection)

    def batch_async_get_data_series(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_get_data_series(self.access_token, self.api_host, list_of_args,
                                               output_list=output_list, map_result=map_result)

    def get_data_points(self, **selection):
        return lib.get_data_points(self.access_token, self.api_host, **selection)

    def batch_async_get_data_points(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_get_data_points(self.access_token, self.api_host, list_of_args,
                                               output_list=output_list, map_result=map_result)

    def search(self, entity_type, search_terms):
        return lib.search(self.access_token, self.api_host,
                          entity_type, search_terms)

    def batch_async_search(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_search(self.access_token, self.api_host, list_of_args,
                                      output_list=output_list, map_result=map_result)

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

    def batch_async_get_geo_centre(self, list_of_args, output_list=None, map_result=None):
        return lib.batch_async_get_geo_centre(self.access_token, self.api_host, list_of_args,
                                              output_list=output_list, map_result=map_result)
