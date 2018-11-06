from api.client import Client
from api.client import batch_lib as batch_lib

class BatchClient(Client):

    def __init__(self, api_host, access_token):
        super(BatchClient, self).__init__(api_host, access_token)

    # Same things below as above but batched and async.

    # def batch_get_available(self, entity_type):
    #     pass
    #     # TODO
    #     # return lib.get_available(self.access_token, self.api_host, entity_type)

    # def batch_list_available(self, selected_entities):
    #     pass
    #     # TODO
    #     # return lib.list_available(self.access_token, self.api_host, selected_entities)

    def batch_lookup(self, entities, results, map_response=None):
        return batch_lib.batch_lookup(self.access_token, self.api_host, entities, results, map_response)

    #
    # def batch_get_data_series(self, **selection):
    #     pass
    #     # TODO
    #     # return lib.get_data_series(self.access_token, self.api_host, **selection)

    def batch_get_data_points(self, selections, results, map_returned=None):
        return batch_lib.batch_get_data_points(self.access_token, self.api_host, selections, results, map_returned)
    #
    # def batch_search(self, entity_type, search_terms):
    #     pass
    #     # TODO
    #     # return lib.search(self.access_token, self.api_host,
    #     #                   entity_type, search_terms)
    #
    # def batch_search_and_lookup(self, entity_type, search_terms):
    #     pass
    #     # TODO
    #     # return lib.search_and_lookup(self.access_token, self.api_host,
    #     #                              entity_type, search_terms)
    #
    # def batch_lookup_belongs(self, entity_type, entity_id):
    #     pass
    #     # TODO
    #     # return lib.lookup_belongs(self.access_token, self.api_host,
    #     #                           entity_type, entity_id)
    #
    # def batch_rank_series_by_source(self, series_list):
    #     pass
    #     # TODO
    #     # return lib.rank_series_by_source(self.access_token, self.api_host,
    #     #                                  series_list)

