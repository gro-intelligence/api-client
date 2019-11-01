from builtins import object
from api.client import lib


class Client(object):

    """API client with stateful authentication for lib functions."""

    def __init__(self, api_host, access_token):
        self.api_host = api_host
        self.access_token = access_token

    def get_available(self, entity_type):
        """List the first 5000 available entities of the given type.

        Parameters
        ----------
        entity_type : string
            'items', 'metrics', or 'regions'

        Returns
        -------
        data : list of dicts

            Example::

                [ { 'id': 0, 'contains': [1, 2, 3], 'name': 'World', 'level': 1},
                { 'id': 1, 'contains': [4, 5, 6], 'name': 'Asia', 'level': 2},
                ... ]

        """
        return lib.get_available(self.access_token, self.api_host, entity_type)

    def list_available(self, selected_entities):
        """List available entities given some selected entities.

        Given one or more selections, return entities combinations that have
        data for the given selections.

        Parameters
        ----------
        selected_entities : dict

            Example::

                { 'metric_id': 123, 'item_id': 456, 'source_id': 7 }

            Keys may include: metric_id, item_id, region_id, partner_region_id,
            source_id, frequency_id

        Returns
        -------
        list of dicts

            Example::

                [ { 'metric_id': 11078, 'metric_name': 'Export Value (currency)',
                    'item_id': 274, 'item_name': 'Corn',
                    'region_id': 1215, 'region_name': 'United States',
                    'source_id': 15, 'source_name': 'USDA GATS' },
                { ... },
                ... ]

        """
        return lib.list_available(self.access_token, self.api_host, selected_entities)

    def lookup(self, entity_type, entity_id):
        """Retrieve details about a given id of type entity_type.

        https://github.com/gro-intelligence/api-client/wiki/Entities-Definition

        Parameters
        ----------
        access_token : string
        api_host : string
        entity_type : string
            'items', 'metrics', 'regions', 'units', 'frequencies', or 'sources'
        entity_id : int

        Returns
        -------
        dict

            Example::

                { 'id': 274,
                'contains': [779, 780, ...]
                'name': 'Corn',
                'definition': ('The seeds of the widely cultivated corn plant <i>Zea mays</i>, which'
                            ' is one of the world\'s most popular grains.') }

        """
        return lib.lookup(self.access_token, self.api_host, entity_type, entity_id)

    def lookup_unit_abbreviation(self, unit_id):
        """
            TODO
        """

        # DEPRECATED
        return self.lookup('units', unit_id)['abbreviation']

    def get_data_series(self, **selection):
        """Get available data series for the given selections.

        https://github.com/gro-intelligence/api-client/wiki/Data-Series-Definition

        Parameters
        ----------
        access_token : string
        api_host : string
        metric_id : integer, optional
        item_id : integer, optional
        region_id : integer, optional
        partner_region_id : integer, optional
        source_id : integer, optional
        frequency_id : integer, optional

        Returns
        -------
        list of dicts

            Example::

                [{ 'metric_id': 2020032, 'metric_name': 'Seed Use',
                'item_id': 274, 'item_name': 'Corn',
                'region_id': 1215, 'region_name': 'United States',
                'source_id': 24, 'source_name': 'USDA FEEDGRAINS',
                'frequency_id': 7,
                'start_date': '1975-03-01T00:00:00.000Z', 'end_date': '2018-05-31T00:00:00.000Z'
                }, { ... }, ... ]

        """
        return lib.get_data_series(self.access_token, self.api_host, **selection)

    def get_data_points(self, **selection):
        """Get all the data points for a given selection.

        https://github.com/gro-intelligence/api-client/wiki/Data-Point-Definition

        Parameters
        ----------
        access_token : string
        api_host : string
        metric_id : integer
        item_id : integer
        region_id : integer
        partner_region_id : integer
        source_id : integer
        frequency_id : integer
        start_date : string, optional
            all points with start dates equal to or after this date
        end_date : string, optional
            all points with end dates equal to or after this date
        show_revisions : boolean, optional
            False by default, meaning only the latest value for each period. If true, will return all
            values for a given period, differentiated by the `reporting_date` field.
        insert_null : boolean, optional
            False by default. If True, will include a data point with a None value for each period
            that does not have data.
        at_time : string, optional
            Estimate what data would have been available via Gro at a given time in the past. See
            /api/client/samples/at-time-query-examples.ipynb for more details.

        Returns
        -------
        list of dicts

            Example::

                [ {
                    "start_date": "2000-01-01T00:00:00.000Z",
                    "end_date": "2000-12-31T00:00:00.000Z",
                    "value": 251854000,
                    "input_unit_id": 14,
                    "input_unit_scale": 1,
                    "metric_id": 860032,
                    "item_id": 274,
                    "region_id": 1215,
                    "frequency_id": 9,
                    "unit_id": 14
                }, ...]

        """
        return lib.get_data_points(self.access_token, self.api_host, **selection)

    def search(self, entity_type, search_terms):
        """Search for the given search term. Better matches appear first.

        Parameters
        ----------
        access_token : string
        api_host : string
        entity_type : string
            One of: 'metrics', 'items', 'regions', or 'sources'
        search_terms : string

        Returns
        -------
        list of dicts

            Example::

                [{'id': 5604}, {'id': 10204}, {'id': 10210}, ....]

        """
        return lib.search(self.access_token, self.api_host,
                          entity_type, search_terms)

    def search_and_lookup(self, entity_type, search_terms):
        """Search for the given search terms and look up their details.

        For each result, yield a dict of the entity and it's properties:
        { 'id': <integer id of entity, unique within this entity type>,
            'name':    <string canonical name>
            'contains': <array of ids of entities that are contained in this one>,
            ....
            <other properties> }

        Parameters
        ----------
        access_token : string
        api_host : string
        entity_type : string
            One of: 'metrics', 'items', 'regions', or 'sources'
        search_terms : string
        num_results: int
            Maximum number of results to return

        Yields
        ------
        dict
            Result from search() passed to lookup() to get additional details. For example::

                { 'id': 274, 'contains': [779, 780, ...] 'name': 'Corn',
                'definition': 'The seeds of the widely cultivated...' }

            See output of lookup(). Note that as with search(), the first result is
            the best match for the given search term(s).

        """

        # DEPRECATED
        return lib.search_and_lookup(self.access_token, self.api_host,
                                     entity_type, search_terms)

    def lookup_belongs(self, entity_type, entity_id):
        """Look up details of entities containing the given entity.

        Parameters
        ----------
        access_token : string
        api_host : string
        entity_type : string
            One of: 'metrics', 'items', or 'regions'
        entity_id : integer

        Yields
        ------
        dict
            Result of lookup() on each entity the given entity belongs to.

            For example: For the region 'United States', one yielded result will be for
            'North America.' The format of which matches the output of lookup()::

                { 'id': 15,
                'contains': [ 1008, 1009, 1012, 1215, ... ],
                'name': 'North America',
                'level': 2 }

        """

        # DEPRECATED
        return lib.lookup_belongs(self.access_token, self.api_host,
                                  entity_type, entity_id)

    def rank_series_by_source(self, series_list):
        return lib.rank_series_by_source(self.access_token, self.api_host,
                                         series_list)

    def get_geo_centre(self, region_id):
        """Given a region ID, return the geographic centre in degrees lat/lon.

        Parameters
        ----------
        access_token : string
        api_host : string
        region_id : integer

        Returns
        -------
        list of dicts

            Example::

                [{ 'centre': [ 45.7228, -112.996 ], 'regionId': 1215, 'regionName': 'United States' }]

        """
        return lib.get_geo_centre(self.access_token, self.api_host, region_id)

    def get_geojson(self, region_id):
        """Given a region ID, return a geojson shape information

        Parameters
        ----------
        access_token : string
        api_host : string
        region_id : integer

        Returns
        -------
        a geojson object e.g.
        { 'type': 'GeometryCollection',
        'geometries': [{'type': 'MultiPolygon',
                        'coordinates': [[[[-38.394, -4.225], ...]]]}, ...]}
        or None if not found.
        """
        return lib.get_geojson(self.access_token, self.api_host, region_id)

    def get_descendant_regions(self, region_id, descendant_level=None):
        """Look up details of regions of the given level contained by a region.

        Given any region by id, recursively get all the descendant regions
        that are of the specified level.

        This takes advantage of the assumption that region graph is
        acyclic. This will only traverse ordered region levels (strictly
        increasing region level id) and thus skips non-administrative region
        levels.

        Parameters
        ----------
        access_token : string
        api_host : string
        region_id : integer
        descendant_level : integer
            The region level of interest. See REGION_LEVELS constant.

        Returns
        -------
        list of dicts

            Example::

                [{
                    'id': 13100,
                    'contains': [139839, 139857, ...],
                    'name': 'Wisconsin',
                    'level': 4
                } , {
                    'id': 13101,
                    'contains': [139891, 139890, ...],
                    'name': 'Wyoming',
                    'level': 4
                }, ...]

            See output of lookup()

        """
        return lib.get_descendant_regions(self.access_token, self.api_host,
                                          region_id, descendant_level)
