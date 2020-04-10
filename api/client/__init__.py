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
        entity_type : {'metrics', 'items', 'regions'}

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


    def lookup(self, entity_type, entity_ids):
        """Retrieve details about a given id or list of ids of type entity_type.

        https://developers.gro-intelligence.com/gro-ontology.html

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions', 'frequencies', 'sources', 'units' }
        entity_ids : int or list of ints

        Returns
        -------
        dict or dict of dicts
            A dict with entity details is returned if an integer is given for entity_ids.
            A dict of dicts with entity details, keyed by id, is returned if a list of integers is
            given for entity_ids.

            Example::

                { 'id': 274,
                  'contains': [779, 780, ...]
                  'name': 'Corn',
                  'definition': 'The seeds of the widely cultivated corn plant <i>Zea mays</i>,'
                                ' which is one of the world\'s most popular grains.' }

            Example::

                {   '274': {
                        'id': 274,
                        'contains': [779, 780, ...],
                        'belongsTo': [4138, 8830, ...],
                        'name': 'Corn',
                        'definition': 'The seeds of the widely cultivated corn plant'
                                      ' <i>Zea mays</i>, which is one of the world\'s most popular'
                                      ' grains.'
                    },
                    '270': {
                        'id': 270,
                        'contains': [1737, 7401, ...],
                        'belongsTo': [8830, 9053, ...],
                        'name': 'Soybeans',
                        'definition': 'The seeds and harvested crops of plants belonging to the'
                                      ' species <i>Glycine max</i> that are used in the production'
                                      ' of oil and both human and livestock consumption.'
                    }
                }

        """
        return lib.lookup(self.access_token, self.api_host, entity_type, entity_ids)


    def lookup_unit_abbreviation(self, unit_id):
        return self.lookup('units', unit_id)['abbreviation']

    def get_allowed_units(self, metric_id, item_id=None):
        """Get a list of unit that can be used with the given metric (and
        optionally, item).

        Parameters
        ----------
        metric_id: int
        item_id: int, optional.


        Returns
        -------
        list of unit ids

        """
        return lib.get_allowed_units(self.access_token, self.api_host, metric_id,
                                     item_id)

    def get_data_series(self, **selection):
        """Get available data series for the given selections.

        https://developers.gro-intelligence.com/data-series-definition.html

        Parameters
        ----------
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
                   'start_date': '1975-03-01T00:00:00.000Z',
                   'end_date': '2018-05-31T00:00:00.000Z'
                 }, { ... }, ... ]

        """
        return lib.get_data_series(self.access_token, self.api_host, **selection)


    def get_data_points(self, **selection):
        return lib.get_data_points(self.access_token, self.api_host, **selection)


    def search(self, entity_type, search_terms):
        """Search for the given search term. Better matches appear first.

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions', 'sources' }
        search_terms : string

        Returns
        -------
        list of dicts

            Example::

                [{'id': 5604}, {'id': 10204}, {'id': 10210}, ....]

        """
        return lib.search(self.access_token, self.api_host,
                          entity_type, search_terms)


    def search_and_lookup(self, entity_type, search_terms, num_results=10):
        """Search for the given search terms and look up their details.

        For each result, yield a dict of the entity and it's properties.

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions', 'sources' }
        search_terms : string
        num_results: int
            Maximum number of results to return. Defaults to 10.

        Yields
        ------
        dict
            Result from :meth:`~.search` passed to :meth:`~.lookup` to get additional details.

            Example::

                { 'id': 274,
                  'contains': [779, 780, ...],
                  'name': 'Corn',
                  'definition': 'The seeds of the widely cultivated...' }

            See output of :meth:`~.lookup`. Note that as with :meth:`~.search`, the first result is
            the best match for the given search term(s).

        """
        return lib.search_and_lookup(self.access_token, self.api_host,
                                     entity_type, search_terms, num_results)


    def lookup_belongs(self, entity_type, entity_id):
        """Look up details of entities containing the given entity.

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions' }
        entity_id : int

        Yields
        ------
        dict
            Result of :meth:`~.lookup` on each entity the given entity belongs to.

            For example: For the region 'United States', one yielded result will be for
            'North America.' The format of which matches the output of :meth:`~.lookup`::

                { 'id': 15,
                  'contains': [ 1008, 1009, 1012, 1215, ... ],
                  'name': 'North America',
                  'level': 2 }

        """
        return lib.lookup_belongs(self.access_token, self.api_host, entity_type, entity_id)


    def rank_series_by_source(self, selections_list):
        """Given a list of series selections, for each unique combination excluding source, expand
        to all available sources and return them in ranked order. The order corresponds to how well
        that source covers the selection (metrics, items, regions, and time range and frequency).

        Parameters
        ----------
        series_list : list of dicts
            See the output of :meth:`~.get_data_series`.

        Yields
        ------
        dict
            The input series_list, expanded out to each possible source, ordered by coverage.

        """
        return lib.rank_series_by_source(self.access_token, self.api_host, selections_list)


    def get_geo_centre(self, region_id):
        """Given a region ID, return the geographic centre in degrees lat/lon.

        Parameters
        ----------
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
        region_id : integer

        Returns
        -------
        a geojson object or None

            Example::

                { 'type': 'GeometryCollection',
                'geometries': [{'type': 'MultiPolygon',
                                'coordinates': [[[[-38.394, -4.225], ...]]]}, ...]}

        """
        return lib.get_geojson(self.access_token, self.api_host, region_id)


    def get_descendant_regions(self, region_id, descendant_level=None,
                               include_historical=True, include_details=True):
        """Look up details of all regions of the given level contained by a region.

        Given any region by id, get all the descendant regions that are of the specified level.

        Parameters
        ----------
        region_id : integer
        descendant_level : integer, optional
            The region level of interest. See REGION_LEVELS constant. If not provided, get all
            descendants.
        include_historical : boolean, optional
            True by default. If False is specified, regions that only exist in historical data
            (e.g. the Soviet Union) will be excluded.
        include_details : boolean, optional
            True by default. Will perform a lookup() on each descendant region to find name,
            latitude, longitude, etc. If this option is set to False, only ids of descendant
            regions will be returned, which makes execution significantly faster.

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

            See output of :meth:`~.lookup`

        """
        return lib.get_descendant_regions(self.access_token, self.api_host, region_id,
                                          descendant_level, include_historical, include_details)


    def get_available_timefrequency(self, **selection):
        """Given a selection, return a list of frequencies and time ranges.
        The results are ordered by coverage-optimized ranking.

        Parameters
        ----------
        metric_id : integer, optional
        item_id : integer, optional
        region_id : integer, optional
        partner_region_id : integer, optional

        Returns
        -------
        list of dicts

            Example::

                 [{
                    'startDate': '2000-02-18T00:00:00.000Z',
                    'frequencyId': 3,
                    'endDate': '2020-03-12T00:00:00.000Z',
                    'name': '8-day'
                  }, {
                    'startDate': '2019-09-02T00:00:00.000Z',
                    'frequencyId': 1,
                    'endDate': '2020-03-09T00:00:00.000Z',
                    'name': u'daily'}, ... ]
        """
        return lib.get_available_timefrequency(self.access_token, self.api_host,
                                               **selection)

    def get_top(self, entity_type, num_results=5, **selection):
        """Find the data series with the highest cumulative value for the given time range.

        Examples::

            # To get FAO's top 5 corn-producing countries of all time:
            >>> get_top('regions', metric_id=860032, item_id=274, frequency_id=9, source_id=2)

            # To get FAO's top 5 corn-producing countries of 2014:
            >>> get_top('regions', metric_id=860032, item_id=274, frequency_id=9, source_id=2,
                        start_date='2014-01-01', end_date='2014-12-31')

            # To get the United States' top 15 exports in the decade of 2010-2019:
            >>> get_top('items', num_results=15, metric_id=20032, region_id=1215, frequency_id=9,
                        source_id=2, start_date='2010-01-01', end_date='2019-12-31')

        Parameters
        ----------
        entity_type : { 'items', 'regions' }
            The entity type to rank, all other selections being the same. Only items and regions
            are rankable at this time.
        num_results : integer, optional
            How many data series to rank. Top 5 by default.
        metric_id : integer
        item_id : integer
            Required if requesting top regions. Disallowed if requesting top items.
        region_id : integer
            Required if requesting top items. Disallowed if requesting top regions.
        partner_region_id : integer, optional
        frequency_id : integer
        source_id : integer
        start_date : string, optional
            If not provided, the cumulative value used for ranking will include data points as far
            back as the source provides.
        end_date : string, optional

        Returns
        -------
        list of dicts

            Example::

                [
                    {'metricId': 860032, 'itemId': 274, 'regionId': 1215, 'frequencyId': 9,
                     'sourceId': 2, 'value': 400, 'unitId': 14},
                    {'metricId': 860032, 'itemId': 274, 'regionId': 1215, 'frequencyId': 9,
                     'sourceId': 2, 'value': 395, 'unitId': 14},
                    {'metricId': 860032, 'itemId': 274, 'regionId': 1215, 'frequencyId': 9,
                     'sourceId': 2, 'value': 12, 'unitId': 14},
                ]

            Along with the series attributes, value and unit are also given for the total cumulative
            value the series are ranked by. You may then use the results to call
            :meth:`~.get_data_points` to get the individual time series points.
        """
        return lib.get_top(self.access_token, self.api_host, entity_type, num_results, **selection)
