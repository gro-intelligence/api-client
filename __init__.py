from api.client import lib


class Client(object):

    """API client with stateful authentication for lib functions. """

    def __init__(self, api_host, access_token):
        self.api_host = api_host
        self.access_token = access_token

    def get_available(self, entity_type):
        return lib.get_available(self.access_token, self.api_host, entity_type)

    def list_available(self, selected_entities):
        return lib.list_available(self.access_token, self.api_host, selected_entities)

    def lookup(self, entity_type, entity_id):
        return lib.lookup(self.access_token, self.api_host, entity_type, entity_id)

    def get_data_series(self, **selection):
        return lib.get_data_series(self.access_token, self.api_host, **selection)

    def get_data_points(self, **selection):
        return lib.get_data_points(self.access_token, self.api_host, **selection)

    def search(self, entity_type, search_terms):
        return lib.search(self.access_token, self.api_host, entity_type, search_terms)
