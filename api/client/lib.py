"""Base module for making API requests.

Client, GroClient, CropModel, and BatchClient all build on top of endpoints
exposed in this module. Helper functions or shims or derivative functionality
should appear in the client classes rather than here.
"""

from builtins import map
from builtins import str
from api.client import cfg
import json
import logging
import requests
import time
try:
    # functools are native in Python 3.2.3+
    from functools import lru_cache as memoize
except ImportError:
    from backports.functools_lru_cache import lru_cache as memoize

CROP_CALENDAR_METRIC_ID = 2260063

REGION_LEVELS = {
    'world': 1,
    'continent': 2,
    'country': 3,
    'province': 4,  # Equivalent to state in the United States
    'district': 5,  # Equivalent to county in the United States
    'city': 6,
    'market': 7,
    'other': 8,
    'coordinate': 9
}


def get_default_logger():
    """Get a logging object using the default log level set in cfg.

    https://docs.python.org/3/library/logging.html

    Returns
    -------
    logger : logging.Logger

    """
    logger = logging.getLogger(__name__)
    logger.setLevel(cfg.DEFAULT_LOG_LEVEL)
    if not logger.handlers:
        stderr_handler = logging.StreamHandler()
        logger.addHandler(stderr_handler)
    return logger


def get_access_token(api_host, user_email, user_password, logger=None):
    """Request an access token.

    Parameters
    ----------
    api_host : string
        The API host's url, excluding 'https://'
        ex. 'api.gro-intelligence.com'
    user_email : string
        Email address associated with user's Gro account
    user_password : string
        Password for user's Gro account
    logger : logging.Logger
        Alternative logger object if wanting to use a non-default one.
        Otherwise get_default_logger() will be used.

    Returns
    -------
    accessToken : string

    """
    retry_count = 0
    if not logger:
        logger = get_default_logger()
    while retry_count < cfg.MAX_RETRIES:
        get_api_token = requests.post('https://' + api_host + '/api-token',
                                      data={'email': user_email,
                                            'password': user_password})
        if get_api_token.status_code == 200:
            logger.debug('Authentication succeeded in get_access_token')
            return get_api_token.json()['data']['accessToken']
        else:
            logger.warning('Error in get_access_token: {}'.format(
                get_api_token))
        retry_count += 1
    raise Exception('Giving up on get_access_token after {0} tries.'.format(
        retry_count))


def redirect(old_params, migration):
    """Update query parameters to follow a redirection response from the API.

    >>> redirect(
    ...     {'metricId': 14, 'sourceId': 2, 'itemId': 145},
    ...     {'old_metric_id': 14, 'new_metric_id': 15, 'source_id': 2}
    ... ) == {'sourceId': 2, 'itemId': 145, 'metricId': 15}
    True

    Parameters
    ----------
    old_params : dict
        The original parameters provided to the API request
    migration : dict
        The body of the 301 response indicating which of the inputs have been
        migrated and what values they have been migrated to

    Returns
    -------
    new_params : dict
        The mutated params object with values replaced according to the
        redirection instructions provided by the API

    """
    new_params = old_params.copy()
    for migration_key in migration:
        split_mig_key = migration_key.split('_')
        if split_mig_key[0] == 'new':
            param_key = snake_to_camel('_'.join([split_mig_key[1], 'id']))
            new_params[param_key] = migration[migration_key]
    return new_params


def get_data(url, headers, params=None, logger=None):
    """General 'make api request' function.

    Assigns headers and builds in retries and logging.

    Parameters
    ----------
    url : string
    headers : dict
    params : dict
    logger : logging.Logger

    Returns
    -------
    data : list or dict

    """
    base_log_record = dict(route=url, params=params)
    retry_count = 0
    if not logger:
        logger = get_default_logger()
        logger.debug(url)
        logger.debug(params)
    while retry_count < cfg.MAX_RETRIES:
        start_time = time.time()
        data = requests.get(url, params=params, headers=headers, timeout=None)
        elapsed_time = time.time() - start_time
        log_record = dict(base_log_record)
        log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
        log_record['retry_count'] = retry_count
        log_record['status_code'] = data.status_code
        if data.status_code == 200:
            logger.debug('OK', extra=log_record)
            return data
        retry_count += 1
        log_record['tag'] = 'failed_gro_api_request'
        if retry_count < cfg.MAX_RETRIES:
            logger.warning(data.text, extra=log_record)
        if data.status_code == 429:
            time.sleep(2 ** retry_count)  # Exponential backoff before retrying
        elif data.status_code == 301:
            new_params = redirect(params, data.json()['data'][0])
            logger.warning('Redirecting {} to {}'.format(params, new_params), extra=log_record)
            params = new_params
        elif data.status_code in [404, 401, 500]:
            break
        else:
            logger.error(data.text, extra=log_record)
    raise Exception('Giving up on {} after {} tries. Error is: {}.'.format(
        url, retry_count, data.text))


@memoize(maxsize=None)
def get_available(access_token, api_host, entity_type):
    """List the first 5000 available entities of the given type.

    Parameters
    ----------
    access_token : string
    api_host : string
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
    url = '/'.join(['https:', '', api_host, 'v2', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()['data']


def list_available(access_token, api_host, selected_entities):
    """List available entities given some selected entities.

    Given one or more selections, return entities combinations that have
    data for the given selections.

    Parameters
    ----------
    access_token : string
    api_host : string
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
    url = '/'.join(['https:', '', api_host, 'v2/entities/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = dict([(snake_to_camel(key), value)
                   for (key, value) in list(selected_entities.items())])
    resp = get_data(url, headers, params)
    try:
        return resp.json()['data']
    except KeyError:
        raise Exception(resp.text)


@memoize(maxsize=None)
def lookup(access_token, api_host, entity_type, entity_id):
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
    url = '/'.join(['https:', '', api_host, 'v2', entity_type, str(entity_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    try:
        return resp.json()['data']
    except KeyError:
        raise Exception(resp.text)


@memoize(maxsize=None)
def snake_to_camel(term):
    """Convert a string from snake_case to camelCase.

    >>> snake_to_camel('hello_world')
    'helloWorld'

    Parameters
    ----------
    term : string

    Returns
    -------
    string

    """
    camel = term.split('_')
    return ''.join(camel[:1] + list([x[0].upper()+x[1:] for x in camel[1:]]))


def get_params_from_selection(**selection):
    """Construct http request params from dict of entity selections.

    For use with get_data_series() and rank_series_by_source().

    >>> get_params_from_selection(
    ...     metric_id=123, item_id=456, unit_id=14
    ... ) == { 'itemId': 456, 'metricId': 123 }
    True

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
    dict
        selections with valid keys converted to camelcase and invalid ones filtered out

    """
    params = {}
    for key, value in list(selection.items()):
        if key in ('region_id', 'partner_region_id', 'item_id', 'metric_id',
                   'source_id', 'frequency_id'):
            params[snake_to_camel(key)] = value
    return params


def get_crop_calendar_params(**selection):
    """Construct http request params from dict of entity selections.

    For use with get_crop_calendar_data_points()

    >>> get_crop_calendar_params(
    ...     metric_id=123, item_id=456, region_id=14
    ... ) == { 'itemId': 456, 'regionId': 14 }
    True

    Parameters
    ----------
    item_id : integer
    region_id : integer

    Returns
    -------
    dict
        selections with valid keys converted to camelcase and invalid ones
        filtered out

    """
    params = {}
    for key, value in list(selection.items()):
        if key in ('region_id', 'item_id'):
            params[snake_to_camel(key)] = value
    return params


def get_data_call_params(**selection):
    """Construct http request params from dict of entity selections.

    For use with get_data_points().

    >>> get_data_call_params(
    ...     metric_id=123, start_date='2012-01-01', unit_id=14
    ... ) == {'startDate': '2012-01-01', 'metricId': 123}
    True

    Parameters
    ----------
    metric_id : integer
    item_id : integer
    region_id : integer
    partner_region_id : integer
    source_id : integer
    frequency_id : integer
    start_date : string, optional
    end_date : string, optional
    show_revisions : boolean, optional
    insert_null : boolean, optional
    at_time : string, optional

    Returns
    -------
    dict
        selections with valid keys converted to camelcase and invalid ones filtered out

    """
    params = get_params_from_selection(**selection)
    for key, value in list(selection.items()):
        if key in ('start_date', 'end_date', 'show_revisions', 'insert_null', 'at_time'):
            params[snake_to_camel(key)] = value
    return params


def get_data_series(access_token, api_host, **selection):
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
    url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params_from_selection(**selection)
    resp = get_data(url, headers, params)
    try:
        return resp.json()['data']
    except KeyError:
        raise Exception(resp.text)


def rank_series_by_source(access_token, api_host, series_list):
    """Given a list of series, return them in source-ranked order.

    If there are multiple sources for the same selection, the prefered source
    comes first. Differences other than source_id are not affected.

    Parameters
    ----------
    access_token : string
    api_host : api_host
    series_list : list of dicts
        See output of get_data_series()

    Yields
    ------
    dict
        The input series_list but reordered by source rank

    """
    # We sort the internal tuple representations of the dictionaries because
    # otherwise when we call set() we end up with duplicates if iteritems()
    # returns a different order for the same dictionary. See test case.
    selections_sorted = set(tuple(sorted(
        [k_v for k_v in iter(list(single_series.items())) if k_v[0] !=
            'source_id'],
        key=lambda x: x[0])) for single_series in series_list)

    for series in map(dict, selections_sorted):
        url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
        headers = {'authorization': 'Bearer ' + access_token}
        params = dict((k + 's', v) for k, v in iter(list(
            get_params_from_selection(**series).items())))
        source_ids = get_data(url, headers, params).json()
        for source_id in source_ids:
            # Make a copy to avoid passing the same reference each time.
            series_with_source = dict(series)
            series_with_source['source_id'] = source_id
            yield series_with_source


def format_crop_calendar_response(resp):
    """Make cropcalendar output a format similar to get_data_points().

    >>> format_crop_calendar_response([{
    ...     'metricId': 2260063,
    ...     'itemId': 274,
    ...     'regionId': 13051,
    ...     'sourceId': 5,
    ...     'frequencyId': 15,
    ...     'data': [{
    ...         'sageItem': 'Corn',
    ...         'plantingStartDate': '2000-03-04',
    ...         'plantingEndDate': '2000-05-17',
    ...         'harvestingStartDate': '2000-07-20',
    ...         'harvestingEndDate': '2000-11-01',
    ...         'multiYear': False
    ...     }]
    ... }]) == [{
    ...     'metric_id': 2260063,
    ...     'item_id': 274,
    ...     'region_id': 13051,
    ...     'frequency_id': 15,
    ...     'source_id': 5,
    ...     'start_date': '2000-03-04',
    ...     'end_date': '2000-05-17',
    ...     'value': 'planting',
    ...     'input_unit_id': None,
    ...     'input_unit_scale': None,
    ...     'reporting_date': None
    ... }, {
    ...     'metric_id': 2260063,
    ...     'item_id': 274,
    ...     'region_id': 13051,
    ...     'frequency_id': 15,
    ...     'source_id': 5,
    ...     'start_date': '2000-07-20',
    ...     'end_date': '2000-11-01',
    ...     'value': 'harvesting',
    ...     'input_unit_id': None,
    ...     'input_unit_scale': None,
    ...     'reporting_date': None
    ... }]
    True

    Parameters
    ----------
    resp : list of dicts
        The output from /v2/cropcalendar/data. See doctest

    Returns
    -------
    points : list of dicts
        The input ``resp`` dicts with keys modified to match the get_data_points
        output keys. Splits each point with plantingStartDate, plantingEndDate,
        harvestingStartDate, and harvestingEndDate into two points with start
        and end date where the value is the state of the crop as a string.

    """
    points = []
    for point in resp:
        # A single point may have multiple data entries if there are multiple
        # harvests
        for dataEntry in point['data']:
            # Some start/end dates can be undefined (ex: {regionId: 12314,
            # itemId: 95} - Wheat in Alta, Russia). Those are returned as empty
            # strings, so here I am checking for that and replacing those cases
            # with Nones. Also, in some cases both start AND end are undefined,
            # in which case I am excluding the data point entirely.
            if (dataEntry['plantingStartDate'] != '' or
                    dataEntry['plantingEndDate'] != ''):
                points.append({
                    'metric_id': point['metricId'],
                    'item_id': point['itemId'],
                    'region_id': point['regionId'],
                    'frequency_id': point['frequencyId'],
                    'source_id': point['sourceId'],
                    'start_date': (dataEntry['plantingStartDate']
                                   if dataEntry['plantingStartDate'] != ''
                                   else None),
                    'end_date': (dataEntry['plantingEndDate']
                                 if dataEntry['plantingEndDate'] != ''
                                 else None),
                    'value': 'planting',
                    'input_unit_id': None,
                    'input_unit_scale': None,
                    'reporting_date': None
                })
            if (dataEntry['harvestingStartDate'] != '' or
                    dataEntry['harvestingEndDate'] != ''):
                points.append({
                    'metric_id': point['metricId'],
                    'item_id': point['itemId'],
                    'region_id': point['regionId'],
                    'frequency_id': point['frequencyId'],
                    'source_id': point['sourceId'],
                    'start_date': (dataEntry['harvestingStartDate']
                                   if dataEntry['harvestingStartDate'] != ''
                                   else None),
                    'end_date': (dataEntry['harvestingEndDate']
                                 if dataEntry['harvestingEndDate'] != ''
                                 else None),
                    'value': 'harvesting',
                    'input_unit_id': None,
                    'input_unit_scale': None,
                    'reporting_date': None
                })
    return points


def get_crop_calendar_data_points(access_token, api_host, **selection):
    """Get crop calendar data.

    Has different input/output from the regular /v2/data call, so this
    normalizes the interface and output format to make compatible
    get_data_points().

    Parameters
    ----------
    access_token : string
    api_host : string
    selection : dict
        See get_crop_calendar_params() input

    Returns
    -------
    list of dicts
        See format_crop_calendar_response() output

    """
    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/cropcalendar/data'])
    params = get_crop_calendar_params(**selection)
    resp = get_data(url, headers, params)
    return format_crop_calendar_response(resp.json())


def get_data_points(access_token, api_host, **selection):
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
    if(selection['metric_id'] == CROP_CALENDAR_METRIC_ID):
        return get_crop_calendar_data_points(access_token, api_host,
                                             **selection)

    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/data'])
    params = get_data_call_params(**selection)
    resp = get_data(url, headers, params)
    return resp.json()


@memoize(maxsize=None)
def universal_search(access_token, api_host, search_terms):
    """Search across all entity types for the given terms.

    Parameters
    ----------
    access_token : string
    api_host : string
    search_terms : string

    Returns
    -------
    list of [id, entity_type] pairs

        Example::

            [[5604, 'item'], [10204, 'item'], [410032, 'metric'], ....]

    """
    url_pieces = ['https:', '', api_host, 'v2/search']
    url = '/'.join(url_pieces)
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, {'q': search_terms})
    return resp.json()


@memoize(maxsize=None)
def search(access_token, api_host, entity_type, search_terms):
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
    url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, {'q': search_terms})
    return resp.json()


def search_and_lookup(access_token, api_host, entity_type, search_terms, num_results=10):
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
    search_results = search(access_token, api_host, entity_type, search_terms)
    for result in search_results[:num_results]:
        yield lookup(access_token, api_host, entity_type, result['id'])


def lookup_belongs(access_token, api_host, entity_type, entity_id):
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
    url = '/'.join(['https:', '', api_host, 'v2', entity_type, 'belongs-to'])
    params = {'ids': str(entity_id)}
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, params)
    for parent_entity_id in resp.json().get('data').get(str(entity_id), []):
        yield lookup(access_token, api_host, entity_type, parent_entity_id)


def get_geo_centre(access_token, api_host, region_id):
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
    url = '/'.join(['https:', '', api_host, 'v2/geocentres?regionIds=' +
                    str(region_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()['data']


@memoize(maxsize=None)
def get_geojson(access_token, api_host, region_id):
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
    url = '/'.join(['https:', '', api_host, 'v2/geocentres?includeGeojson=True&regionIds=' +
                    str(region_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    for region in resp.json()['data']:
        return json.loads(region['geojson'])
    return None


def get_descendant_regions(access_token, api_host, region_id,
                           descendant_level, include_historical):
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
    descendants = []
    region = lookup(access_token, api_host, 'regions', region_id)
    for member_id in region['contains']:
        member = lookup(access_token, api_host, 'regions', member_id)
        if (not include_historical and member['historical']):
            pass
        elif descendant_level == member['level']:
            descendants.append(member)
        elif member['level'] < descendant_level:
            descendants += get_descendant_regions(
                access_token, api_host, member_id, descendant_level, include_historical)
    return descendants


if __name__ == '__main__':
    # To run doctests:
    # $ python lib.py -v
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
