from api.client import lib


class Client(object):

    """API client with stateful authentication for lib functions. """

    __unit_names = {}

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
        """Wrapper to lookup unit names, with local cache to avoid repeated lookups."""
        if unit_id not in self.__unit_names:
            self.__unit_names[unit_id] = self.lookup('units', unit_id)['abbreviation']
        return self.__unit_names[unit_id]

    def lookup_any_entity(id_or_name):
        entities = ['items', 'metrics', 'regions', 'sources', 'units', 'frequencies', 'sources' ]
        return_list = list()
        if type( unknown_value ) == str:
            for entity_type in entities:
                return_list.append( [entity_type] )
                return_list.append(self.search(entity_type, unknown_value))
        elif type( unknown_value ) == int:
            for entity_type in entities:
                return_list.append( [entity_type] )
                return_list.append( lookup( tok, api_host, entity_type, unknown_value ) )
        else:
            raise Exception('Need to use string or integer input')
        return return_list
        
    def get_data_series(self, **selection):
        return lib.get_data_series(self.access_token, self.api_host, **selection)

    def get_data_points(self, **selection):
        return lib.get_data_points(self.access_token, self.api_host, **selection)

    def search(self, entity_type, search_terms):
        return lib.search(self.access_token, self.api_host, entity_type, search_terms)
