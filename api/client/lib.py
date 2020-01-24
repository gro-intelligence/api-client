"""Base module for making API requests.

Client, GroClient, CropModel, and BatchClient all build on top of endpoints
exposed in this module. Helper functions or shims or derivative functionality
should appear in the client classes rather than here.
"""

from api.client import cfg
from api.client.constants import DATA_SERIES_UNIQUE_TYPES_ID, ENTITY_PROPERTIES, REGION_LEVELS
from api.client.utils import str_camel_to_snake, snake_to_camel, dict_reformat_keys, list_chunk
from builtins import str
from pkg_resources import get_distribution, DistributionNotFound
import json
import logging
import platform
import requests
import time
try:
    # functools are native in Python 3.2.3+
    from functools import lru_cache as memoize
except ImportError:
    from backports.functools_lru_cache import lru_cache as memoize


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
            param_key = str_snake_to_camel('_'.join([split_mig_key[1], 'id']))
            new_params[param_key] = migration[migration_key]
    return new_params


def get_version_info():
    versions = dict()
    # retrieve python version and api client version
    versions['python-version'] = platform.python_version()
    try:
        versions['api-client-version'] = get_distribution('gro').version
    except DistributionNotFound:
        # package is not installed
        pass
    return versions


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

    # append version info
    headers.update(get_version_info())

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
        elif data.status_code in [400, 401, 404, 500]:
            break
        else:
            logger.error('{}'.format(data), extra=log_record)
    raise Exception('Giving up on {} after {} tries: {}.'.format(
        url, retry_count, data))


@memoize(maxsize=None)
def get_allowed_units(access_token, api_host, metric_id, item_id):
    url = '/'.join(['https:', '', api_host, 'v2/units/allowed'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'metricIds': metric_id}
    if item_id:
        params['itemIds'] = item_id
    resp = get_data(url, headers, params)
    return [unit['id'] for unit in resp.json()['data']]


@memoize(maxsize=None)
def get_available(access_token, api_host, entity_type):
    url = '/'.join(['https:', '', api_host, 'v2', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()['data']


def list_available(access_token, api_host, selected_entities):
    url = '/'.join(['https:', '', api_host, 'v2/entities/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = dict([(str_snake_to_camel(key), value)
                   for (key, value) in list(selected_entities.items())])
    resp = get_data(url, headers, params)
    try:
        return resp.json()['data']
    except KeyError:
        raise Exception(resp.text)


def lookup(access_token, api_host, entity_type, entity_ids, property_names=None):
    if isinstance(entity_ids, int):
        entity_ids = [entity_ids]
    if property_names is None:
        property_names = list(ENTITY_PROPERTIES[entity_type].keys())
    responses = {}
    for property_name in property_names:
        for entity_id, property_value in lookup_property(access_token, api_host, entity_type,
                                                         entity_ids, property_name):
            responses[entity_id] = {**d.get(entity_id, {}), **{property_name: []}}
    if len(entity_ids) == 1:
        return responses[str(entity_ids[0])]
    else:
        return responses


def lookup_property(access_token, api_host, entity_type, entity_ids, property_name):
    assert entity_type in ENTITY_PROPERTIES, \
        'entity_type must be one of {}'.format(ENTITY_PROPERTIES)
    if isinstance(entity_ids, int):
        entity_ids = [entity_ids]
    else:
        assert isinstance(entity_ids, list), 'entity_ids must be a list'
        assert len(entity_ids) > 0, 'entity_ids must contain at least one element'
        assert isinstance(entity_ids[0], int), 'entity_ids must be a list of integers'
    assert property_name in ENTITY_PROPERTIES[entity_type], \
        'property_name must be one of {}'.format(ENTITY_PROPERTIES[entity_type].keys())

    url = '/'.join(['https:', '', api_host, 'v2', entity_type,
                    ENTITY_PROPERTIES[entity_type][property_name]])
    headers = {'authorization': 'Bearer ' + access_token}
    output = {}
    for id_chunk in list_chunk(entity_ids):
        params = {'ids': '[{}]'.format(','.join([str(entity_id) for entity_id in entity_ids]))}
        resp = get_data(url, headers, params)
        try:
            output.update(resp.json()['data'])
        except KeyError:
            raise Exception(resp.text)
    if len(entity_ids) == 1:
        return output[str(entity_ids[0])]
    return output


def get_params(additional_keys=[], **selection):
    """Construct http request params from dict of entity selections.

    For use with get_data_series() and rank_series_by_source().

    >>> get_params(metric_id=123, item_id=456, unit_id=14) == { 'itemId': 456, 'metricId': 123 }
    True
    >>> get_params(
    ...     ['start_date', 'end_date', 'show_revisions', 'insert_null', 'at_time']
    ...     metric_id=123, start_date='2012-01-01', unit_id=14, at_time='2019-01-01'
    ... ) == {'metricId': 123, 'startDate': '2012-01-01', 'atTime': '2019-01-01'}

    Parameters
    ----------
    metric_id : integer, optional
    item_id : integer, optional
    region_id : integer, optional
    partner_region_id : integer, optional
    source_id : integer, optional
    frequency_id : integer, optional
    additional_keys : list, optional

    Returns
    -------
    dict
        selections with valid keys converted to camelcase and invalid ones filtered out

    """
    params = {}
    for key, value in list(selection.items()):
        if key in DATA_SERIES_UNIQUE_TYPES_ID + additional_keys:
            params[str_snake_to_camel(key)] = value
    return params


def get_data_series(access_token, api_host, **selection):
    logger = get_default_logger()
    url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params(['start_date', 'end_date'], **selection)
    resp = get_data(url, headers, params)
    try:
        response = resp.json()['data']
        if any((series.get('metadata', {}).get('includes_historical_region', False)) for series in response):
            logger.warning('Some of the regions in your data call are historical, with boundaries that may be outdated. The regions may have overlapping values with current regions')
        return response
    except KeyError:
        raise Exception(resp.text)


def get_source_ranking(access_token, api_host, selections):
    """Given a series, return a list of ranked sources.

    Parameters
    ----------
    access_token : string
    api_host : string
    selections : dict

    Returns
    -------
    list of dicts
        Sources that match the selections, sorted by rank

    """
    def make_key(key):
        if key not in ('startDate', 'endDate'):
            return key + 's'
        return key
    params = dict((make_key(k), v)
                  for k, v in iter(list(get_params(['start_date', 'end_date'],
                                                   **selections).items())))
    url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
    headers = {'authorization': 'Bearer ' + access_token}
    return get_data(url, headers, params).json()


def rank_series_by_source(access_token, api_host, series_list):
    for series in series_list:
        try:
            # Remove source if selected, to consider all sources.
            series.pop('source_name', None)
            series.pop('source_id', None)
            source_ids = get_source_ranking(access_token, api_host, series)
        except ValueError:
            continue  # empty response
        for source_id in source_ids:
            # Make a copy to avoid passing the same reference each time.
            series_with_source = dict(series)
            series_with_source['source_id'] = source_id
            yield series_with_source


def list_of_series_to_single_series(series_list, add_belongs_to=False):
    """Convert list_of_series format from API back into the familiar single_series output format.

    >>> list_of_series_to_single_series([{
    ...     'series': { 'metricId': 1, 'itemId': 2, 'regionId': 3, 'unitId': 4, 'inputUnitId': 5,
    ...                 'belongsTo': { 'itemId': 22 }
    ...     },
    ...     'data': [
    ...         ['2001-01-01', '2001-12-31', 123],
    ...         ['2002-01-01', '2002-12-31', 123, '2012-01-01'],
    ...         ['2003-01-01', '2003-12-31', 123, None, {}]
    ...     ]
    ... }], True) == [
    ...   { 'start_date': '2001-01-01',
    ...     'end_date': '2001-12-31',
    ...     'value': 123,
    ...     'unit_id': 4,
    ...     'input_unit_id': 4,
    ...     'input_unit_scale': 1,
    ...     'reporting_date': None,
    ...     'metric_id': 1,
    ...     'item_id': 2,
    ...     'region_id': 3,
    ...     'partner_region_id': 0,
    ...     'frequency_id': None,
    ...     'belongs_to': { 'item_id': 22 } },
    ...   { 'start_date': '2002-01-01',
    ...     'end_date': '2002-12-31',
    ...     'value': 123,
    ...     'unit_id': 4,
    ...     'input_unit_id': 4,
    ...     'input_unit_scale': 1,
    ...     'reporting_date': '2012-01-01',
    ...     'metric_id': 1,
    ...     'item_id': 2,
    ...     'region_id': 3,
    ...     'partner_region_id': 0,
    ...     'frequency_id': None,
    ...     'belongs_to': { 'item_id': 22 } },
    ...   { 'start_date': '2003-01-01',
    ...     'end_date': '2003-12-31',
    ...     'value': 123,
    ...     'unit_id': 4,
    ...     'input_unit_id': 4,
    ...     'input_unit_scale': 1,
    ...     'reporting_date': None,
    ...     'metric_id': 1,
    ...     'item_id': 2,
    ...     'region_id': 3,
    ...     'partner_region_id': 0,
    ...     'frequency_id': None,
    ...     'belongs_to': { 'item_id': 22 } }
    ... ]
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
        belongs_to = dict_reformat_keys(series.get('series', {}).get('belongsTo', {}),
                                        str_camel_to_snake)
        for point in series.get('data', []):
            formatted_point = {
                'start_date': point[0],
                'end_date': point[1],
                'value': point[2],
                # list_of_series has unit_id in the series attributes currently. Does
                # not allow for mixed units in the same series
                'unit_id': series['series'].get('unitId', None),
                # input_unit_id and input_unit_scale are deprecated but provided for backwards
                # compatibility. unit_id should be used instead.
                'input_unit_id': series['series'].get('unitId', None),
                'input_unit_scale': 1,
                # If a point does not have reporting_date, use None
                'reporting_date': point[3] if len(point) > 3 else None,
                # Series attributes:
                'metric_id': series['series'].get('metricId', None),
                'item_id': series['series'].get('itemId', None),
                'region_id': series['series'].get('regionId', None),
                'partner_region_id': series['series'].get('partnerRegionId', 0),
                'frequency_id': series['series'].get('frequencyId', None)
                # 'source_id': series['series'].get('sourceId', None), TODO: add source to output
            }
            if add_belongs_to:
                # belongs_to is consistent with the series the user requested. So if an
                # expansion happened on the server side, the user can reconstruct what
                # results came from which request.
                formatted_point['belongs_to'] = belongs_to
            output.append(formatted_point)
    return output


def get_data_points(access_token, api_host, **selection):
    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/data'])
    params = get_params(['start_date', 'end_date', 'show_revisions', 'insert_null', 'at_time'],
                        **selection)
    params['responseType'] = 'list_of_series'
    resp = get_data(url, headers, params)
    return list_of_series_to_single_series(resp.json())


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
    url = '/'.join(['https:', '', api_host, 'v2/search', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, {'q': search_terms})
    return resp.json()


def search_and_lookup(access_token, api_host, entity_type, search_terms, num_results=10):
    search_results = search(access_token, api_host, entity_type, search_terms)
    for result in lookup(access_token, api_host, entity_type, search_results[:num_results]):
        yield result


def lookup_belongs(access_token, api_host, entity_type, entity_id):
    parent_entity_ids = lookup_property(access_token, api_host, entity_type, entity_id, 'belongsTo')
    for parent_details in lookup(access_token, api_host, entity_type, parent_entity_ids):
        yield parent_details


def get_geo_centre(access_token, api_host, region_id):
    url = '/'.join(['https:', '', api_host, 'v2', 'geocentres']
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'regionIds': region_id}
    resp = get_data(url, headers, params)
    return resp.json()['data']


@memoize(maxsize=None)
def get_geojson(access_token, api_host, region_id):
    url = '/'.join(['https:', '', api_host, 'v2/geocentres'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'includeGeojson': True, 'regionIds': region_id}
    resp = get_data(url, headers, params)
    for region in resp.json()['data']:
        return json.loads(region['geojson'])
    return None


def get_descendant_regions(access_token, api_host, region_id,
                           descendant_level=False, include_historical=True, include_details=True):
    url = '/'.join(['https:', '', api_host, 'v2/regions/contains'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'ids': [region_id]}
    if descendant_level:
        params['level'] = descendant_level
    else:
        params['distance'] = -1

    resp = get_data(url, headers, params)
    descendant_region_ids = resp.json()['data'][str(region_id)]

    # Filter out regions with the 'historical' flag set to true
    if not include_historical:
        descendant_region_ids = [
            descendant_region_id for descendant_region_id in descendant_region_ids
            if not lookup(access_token, api_host, 'regions', descendant_region_id)['historical']
        ]

    if include_details:
        return [lookup(access_token, api_host, 'regions', descendant_region_id)
                for descendant_region_id in descendant_region_ids]

    return [{'id': descendant_region_id} for descendant_region_id in descendant_region_ids]


if __name__ == '__main__':
    # To run doctests:
    # $ python lib.py -v
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
