"""Base module for making API requests.

Client, GroClient, CropModel, and BatchClient all build on top of endpoints
exposed in this module. Helper functions or shims or derivative functionality
should appear in the client classes rather than here.
"""

from builtins import map
from builtins import str
from api.client import cfg
import json
import re
import logging
import requests
import time
try:
    # functools are native in Python 3.2.3+
    from functools import lru_cache as memoize
except ImportError:
    from backports.functools_lru_cache import lru_cache as memoize

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

"""Core ontology types, which can be navigated via a graph:"""
GRAPH_TYPES_SINGULAR = ['metric', 'item', 'region']
"""partner_region is just another type of 'region' so graph concepts also apply to it:"""
EXPANDABLE_TYPES_SINGULAR = GRAPH_TYPES_SINGULAR + ['partner_region']
"""frequency and source are part of the unique key for a data series but have no graph:"""
SERIES_TYPES_SINGULAR = EXPANDABLE_TYPES_SINGULAR + ['frequency', 'source']
"""units are not part of the unique key for a data series, but lookup can get info about them:"""
LOOKUP_TYPES_SINGULAR = SERIES_TYPES_SINGULAR + ['unit']
"""Series types (without unit) in type_id format, i.e. 'metric_id':"""
SERIES_TYPES_SINGULAR_ID = [type_singular+'_id' for type_singular in SERIES_TYPES_SINGULAR]


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


@memoize(maxsize=None)
def camel_to_snake(term):
    """Convert a string from camelCase to snake_case.

    >>> camel_to_snake('partnerRegionId')
    'partner_region_id'

    >>> camel_to_snake('partner_region_id')
    'partner_region_id'

    Parameters
    ----------
    term : string
        A camelCase string

    Returns
    -------
    string
        A new snake_case string

    """
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', re.sub('(.)([A-Z][a-z]+)', r'\1_\2', term)).lower()


def camel_to_snake_dict(obj):
    """Convert a dictionary's keys from camelCase to snake_case.

    >>> camel_to_snake_dict({'belongsTo': {'metricId': 4}})
    {'belongs_to': {'metricId': 4}}

    Parameters
    ----------
    term : dict
        A dictionary with camelCase keys

    Returns
    -------
    dict
        A new dictionary with snake_case keys

    """
    return dict((camel_to_snake(key), value) for key, value in obj.items())


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
    ... ) == {'metricId': 15, 'sourceId': 2, 'itemId': 145}
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
        if data.status_code == 204:
            logger.warning('No Content', extra=log_record)
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
            logger.error('{}'.format(data), extra=log_record)
    raise Exception('Giving up on {} after {} tries: {}.'.format(
        url, retry_count, data))


@memoize(maxsize=None)
def get_available(access_token, api_host, entity_type):
    """See Client.get_available()."""
    url = '/'.join(['https:', '', api_host, 'v2', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()['data']


def list_available(access_token, api_host, selected_entities):
    """See Client.list_available()."""
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
    """See Client.lookup()."""
    url = '/'.join(['https:', '', api_host, 'v2', entity_type, str(entity_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    try:
        return resp.json()['data']
    except KeyError:
        raise Exception(resp.text)


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
    start_date: string, optional
    end_date: string, optional

    Returns
    -------
    dict
        selections with valid keys converted to camelcase and invalid ones filtered out

    """
    params = {}
    for key, value in list(selection.items()):
        if key in SERIES_TYPES_SINGULAR_ID+['start_date', 'end_date']:
            params[snake_to_camel(key)] = value
    return params


def get_data_call_params(**selection):
    """Construct http request params from dict of entity selections.

    For use with get_data_points().

    >>> get_data_call_params(metric_id=123, start_date='2012-01-01', unit_id=14) == {
    ...     'metricId': 123, 'startDate': '2012-01-01', 'responseType': 'list_of_series'
    ... }
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
    params['responseType'] = 'list_of_series'
    return params


def get_data_series(access_token, api_host, **selection):
    """See Client.get_data_series()."""
    logger = get_default_logger()
    url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params_from_selection(**selection)
    resp = get_data(url, headers, params)
    try:
        response = resp.json()['data']
        if any((series.get('metadata', {}).get('includes_historical_region', False))
               for series in response):
            logger.warning('Some of the regions in your data call are historical, with boundaries '
                           'that may be outdated. The regions may have overlapping values with '
                           'current regions')
        return response
    except KeyError:
        raise Exception(resp.text)


def get_source_ranking(access_token, api_host, series):
    """Given a series, return a list of ranked sources.

    Parameters
    ----------
    access_token : string
    api_host : string
    series : dict
        Series to calculate source raking for.

    Returns
    -------
    List of dicts
        sources that match the series parameters, sorted by rank.

    """
    def make_key(key):
        if key not in ('startDate', 'endDate'):
            return key + 's'
        return key
    params = dict((make_key(k), v) for k, v in iter(list(
        get_params_from_selection(**series).items())))
    url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
    headers = {'authorization': 'Bearer ' + access_token}
    return get_data(url, headers, params).json()


def rank_series_by_source(access_token, api_host, series_list):
    # We sort the internal tuple representations of the dictionaries because
    # otherwise when we call set() we end up with duplicates if iteritems()
    # returns a different order for the same dictionary. See test case.
    selections_sorted = set(tuple(sorted(
        [k_v for k_v in iter(list(single_series.items()))
         if k_v[0] not in ('source_id', 'source_name')],
        key=lambda x: x[0])) for single_series in series_list)

    for series in map(dict, selections_sorted):
        try:
            source_ids = get_source_ranking(access_token, api_host, series)
        except ValueError:
            continue  # empty response
        for source_id in source_ids:
            # Make a copy to avoid passing the same reference each time.
            series_with_source = dict(series)
            series_with_source['source_id'] = source_id
            yield series_with_source


def format_list_of_series(series_list):
    """Convert list_of_series format from API back into the familiar single_series output format.

    >>> format_list_of_series([{
    ...     'series': { 'metricId': 1, 'itemId': 2, 'regionId': 3, 'belongsTo': { 'itemId': 22 } },
    ...     'data': [
    ...         ['2001-01-01', '2001-12-31', 123]
    ...     ]
    ... }]) == [
    ...   { 'start_date': '2001-01-01',
    ...     'end_date': '2001-12-31',
    ...     'value': 123,
    ...     'unit_id': None,
    ...     'reporting_date': None,
    ...     'metric_id': 1,
    ...     'item_id': 2,
    ...     'region_id': 3,
    ...     'partner_region_id': 0,
    ...     'frequency_id': None,
    ...     'source_id': None,
    ...     'belongs_to': { 'item_id': 22 }
    ... } ]
    True

    """
    if not isinstance(series_list, list):
        # If the output is an error or None or something else that's not a list, just propagate
        return series_list
    output = []
    for series in series_list:
        if not (isinstance(series, dict) and isinstance(series.get('data', []), list)):
            continue
        # All the belongsTo keys are in camelCase. Convert them to snake_case.
        # Only need to do this once per series, so do this outside of the list
        # comprehension and save to a variable to avoid duplicate work:
        belongs_to = camel_to_snake_dict(series.get('series', {}).get('belongsTo', {}))
        output += [{
            'start_date': point[0],
            'end_date': point[1],
            'value': point[2],
            # list_of_series has unit_id in the series attributes currently. Does
            # not allow for mixed units in the same series
            'unit_id': series['series'].get('unitId', None),
            # If a point does not have reporting_date, use None
            'reporting_date': point[3] if len(point) > 3 else None,
            # Series attributes:
            'metric_id': series['series'].get('metricId', None),
            'item_id': series['series'].get('itemId', None),
            'region_id': series['series'].get('regionId', None),
            'partner_region_id': series['series'].get('partnerRegionId', 0),
            'frequency_id': series['series'].get('frequencyId', None),
            'source_id': series['series'].get('sourceId', None),
            # belongs_to is consistent with the series the user requested. So if an
            # expansion happened on the server side, the user can reconstruct what
            # results came from which request.
            'belongs_to': belongs_to
        } for point in series.get('data', [])]
    return output


def get_data_points(access_token, api_host, **selection):
    """See GroClient.get_data_points()."""
    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/data'])
    params = get_data_call_params(**selection)
    resp = get_data(url, headers, params)
    return format_list_of_series(resp.json())


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
    """See Client.search()."""
    url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, {'q': search_terms})
    return resp.json()


def search_and_lookup(access_token, api_host, entity_type, search_terms, num_results=10):
    """See Client.search_and_lookup()."""
    search_results = search(access_token, api_host, entity_type, search_terms)
    for result in search_results[:num_results]:
        yield lookup(access_token, api_host, entity_type, result['id'])


def lookup_belongs(access_token, api_host, entity_type, entity_id):
    """See Client.lookup_belongs()."""
    url = '/'.join(['https:', '', api_host, 'v2', entity_type, 'belongs-to'])
    params = {'ids': str(entity_id)}
    headers = {'authorization': 'Bearer ' + access_token}
    parents = get_data(url, headers, params).json().get('data').get(str(entity_id), [])
    for parent_entity_id in parents:
        yield lookup(access_token, api_host, entity_type, parent_entity_id)


def get_geo_centre(access_token, api_host, region_id):
    """See Client.get_geo_centre()."""
    url = '/'.join(['https:', '', api_host, 'v2/geocentres?regionIds=' +
                    str(region_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()['data']


@memoize(maxsize=None)
def get_geojson(access_token, api_host, region_id):
    """See Client.get_geojson()."""
    url = '/'.join(['https:', '', api_host, 'v2/geocentres?includeGeojson=True&regionIds=' +
                    str(region_id)])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    for region in resp.json()['data']:
        return json.loads(region['geojson'])
    return None


def get_descendant_regions(access_token, api_host, region_id,
                           descendant_level=False, include_historical=True):
    """See Client.get_descendant_regions()."""
    descendants = []
    region = lookup(access_token, api_host, 'regions', region_id)
    for member_id in region['contains']:
        member = lookup(access_token, api_host, 'regions', member_id)
        if (not include_historical and member['historical']):
            continue
        if not descendant_level or descendant_level == member['level']:
            descendants.append(member)
        if not descendant_level or member['level'] < descendant_level:
            descendants += get_descendant_regions(
                access_token, api_host, member_id, descendant_level, include_historical)
    return descendants


if __name__ == '__main__':
    # To run doctests:
    # $ python lib.py -v
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
