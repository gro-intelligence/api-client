"""Base module for making API requests.

GroClient and CropModel build on top of endpoints exposed in this module.
Helper functions or shims or derivative functionality should appear in the client classes rather
than here.
"""

from builtins import str
from groclient import cfg
from collections import OrderedDict
from groclient.constants import REGION_LEVELS, DATA_SERIES_UNIQUE_TYPES_ID
import groclient.utils
import json
import logging
import requests
import time
import platform


from pkg_resources import get_distribution, DistributionNotFound
from typing import List, Union

try:
    # functools are native in Python 3.2.3+
    from functools import lru_cache as memoize
except ImportError:
    from backports.functools_lru_cache import lru_cache as memoize


# Interpreter and API client library version information.
#
# This is global so we only call get_distribution() once at module load time.
# This is a workaround for a curious bug: in specific situations, calling
# get_distribution() while tornado's event loop is running seems to result in
# GroClient's __del__ method running while the object is still in scope,
# resulting in `fetch() called on closed AsyncHTTPClient` errors upon
# subsequent uses of _async_http_client.
_VERSIONS = {'python-version': platform.python_version()}
try:
    _VERSIONS['api-client-version'] = get_distribution('groclient').version
except DistributionNotFound:
    pass


class APIError(Exception):
    def __init__(self, response, retry_count, url, params):
        self.response = response
        self.retry_count = retry_count
        self.url = url
        self.params = params
        self.status_code = response.status_code if hasattr(response, 'status_code') else None
        try:
            json_content = self.response.json()
            # 'error' should be something like 'Not Found' or 'Bad Request'
            self.message = json_content.get('error', '')
            # Some error responses give additional info.
            # For example, a 400 Bad Request might say "metricId is required"
            if 'message' in json_content:
                self.message += ': {}'.format(json_content['message'])
        except Exception:
            # If the error message can't be parsed, fall back to a generic "giving up" message.
            self.message = 'Giving up on {} after {} {}: {}'.format(
                self.url, self.retry_count, 'retry' if self.retry_count == 1 else 'retries', response
            )


def get_default_logger():
    """Get a logging object using the default log level set in cfg.

    https://docs.python.org/3/library/logging.html

    Returns
    -------
    logger : logging.Logger

    """
    logger = logging.getLogger(__name__)
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
    while retry_count <= cfg.MAX_RETRIES:
        get_api_token = requests.post(
            'https://' + api_host + '/api-token', data={'email': user_email, 'password': user_password}
        )
        if get_api_token.status_code == 200:
            logger.debug('Authentication succeeded in get_access_token')
            return get_api_token.json()['data']['accessToken']

        logger.warning(f'Error in get_access_token: {get_api_token}')
        retry_count += 1
    raise Exception(f'Giving up on get_access_token after {retry_count} tries.')


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
            param_key = groclient.utils.str_snake_to_camel('_'.join([split_mig_key[1], 'id']))
            new_params[param_key] = migration[migration_key]
    return new_params


def get_version_info():
    return _VERSIONS.copy()


def convert_value(value, from_convert_factor, to_convert_factor):
    value_in_base_unit = (value * from_convert_factor.get("factor")) + from_convert_factor.get("offset", 0)

    return float(value_in_base_unit - to_convert_factor.get("offset", 0)) / to_convert_factor.get("factor")


def get_data(url, headers, params=None, logger=None, stream=False):
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
    while retry_count <= cfg.MAX_RETRIES:
        start_time = time.time()
        try:
            response = requests.get(url, params=params, headers=headers, timeout=None, stream=stream)
        except Exception as e:
            response = e
        elapsed_time = time.time() - start_time
        status_code = response.status_code if hasattr(response, 'status_code') else None
        log_record = dict(base_log_record)
        log_record['elapsed_time_in_ms'] = 1000 * elapsed_time
        log_record['retry_count'] = retry_count
        log_record['status_code'] = status_code
        if status_code == 200:  # Success
            logger.debug('OK', extra=log_record)
            return response
        if status_code in [204, 206]:  # Success with a caveat - warning
            log_msg = {204: 'No Content', 206: 'Partial Content'}[status_code]
            logger.warning(log_msg, extra=log_record)
            return response
        log_record['tag'] = 'failed_gro_api_request'
        if retry_count < cfg.MAX_RETRIES:
            logger.warning(response.text if hasattr(response, 'text') else response, extra=log_record)
        if status_code in [400, 401, 402, 404]:
            break  # Do not retry
        if status_code == 301:
            new_params = redirect(params, response.json()['data'][0])
            logger.warning('Redirecting {} to {}'.format(params, new_params), extra=log_record)
            params = new_params
        else:
            logger.warning('{}'.format(response), extra=log_record)
            if retry_count > 0:
                # Retry immediately on first failure.
                # Exponential backoff before retrying repeatedly failing requests.
                time.sleep(2**retry_count)
        retry_count += 1
    raise APIError(response, retry_count, url, params)


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
    params = dict(
        [(groclient.utils.str_snake_to_camel(key), value) for (key, value) in list(selected_entities.items())]
    )
    resp = get_data(url, headers, params)
    try:
        return resp.json()['data']
    except KeyError:
        raise Exception(resp.text)


@memoize(maxsize=None)
def lookup_single(access_token, api_host, entity_type, entity_id):
    url = '/'.join(['https:', '', api_host, 'v2', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'ids': [entity_id]}
    resp = get_data(url, headers, params)
    try:
        return resp.json()['data'].get(str(entity_id))
    except KeyError:
        raise Exception(resp.text)


def lookup_batch(access_token, api_host, entity_type, entity_ids):
    url = '/'.join(['https:', '', api_host, 'v2', entity_type])
    headers = {'authorization': 'Bearer ' + access_token}
    all_results = {}
    for id_batch in groclient.utils.list_chunk(entity_ids):
        params = {'ids': id_batch}
        resp = get_data(url, headers, params)
        result = resp.json()['data']
        for id_str in result.keys():
            all_results[id_str] = result[id_str]
    return all_results


def lookup(access_token, api_host, entity_type, entity_ids):
    try:  # Convert iterable types like numpy arrays or tuples into plain lists
        entity_ids = list(entity_ids)
        return lookup_batch(access_token, api_host, entity_type, entity_ids)
    except TypeError:  # Convert anything else, like strings or numpy integers, into plain integers
        entity_id = int(entity_ids)
        # If an integer is given, return only the dict with that id
        return lookup_single(access_token, api_host, entity_type, entity_id)


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
        if key in (
            'region_id',
            'partner_region_id',
            'item_id',
            'metric_id',
            'source_id',
            'frequency_id',
            'start_date',
            'end_date',
        ):
            params[groclient.utils.str_snake_to_camel(key)] = value
    return params


def get_data_call_params(**selection):
    """Construct http request params from dict of entity selections.

    For use with get_data_points().

    >>> get_data_call_params(
    ...     metric_id=123, start_date='2012-01-01', unit_id=14
    ... ) == {'startDate': '2012-01-01', 'metricId': 123, 'responseType': 'list_of_series'}
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
    reporting_history : boolean, optional
    complete_history : boolean, optional
    insert_null : boolean, optional
    show_metadata : boolean, optional
    at_time : string, optional,
    available_since : string, optional

    Returns
    -------
    dict
        selections with valid keys converted to camelcase and invalid ones filtered out

    """
    params = get_params_from_selection(**selection)
    for key, value in list(selection.items()):
        if key == 'show_metadata':
            params[groclient.utils.str_snake_to_camel('show_meta_data')] = value
        elif key == 'complete_history':
            params['showHistory'] = value
        elif key in ('show_revisions', 'reporting_history'):
            params['showReportingDate'] = value
        elif key in ('start_date', 'end_date', 'insert_null', 'at_time', 'available_since', 'coverage_threshold'):
            params[groclient.utils.str_snake_to_camel(key)] = value
    params['responseType'] = 'list_of_series'
    return params


def get_data_series(access_token, api_host, **selection):
    logger = get_default_logger()
    url = '/'.join(['https:', '', api_host, 'v2/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params_from_selection(**selection)
    resp = get_data(url, headers, params)
    try:
        response = resp.json()['data']
        if any((series.get('metadata', {}).get('includes_historical_region', False)) for series in response):
            logger.warning(
                'Data series have some historical regions, ' 'see https://developers.gro-intelligence.com/faq.html'
            )
        return response
    except KeyError:
        raise Exception(resp.text)


def stream_data_series(access_token, api_host, chunk_size=None, **selection):
    logger = get_default_logger()
    url = '/'.join(['https:', '', api_host, 'v2/stream/data_series/list'])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params_from_selection(**selection)
    if type(chunk_size) == int and chunk_size > 1:
        params['chunkSize'] = chunk_size
    resp = get_data(url, headers, params, logger, True)
    try:
        for line in resp.iter_lines(decode_unicode=True):
            if line:
                current_ds_list = json.loads(line)
                if any(
                    (series.get('metadata', {}).get('includes_historical_region', False)) for series in current_ds_list
                ):
                    logger.warning(
                        'Data series have some historical regions, '
                        'see https://developers.gro-intelligence.com/faq.html'
                    )
                yield current_ds_list
    except KeyError:
        raise Exception(resp.text)


def get_top(access_token, api_host, entity_type, num_results=5, **selection):
    url = '/'.join(['https:', '', api_host, 'v2/top/{}'.format(entity_type)])
    headers = {'authorization': 'Bearer ' + access_token}
    params = get_params_from_selection(**selection)
    params['n'] = num_results
    resp = get_data(url, headers, params)
    try:
        return resp.json()
    except KeyError as e:
        raise Exception(resp.text) from e


def make_key(key):
    if key not in ('startDate', 'endDate'):
        return key + 's'
    return key


def get_source_ranking(access_token, api_host, series):
    """Given a series, return a list of ranked sources.

    :param access_token: API access token.
    :param api_host: API host.
    :param series: Series to calculate source raking for.
    :return: List of sources that match the series parameters, sorted by rank.
    """
    params = dict((make_key(k), v) for k, v in iter(list(get_params_from_selection(**series).items())))
    url = '/'.join(['https:', '', api_host, 'v2/available/sources'])
    headers = {'authorization': 'Bearer ' + access_token}
    return get_data(url, headers, params).json()


def rank_series_by_source(access_token, api_host, selections_list):
    series_map = OrderedDict()
    for selection in selections_list:
        series_key = '.'.join(
            [json.dumps(selection.get(type_id)) for type_id in DATA_SERIES_UNIQUE_TYPES_ID if type_id != 'source_id']
        )
        if series_key not in series_map:
            series_map[series_key] = {}
        elif None in series_map[series_key]:
            continue
        series_map[series_key][selection.get('source_id')] = selection

    for series_key, series_by_source_id in series_map.items():
        series_without_source = {
            type_id: json.loads(series_key.split('.')[idx])
            for idx, type_id in enumerate(DATA_SERIES_UNIQUE_TYPES_ID)
            if type_id != 'source_id' and series_key.split('.')[idx] != 'null'
        }
        try:
            source_ids = get_source_ranking(access_token, api_host, series_without_source)
        # Catch "no content" response from get_source_ranking()
        except ValueError:
            continue  # empty response

        for source_id in source_ids:
            if source_id in series_by_source_id:
                yield series_by_source_id[source_id]
            if None in series_by_source_id:
                yield groclient.utils.dict_assign(series_without_source, 'source_id', source_id)


def get_available_timefrequency(access_token, api_host, **series):
    params = dict((make_key(k), v) for k, v in iter(list(get_params_from_selection(**series).items())))
    url = '/'.join(['https:', '', api_host, 'v2/available/time-frequencies'])
    headers = {'authorization': 'Bearer ' + access_token}
    response = get_data(url, headers, params)
    if response.status_code == 204:
        return []
    return [groclient.utils.dict_reformat_keys(tf, groclient.utils.str_camel_to_snake) for tf in response.json()]


def list_of_series_to_single_series(series_list, add_belongs_to=False, include_historical=True):
    """Convert list_of_series format from API back into the familiar single_series output format."""
    if not isinstance(series_list, list):
        # If the output is an error or None or something else that's not a list, just propagate
        return series_list
    output = []
    for series in series_list:
        if not (isinstance(series, dict) and isinstance(series.get('data', []), list)):
            continue
        series_metadata = series.get('series', {}).get('metadata', {})
        has_historical_regions = series_metadata.get('includesHistoricalRegion', False) or series_metadata.get(
            'includesHistoricalPartnerRegion', False
        )
        if not include_historical and has_historical_regions:
            continue
        # All the belongsTo keys are in camelCase. Convert them to snake_case.
        # Only need to do this once per series, so do this outside of the list
        # comprehension and save to a variable to avoid duplicate work:
        belongs_to = groclient.utils.dict_reformat_keys(
            series.get('series', {}).get('belongsTo', {}), groclient.utils.str_camel_to_snake
        )
        for point in series.get('data', []):
            formatted_point = {
                'start_date': point[0],
                'end_date': point[1],
                'value': point[2],
                'unit_id': point[4] if len(point) > 4 else series['series'].get('unitId', None),
                'metadata': point[5] if len(point) > 5 and point[5] is not None else {},
                # input_unit_id and input_unit_scale are deprecated but provided for backwards
                # compatibility. unit_id should be used instead.
                'input_unit_id': point[4] if len(point) > 4 else series['series'].get('unitId', None),
                'input_unit_scale': 1,
                # If a point does not have reporting_date, use None
                'reporting_date': point[3] if len(point) > 3 else None,
                # If a point does not have available_date, use None
                'available_date': point[6] if len(point) > 6 else None,
                # Series attributes:
                'metric_id': series['series'].get('metricId', None),
                'item_id': series['series'].get('itemId', None),
                'region_id': series['series'].get('regionId', None),
                'partner_region_id': series['series'].get('partnerRegionId', 0),
                'frequency_id': series['series'].get('frequencyId', None)
                # 'source_id': series['series'].get('sourceId', None), TODO: add source to output
            }

            if formatted_point['metadata'].get('confInterval') is not None:
                formatted_point['metadata']['conf_interval'] = formatted_point['metadata'].pop('confInterval')

            if add_belongs_to:
                # belongs_to is consistent with the series the user requested. So if an
                # expansion happened on the server side, the user can reconstruct what
                # results came from which request.
                formatted_point['belongs_to'] = belongs_to
            output.append(formatted_point)
    return output


def get_data_points(access_token, api_host, **selection):
    logger = get_default_logger()
    headers = {'authorization': 'Bearer ' + access_token}
    url = '/'.join(['https:', '', api_host, 'v2/data'])
    params = get_data_call_params(**selection)
    required_params = [
        groclient.utils.str_snake_to_camel(type_id)
        for type_id in DATA_SERIES_UNIQUE_TYPES_ID
        if type_id != 'partner_region_id'
    ]
    missing_params = list(required_params - params.keys())
    if len(missing_params):
        message = 'API request cannot be processed because {} not specified.'.format(
            missing_params[0] + ' is'
            if len(missing_params) == 1
            else ', '.join(missing_params[:-1]) + ' and ' + missing_params[-1] + ' are'
        )
        logger.warning(message)
        raise ValueError(message)
    resp = get_data(url, headers, params)
    include_historical = selection.get('include_historical', True)
    return list_of_series_to_single_series(resp.json(), False, include_historical)


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
    search_results = search(access_token, api_host, entity_type, search_terms)[:num_results]
    search_result_ids = [result['id'] for result in search_results]
    search_result_details = lookup(access_token, api_host, entity_type, search_result_ids)
    for search_result_id in search_result_ids:
        yield search_result_details[str(search_result_id)]


def lookup_belongs(access_token, api_host, entity_type, entity_id):
    parent_ids = lookup(access_token, api_host, entity_type, entity_id)['belongsTo']
    parent_details = lookup(access_token, api_host, entity_type, parent_ids)
    for parent_id in parent_ids:
        yield parent_details[str(parent_id)]


def get_geo_centre(access_token, api_host, region_id):
    url = '/'.join(['https:', '', api_host, 'v2/geocentres'])
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, {'regionIds': region_id})
    return resp.json()['data']


@memoize(maxsize=None)
def get_geojsons(access_token, api_host, region_id, descendant_level, zoom_level):
    url = '/'.join(['https:', '', api_host, 'v2/geocentres'])
    params = {'includeGeojson': True, 'regionIds': region_id, 'zoom': zoom_level}
    if descendant_level:
        params['reqRegionLevelId'] = descendant_level
        params['stringify'] = 'false'
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers, params)
    return [groclient.utils.dict_reformat_keys(r, groclient.utils.str_camel_to_snake) for r in resp.json()['data']]


def get_geojson(access_token, api_host, region_id, zoom_level):
    for region in get_geojsons(access_token, api_host, region_id, None, zoom_level):
        return json.loads(region['geojson'])


def get_ancestor(
    access_token,
    api_host,
    entity_type,
    entity_id,
    distance=None,
    include_details=True,
    ancestor_level=None,
    include_historical=True,
):
    url = f'https://{api_host}/v2/{entity_type}/belongs-to'
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'ids': [entity_id]}
    if distance:
        params['distance'] = distance
    else:
        if entity_type == 'regions' and ancestor_level:
            params['level'] = ancestor_level
        else:
            params['distance'] = -1

    resp = get_data(url, headers, params)
    ancestor_entity_ids = resp.json()['data'][str(entity_id)]

    # Filter out regions with the 'historical' flag set to true
    if not include_historical or include_details:
        entity_details = lookup(access_token, api_host, entity_type, ancestor_entity_ids)

        if not include_historical:
            ancestor_entity_ids = [entity['id'] for entity in entity_details.values() if not entity['historical']]

        if include_details:
            return [entity_details[str(child_entity_id)] for child_entity_id in ancestor_entity_ids]

    return [{'id': ancestor_entity_id} for ancestor_entity_id in ancestor_entity_ids]


def get_descendant(
    access_token,
    api_host,
    entity_type,
    entity_id,
    distance=None,
    include_details=True,
    descendant_level=None,
    include_historical=True,
):
    url = f'https://{api_host}/v2/{entity_type}/contains'
    headers = {'authorization': 'Bearer ' + access_token}
    params = {'ids': [entity_id]}
    if distance:
        params['distance'] = distance
    else:
        if entity_type == 'regions' and descendant_level:
            params['level'] = descendant_level
        else:
            params['distance'] = -1

    if entity_type == 'regions':
        params['includeHistorical'] = include_historical

    resp = get_data(url, headers, params)
    descendant_entity_ids = resp.json()['data'][str(entity_id)]

    # Filter out regions with the 'historical' flag set to true
    if include_details:
        entity_details = lookup(access_token, api_host, entity_type, descendant_entity_ids)
        return [entity_details[str(child_entity_id)] for child_entity_id in descendant_entity_ids]

    return [{'id': descendant_entity_id} for descendant_entity_id in descendant_entity_ids]


def get_area_weighting_series_names(access_token, api_host):
    url = f'https://{api_host}/area-weighting-series-names'
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()


def get_area_weighting_weight_names(access_token, api_host):
    url = f'https://{api_host}/area-weighting-weight-names'
    headers = {'authorization': 'Bearer ' + access_token}
    resp = get_data(url, headers)
    return resp.json()


def get_area_weighted_series(access_token: str, api_host: str, series_name: str, weight_names: List[str], 
                             region_id: Union[int, List[int]], method: str, latest_date_only: bool):
    url = f'https://{api_host}/area-weighting'
    headers = {'authorization': 'Bearer ' + access_token}
    if isinstance(region_id, int):
        region_id = [region_id]
    params = {
        'seriesName': series_name,
        'weightNames': weight_names,
        'regionIds': region_id,
        'method': method,
        'latestDateOnly': latest_date_only,
    }
    resp = get_data(url, headers, params=params)
    return resp.json()


if __name__ == '__main__':
    # To run doctests:
    # $ python lib.py -v
    import doctest

    doctest.testmod(
        raise_on_error=True,  # Set to False for prettier error message
        optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
    )
