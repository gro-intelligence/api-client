from __future__ import print_function
from functools import partial
import itertools
import json
import os
import time

from typing import List, Union

# Python3 support
try:
    # Python3
    from urllib.parse import urlencode
except ImportError:
    # Python2
    from urllib import urlencode

from groclient import cfg, lib
from groclient.constants import REGION_LEVELS, DATA_SERIES_UNIQUE_TYPES_ID, ENTITY_KEY_TO_TYPE
from groclient.utils import intersect, zip_selections, dict_unnest, str_snake_to_camel
from groclient.lib import APIError

import pandas
from tornado import gen
from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado.ioloop import IOLoop
from tornado.queues import Queue


class BatchError(APIError):
    """Replicate the APIError interface given a Tornado HTTPError."""

    def __init__(self, response, retry_count, url, params):
        self.response = response
        self.retry_count = retry_count
        self.url = url
        self.params = params
        self.status_code = self.response.code if hasattr(self.response, "code") else None
        try:
            json_content = json_decode(self.response.body)
            # 'error' should be something like 'Not Found' or 'Bad Request'
            self.message = json_content.get("error", "")
            # Some error responses give additional info.
            # For example, a 400 Bad Request might say "metricId is required"
            if "message" in json_content:
                self.message += ": {}".format(json_content["message"])
        except Exception:
            # If the error message can't be parsed, fall back to a generic "giving up" message.
            self.message = "Giving up on {} after {} {}: {}".format(
                self.url,
                self.retry_count,
                "retry" if self.retry_count == 1 else "retries",
                response,
            )


class GroClient(object):
    """API client with stateful authentication for lib functions and extra convenience methods."""

    def __init__(
        self,
        api_host=cfg.API_HOST,
        access_token=None,
        proxy_host=None,
        proxy_port=None,
        proxy_username=None,
        proxy_pass=None,
    ):
        """Construct a GroClient instance.

        Parameters
        ----------
        api_host : string, optional
            The API server hostname.
        access_token : string, optional
            Your Gro API authentication token. If not specified, the
            :code:`$GROAPI_TOKEN` environment variable is used. See
            :doc:`authentication`.
        proxy_host : string, optional
            If you're instantiating the GroClient behind a proxy, you'll need to
            provide the proxy_host to properly send requests using the groclient
            library.
        proxy_port : int, optional
            If you're instantiating the GroClient behind a proxy, you'll need to
            provide the proxy_port to properly send requests using the groclient
            library.
        proxy_username : string, optional
            If you're instantiating the GroClient behind a proxy, and your proxy
            requires a username and password, you'll need to provide the proxy_username.
        proxy_pass : string optional
            Password for your proxy username.

        Raises
        ------
            RuntimeError
                Raised when neither the :code:`access_token` parameter nor
                :code:`$GROAPI_TOKEN` environment variable are set.

        Examples
        --------
            >>> client = GroClient()  # token stored in $GROAPI_TOKEN

            >>> client = GroClient(access_token="your_token_here")

            # example useage when accessed via a proxy
            >>> client = GroClient(access_token="your_token_here", proxy_host="0.0.0.0", proxy_port=8080,
            proxy_username="user_name", proxy_pass="secret_password")
        """
        # Initialize early since they're referenced in the destructor and
        # access_token checking may cause constructor to exit early.
        self._async_http_client = None
        self._ioloop = None

        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._proxy_username = proxy_username
        self._proxy_pass = proxy_pass

        if access_token is None:
            access_token = os.environ.get("GROAPI_TOKEN")
            if access_token is None:
                raise RuntimeError(
                    "$GROAPI_TOKEN environment variable must be set when "
                    "GroClient is constructed without the access_token argument"
                )
        self.api_host = api_host
        self.access_token = access_token
        self._logger = lib.get_default_logger()
        self._data_series_list = set()  # all that have been added
        self._data_series_queue = []  # added but not loaded in data frame
        self._data_frame = pandas.DataFrame()
        try:
            # Each GroClient has its own IOLoop and AsyncHTTPClient.
            self._ioloop = IOLoop()
            # Note: force_instance is needed to disable Tornado's
            # pseudo-singleton AsyncHTTPClient caching behavior.
            if self._proxy_host and self._proxy_port:
                defaults_dict = {"proxy_host": self._proxy_host, "proxy_port": self._proxy_port}
                if self._proxy_username and self._proxy_pass:
                    defaults_dict['proxy_username'] = self._proxy_username
                    defaults_dict['proxy_pass'] = self._proxy_pass
                AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
                self._async_http_client = AsyncHTTPClient(force_instance=True, defaults=defaults_dict)
            else:
                self._async_http_client = AsyncHTTPClient(force_instance=True)
        except Exception as e:
            self._logger.warning("Unable to initialize event loop, async methods disabled: {}".format(e))

    def __del__(self):
        if self._async_http_client is not None:
            self._async_http_client.close()
        if self._ioloop is not None:
            self._ioloop.stop()
            self._ioloop.close()

    def get_logger(self):
        return self._logger

    @gen.coroutine
    def async_get_data(self, url, headers, params=None):
        base_log_record = dict(route=url, params=params)

        def log_request(start_time, retry_count, msg, status_code):
            elapsed_time = time.time() - start_time
            log_record = dict(base_log_record)
            log_record["elapsed_time_in_ms"] = 1000 * elapsed_time
            log_record["retry_count"] = retry_count
            log_record["status_code"] = status_code
            if status_code == 200:
                self._logger.debug(msg, extra=log_record)
            else:
                self._logger.warning(msg, extra=log_record)

        """General 'make api request' function.

        Assigns headers and builds in retries and logging.
        """
        self._logger.debug(url)

        # append version info
        headers.update(lib.get_version_info())

        # Initialize to -1 so first attempt will be retry 0
        retry_count = -1
        while retry_count <= cfg.MAX_RETRIES:
            retry_count += 1
            start_time = time.time()
            http_request = HTTPRequest(
                "{url}?{params}".format(url=url, params=urlencode(params)),
                method="GET",
                headers=headers,
                request_timeout=cfg.TIMEOUT,
                connect_timeout=cfg.TIMEOUT,
            )
            try:
                try:
                    response = yield self._async_http_client.fetch(http_request)
                    status_code = response.code
                except HTTPError as e:
                    # Catch non-200 codes that aren't errors
                    status_code = e.code if hasattr(e, "code") else None
                    if status_code in [204, 206]:
                        log_msg = {204: "No Content", 206: "Partial Content"}[status_code]
                        response = e.response
                        log_request(start_time, retry_count, log_msg, status_code)
                        # Do not retry.
                    elif status_code == 301:
                        redirected_ids = json.loads(e.response.body.decode("utf-8"))["data"][0]
                        new_params = lib.redirect(params, redirected_ids)
                        log_request(
                            start_time,
                            retry_count,
                            "Redirecting {} to {}".format(params, new_params),
                            status_code,
                        )
                        params = new_params
                        continue  # retry
                    else:  # Otherwise, propagate to error handling
                        raise e
            except Exception as e:
                # HTTPError raised when there's a non-200 status code
                # socket.gaio error raised when there's a connection error
                response = e.response if hasattr(e, "response") else e
                status_code = e.code if hasattr(e, "code") else None
                error_msg = e.response.error if (hasattr(e, "response") and hasattr(e.response, "error")) else e
                log_request(start_time, retry_count, error_msg, status_code)
                if status_code in [429, 500, 502, 503, 504]:
                    # First retry is immediate.
                    # After that, exponential backoff before retrying.
                    if retry_count > 0:
                        time.sleep(2**retry_count)
                    continue
                elif status_code in [400, 401, 402, 404]:
                    break  # Do not retry. Go right to raising an Exception.

            # Request was successful
            log_request(start_time, retry_count, "OK", status_code)
            raise gen.Return(json_decode(response.body) if hasattr(response, "body") else None)

        # Retries failed. Raise exception
        raise BatchError(response, retry_count, url, params)

    def batch_async_queue(self, func, batched_args, output_list, map_result):
        """Asynchronously call func.

        Parameters
        ----------
        func : function
            The function to be batched. Typically a Client method.
        batched_args : list of dicts
            Inputs
        output_list : any, optional
            A custom accumulator to use in map_result. For example: may pass in a non-empty list
            to append results to it, or may pass in a pandas dataframe, etc. By default, is a list
            of n 0s, where n is the length of batched_args.
        map_result : function, optional
            Function to apply changes to individual requests' responses before returning. Must
            return an accumulator, like a map() function.
            Takes 4 params:
            1. the index in batched_args
            2. the element from batched_args
            3. the result from that input
            4. `output_list`. The accumulator of all results

        """
        assert (
            type(batched_args) is list
        ), "Only argument to a batch async decorated function should be a \
            list of a list of the individual non-keyword arguments being \
            passed to the original function."

        # Wrap output_list in an object so it can be modified within inner functions' scope
        # In Python 3, can accomplish the same thing with `nonlocal` keyword.
        output_data = {}
        if output_list is None:
            output_data["result"] = [0] * len(batched_args)
        else:
            output_data["result"] = output_list

        if not map_result:
            # Default map_result function separates output by index of the query. For example:
            # batched_args: [exports of corn, exports of soybeans]
            # accumulator: [[corn datapoint, corn datapoint],
            #               [soybean data point, soybean data point]]
            def map_result(idx, query, response, accumulator):
                accumulator[idx] = response
                return accumulator

        q = Queue()

        @gen.coroutine
        def consumer():
            """Execute func on all items in queue asynchronously."""
            while q.qsize():
                try:
                    idx, item = q.get().result()
                    self._logger.debug("Doing work on {}".format(idx))
                    if type(item) is dict:
                        # Assume that dict types should be unpacked as kwargs
                        result = yield func(**item)
                    elif type(item) is list:
                        # Assume that list types should be unpacked as positional args
                        result = yield func(*item)
                    else:
                        result = yield func(item)
                    output_data["result"] = map_result(idx, item, result, output_data["result"])
                    self._logger.debug("Done with {}".format(idx))
                    q.task_done()
                except Exception:
                    # Cease processing
                    # IOLoop raises "Operation timed out after None seconds"
                    self._ioloop.stop()
                    self._ioloop.close()

        def producer():
            """Immediately enqueue the whole batch of requests."""
            lasttime = time.time()
            for idx, item in enumerate(batched_args):
                q.put((idx, item))
            elapsed = time.time() - lasttime
            self._logger.info("Queued {} requests in {}".format(q.qsize(), elapsed))

        @gen.coroutine
        def main():
            # Start consumer without waiting (since it never finishes).
            for i in range(cfg.MAX_QUERIES_PER_SECOND):
                self._ioloop.spawn_callback(consumer)
            producer()  # Wait for producer to put all tasks.
            yield q.join()  # Wait for consumer to finish all tasks.

        self._ioloop.run_sync(main)
        return output_data["result"]

    # TODO: deprecate  the following  two methods, standardize  on one
    # approach with get_data_points and get_df
    @gen.coroutine
    def get_data_points_generator(self, **selection):
        headers = {"authorization": "Bearer " + self.access_token}
        url = "/".join(["https:", "", self.api_host, "v2/data"])
        params = lib.get_data_call_params(**selection)
        required_params = [
            str_snake_to_camel(type_id) for type_id in DATA_SERIES_UNIQUE_TYPES_ID if type_id != 'partner_region_id'
        ]
        missing_params = list(required_params - params.keys())
        if len(missing_params):
            message = 'API request cannot be processed because {} not specified.'.format(
                missing_params[0] + ' is'
                if len(missing_params) == 1
                else ', '.join(missing_params[:-1]) + ' and ' + missing_params[-1] + ' are'
            )
            self._logger.warning(message)
            raise ValueError(message)

        try:
            list_of_series_points = yield self.async_get_data(url, headers, params)
            include_historical = selection.get("include_historical", True)
            points = lib.list_of_series_to_single_series(list_of_series_points, False, include_historical)
            # Apply unit conversion if a unit is specified
            if "unit_id" in selection:
                raise gen.Return(
                    list(
                        map(
                            partial(self.convert_unit, target_unit_id=selection["unit_id"]),
                            points,
                        )
                    )
                )

            raise gen.Return(points)
        except BatchError as b:
            raise gen.Return(b)

    def batch_async_get_data_points(self, batched_args, output_list=None, map_result=None):
        """Make many :meth:`~get_data_points` requests asynchronously.

        Parameters
        ----------
        batched_args : list of dicts
            Each dict should be a `selections` object like would be passed to
            :meth:`~get_data_points`.

            Example::

                input_list = [
                    {'metric_id': 860032, 'item_id': 274, 'region_id': 1215, 'frequency_id': 9, 'source_id': 2},
                    {'metric_id': 860032, 'item_id': 270, 'region_id': 1215, 'frequency_id': 9, 'source_id': 2}
                ]

        output_list : any, optional
            A custom accumulator to use in map_result. For example: may pass in a non-empty list
            to append results to it, or may pass in a pandas dataframe, etc. By default, is a list
            of n 0s, where n is the length of batched_args.
        map_result : function, optional
            Function to apply changes to individual requests' responses before returning.
            Takes 4 params:
            1. the index in batched_args
            2. the element from batched_args
            3. the result from that input
            4. `output_list`. The accumulator of all results

            Example::

                output_list = []

                # Merge all responses into a single list
                def map_response(inputIndex, inputObject, response, output_list):
                    output_list += response
                    return output_list

                batch_output = client.batch_async_get_data_points(input_list,
                                                                  output_list=output_list,
                                                                  map_result=map_response)

        Returns
        -------
        any
            By default, returns a list of lists of data points. Likely either objects or lists of
            dictionaries. If using a custom map_result function, can return any type.

            Example of the default output format::

                [
                    [
                        {'metric_id': 1, 'item_id': 2, 'start_date': 2000-01-01, 'value': 41, ...},
                        {'metric_id': 1, 'item_id': 2, 'start_date': 2001-01-01, 'value': 39, ...},
                        {'metric_id': 1, 'item_id': 2, 'start_date': 2002-01-01, 'value': 50, ...},
                    ],
                    [
                        {'metric_id': 1, 'item_id': 6, 'start_date': 2000-01-01, 'value': 12, ...},
                        {'metric_id': 1, 'item_id': 6, 'start_date': 2001-01-01, 'value': 13, ...},
                        {'metric_id': 1, 'item_id': 6, 'start_date': 2002-01-01, 'value': 4, ...},
                    ],
                ]

        """
        return self.batch_async_queue(self.get_data_points_generator, batched_args, output_list, map_result)

    @gen.coroutine
    def async_rank_series_by_source(self, *selections_list):
        """Get all sources, in ranked order, for a given selection."""
        response = self.rank_series_by_source(selections_list)
        raise gen.Return(list(response))

    def batch_async_rank_series_by_source(self, batched_args, output_list=None, map_result=None):
        """Perform multiple rank_series_by_source requests asynchronously.

        Parameters
        ----------
        batched_args : list of lists of dicts
            See :meth:`~.rank_series_by_source` `selections_list`. A list of those lists.

        """
        return self.batch_async_queue(self.async_rank_series_by_source, batched_args, output_list, map_result)

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
        return self.lookup("units", unit_id)["abbreviation"]

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
        return lib.get_allowed_units(self.access_token, self.api_host, metric_id, item_id)

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

    def stream_data_series(self, chunk_size=10000, **selection):
        """Retrieve available data series for the given selections.
        Similar to :meth:`~.get_data_series`, but API will stream data in chunk of given size

        Parameters
        ----------
        chunk_size : integer, optional
            Number of data series to be returned in each chunk. Defaults to 10000
        metric_id : integer, optional
        item_id : integer, optional
        region_id : integer, optional
        partner_region_id : integer, optional
        source_id : integer, optional
        frequency_id : integer, optional

        Yields
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
        return lib.stream_data_series(self.access_token, self.api_host, chunk_size, **selection)

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
        return lib.search(self.access_token, self.api_host, entity_type, search_terms)

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
        return lib.search_and_lookup(self.access_token, self.api_host, entity_type, search_terms, num_results)

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
        selections_list : list of dicts
            See the output of :meth:`~.get_data_series`.

        Yields
        ------
        dict
            The input selections_list, expanded out to each possible source, ordered by coverage.

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

                [{'centre': [ 39.8333, -98.5855 ], 'regionId': 1215, 'regionName': 'United States'}]
        """
        return lib.get_geo_centre(self.access_token, self.api_host, region_id)

    def get_geojsons(self, region_id, descendant_level=None, zoom_level=7):
        """Given a region ID, return shape information in geojson, for the
        region and all its descendants at the given level (if specified).

        Parameters
        ----------
        region_id : integer
        descendant_level : integer, admin region level (2, 3, 4 or 5)
        zoom_level : integer, optional(allow 1-8)
            Valid if include_geojson equals True. If zoom level is specified and it is less than 6,
            simplified shapefile will be returned. Otherwise, detailed shapefile will be used by default.

        Returns
        -------
        list of dicts

            Example::

                [{  'centre': [ 39.8333, -98.5855 ],
                    'regionId': 1215,
                    'regionName': 'United States',
                    u'geojson': u'{"type":"GeometryCollection","geometries":[{"type":"MultiPolygon","coordinates":[[[[-155.651382446,20.1647224430001], ...]]]}]}'
                }]

        """
        return lib.get_geojsons(self.access_token, self.api_host, region_id, descendant_level, zoom_level)

    def get_geojson(self, region_id, zoom_level=7):
        """Given a region ID, return shape information in geojson.

        Parameters
        ----------
        region_id : integer
        zoom_level : integer, optional(allow 1-8)
            Valid if include_geojson equals True. If zoom level is specified and it is less than 6,
            simplified shapefile will be returned. Otherwise, detailed shapefile will be used by default.

        Returns
        -------
        a geojson object or None

            Example::

                { 'type': 'GeometryCollection',
                'geometries': [{'type': 'MultiPolygon',
                                'coordinates': [[[[-38.394, -4.225], ...]]]}, ...]}

        """
        return lib.get_geojson(self.access_token, self.api_host, region_id, zoom_level)

    def get_ancestor(
        self,
        entity_type,
        entity_id,
        distance=None,
        include_details=True,
        ancestor_level=None,
        include_historical=True,
    ):
        """Given an item, metric, or region, returns all its ancestors i.e.
        entities that "contain" in the given entity.

        The `distance` parameter controls how many levels of ancestor entities you want to be
        returned. Additionally, if you are getting the ancestors of a given region, you can
        specify the `ancestor_level`, which will return only the ancestors of the given
        `ancestor_level`. However, if both parameters are specified, `distance` takes precedence
        over `ancestor_level`.

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions' }
        entity_id : integer
        distance: integer, optional
            Return all entities that contain the entity_id at maximum distance. If provided along
            with `ancestor_level`, this will take precedence over `ancestor_level`.
            If not provided, get all ancestors.
        include_details : boolean, optional
            True by default. Will perform a lookup() on each ancestor to find name,
            definition, etc. If this option is set to False, only ids of ancestor
            entities will be returned, which makes execution significantly faster.
        ancestor_level : integer, optional
            The region level of interest. See REGION_LEVELS constant. This should only be specified
            if the `entity_type` is 'regions'. If provided along with `distance`, `distance` will
            take precedence. If not provided, and `distance` not provided, get all ancestors.
        include_historical : boolean, optional
            True by default. If False is specified, regions that only exist in historical data
            (e.g. the Soviet Union) will be excluded.

        Returns
        -------
        list of dicts

            Example::

                [{
                    'id': 134,
                    'name': 'Cattle hides, wet-salted',
                    'definition': 'Hides and skins of domesticated cattle-animals ...',
                } , {
                    'id': 382,
                    'name': 'Calf skins, wet-salted',
                    'definition': 'Wet-salted hides and skins of calves-animals of ...'
                }, ...]

            See output of :meth:`~.lookup`

        """
        return lib.get_ancestor(
            self.access_token,
            self.api_host,
            entity_type,
            entity_id,
            distance,
            include_details,
            ancestor_level,
            include_historical,
        )

    def get_descendant(
        self,
        entity_type,
        entity_id,
        distance=None,
        include_details=True,
        descendant_level=None,
        include_historical=True,
    ):
        """Given an item, metric or region, returns all its descendants i.e.
        entities that are "contained" in the given entity

        The `distance` parameter controls how many levels of child entities you want to be returned.
        Additionally, if you are getting the descendants of a given region, you can specify the
        `descendant_level`, which will return only the descendants of the given `descendant_level`.
        However, if both parameters are specified, `distance` takes precedence over
        `descendant_level`.

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions' }
        entity_id : integer
        distance: integer, optional
            Return all entities that contain the entity_id at maximum distance. If provided along
            with `descendant_level`, this will take precedence over `descendant_level`.
            If not provided, get all ancestors.
        include_details : boolean, optional
            True by default. Will perform a lookup() on each descendant  to find name,
            definition, etc. If this option is set to False, only ids of descendant
            entities will be returned, which makes execution significantly faster.
        descendant_level : integer, optional
            The region level of interest. See REGION_LEVELS constant. This should only be specified
            if the `entity_type` is 'regions'. If provided along with `distance`, `distance` will
            take precedence. If not provided, and `distance` not provided, get all descendants.
        include_historical : boolean, optional
            Only applicable to regions. True by default. If False is specified, regions that only exist in historical data
            (e.g. the Soviet Union) will be excluded.

        Returns
        -------
        list of dicts

            Example::

                [{
                    'id': 134,
                    'name': 'Cattle hides, wet-salted',
                    'definition': 'Hides and skins of domesticated cattle-animals ...',
                } , {
                    'id': 382,
                    'name': 'Calf skins, wet-salted',
                    'definition': 'Wet-salted hides and skins of calves-animals of ...'
                }, ...]

            See output of :meth:`~.lookup`

        """
        return lib.get_descendant(
            self.access_token,
            self.api_host,
            entity_type,
            entity_id,
            distance,
            include_details,
            descendant_level,
            include_historical,
        )

    def get_descendant_regions(
        self,
        region_id,
        descendant_level=None,
        include_historical=True,
        include_details=True,
        distance=None,
    ):
        """Look up details of all regions of the given level contained by a region.

        This functionality has been moved to :meth:`~.get_descendant`.
        """
        return lib.get_descendant(
            self.access_token,
            self.api_host,
            'regions',
            region_id,
            distance,
            include_details,
            descendant_level,
            include_historical,
        )

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
                    'start_date': '2000-02-18T00:00:00.000Z',
                    'frequency_id': 3,
                    'end_date': '2020-03-12T00:00:00.000Z',
                    'name': '8-day'
                  }, {
                    'start_date': '2019-09-02T00:00:00.000Z',
                    'frequency_id': 1,
                    'end_date': '2020-03-09T00:00:00.000Z',
                    'name': u'daily'}, ... ]
        """
        return lib.get_available_timefrequency(self.access_token, self.api_host, **selection)

    def get_top(self, entity_type, num_results=5, **selection):
        """Find the data series with the highest cumulative value for the given time range.

        Examples::

            # To get FAO's top 5 corn-producing countries of all time:
            client.get_top('regions', metric_id=860032, item_id=274, frequency_id=9, source_id=2)

            # To get FAO's top 5 corn-producing countries of 2014:
            client.get_top('regions', metric_id=860032, item_id=274, frequency_id=9, source_id=2,
                           start_date='2014-01-01', end_date='2014-12-31')

            # To get the United States' top 15 exports in the decade of 2010-2019:
            client.get_top('items', num_results=15, metric_id=20032, region_id=1215, frequency_id=9,
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

    def get_df(
        self,
        reporting_history=False,
        complete_history=False,
        index_by_series=False,
        include_names=False,
        compress_format=False,
        async_mode=False,
        show_revisions=False,
    ):
        """Call :meth:`~.get_data_points` for each saved data series and return as a combined
        dataframe.

        Note you must have first called either :meth:`~.add_data_series` or
        :meth:`~.add_single_data_series` to save data series into the GroClient's data_series_list.
        You can inspect the client's saved list using :meth:`~.get_data_series_list`.

        Parameters
        ----------
            reporting_history : boolean, optional
                False by default. If true, will return all reporting history from the source.
            complete_history : boolean, optional
                False by default. If true, will return complete history of data points for the selection. This will include
                the reporting history from the source and revisions Gro has captured that may not have been released with an official reporting_date.
            index_by_series : boolean, optional
               If set, the dataframe is indexed by series. See https://developers.gro-intelligence.com/data-series-definition.html
            include_names : boolean, optional
               If set, the dataframe will have additional columns with names of entities.
               Note that this will increase the size of the dataframe by about 5x.
            compress_format: boolean, optional
               If set, each series will be compressed to a single column in the dataframe, with the end_date column
               set as the dataframe inde. All the entity names for each series will be
               placed in column headers.
               compress_format cannot be used simultaneously with reporting_history or complete_history
            async_mode: boolean, optional
                If set, it will make :meth:`~get_data_points` requests asynchronously.
                Note that when running in a Jupyter Ipython notebook with async_mode, you will need to use nest_asyncio module.
            show_revisions(deprecating) : boolean, optional
                This parameter has been renamed as reporting_history.
        Returns
        -------
        pandas.DataFrame
            The results to :meth:`~.get_data_points` for all the saved series, appended together
            into a single dataframe.
            See https://developers.gro-intelligence.com/data-point-definition.html
        """

        assert not (
            compress_format and (reporting_history or show_revisions or complete_history)
        ), "compress_format cannot be used simultaneously with reporting_history or complete_history"

        data_series_list = []
        while self._data_series_queue:
            data_series = self._data_series_queue.pop()
            if reporting_history or show_revisions:
                data_series["reporting_history"] = True
            if complete_history:
                data_series["complete_history"] = True
            if async_mode:
                data_series_list.append(data_series)
            else:
                self.add_points_to_df(None, data_series, self.get_data_points(**data_series))

        if async_mode:
            self.batch_async_get_data_points(
                data_series_list,
                output_list=self._data_frame,
                map_result=self.add_points_to_df,
            )

        if compress_format:
            include_names = True

        if self._data_frame.empty:
            return self._data_frame

        if include_names:
            name_cols = []
            for entity_type_id in DATA_SERIES_UNIQUE_TYPES_ID + ['unit_id']:
                name_col = entity_type_id.replace('_id', '_name')
                name_cols.append(name_col)
                entity_dict = self.lookup(ENTITY_KEY_TO_TYPE[entity_type_id], self._data_frame[entity_type_id].unique())
                self._data_frame[name_col] = self._data_frame[entity_type_id].apply(
                    lambda entity_id: entity_dict.get(str(entity_id))['name']
                )

            if compress_format:
                return self._data_frame.pivot_table(index='end_date', values='value', columns=name_cols)

        if index_by_series:
            idx_columns = intersect(DATA_SERIES_UNIQUE_TYPES_ID, self._data_frame.columns)

            self._data_frame.set_index(idx_columns, inplace=True)
            self._data_frame.sort_index(inplace=True)

        return self._data_frame

    def async_get_df(
        self,
        reporting_history=False,
        complete_history=False,
        index_by_series=False,
        include_names=False,
        compress_format=False,
        show_revisions=False,
    ):
        return self.get_df(
            reporting_history, complete_history, index_by_series, include_names, compress_format, True, show_revisions
        )

    def add_points_to_df(self, index, data_series, data_points, *args):
        """Add the given datapoints to a pandas dataframe.

        Parameters:
        -----------
        index : unused
        data_series : dict
        data_points : list of dicts

        """

        tmp = pandas.DataFrame(data=[dict_unnest(point) for point in data_points])
        if tmp.empty:
            return
        # get_data_points response doesn't include the
        # source_id. We add it as a column, in case we have
        # several selections series which differ only by source id.
        tmp["source_id"] = data_series["source_id"]
        # tmp should always have end_date/start_date/reporting_date/available_date as columns if not empty
        tmp.end_date = pandas.to_datetime(tmp.end_date)
        tmp.start_date = pandas.to_datetime(tmp.start_date)
        tmp.reporting_date = pandas.to_datetime(tmp.reporting_date)
        if "available_date" in tmp.columns:
            tmp.available_date = pandas.to_datetime(tmp.available_date)

        if self._data_frame.empty:
            self._data_frame = tmp
        else:
            self._data_frame = pandas.concat([self._data_frame, tmp])

    def get_data_points(self, **selections):
        """Get all the data points for a given selection.

        https://developers.gro-intelligence.com/data-point-definition.html

        Example::

            client.get_data_points(**{'metric_id': 860032,
                                      'item_id': 274,
                                      'region_id': 1215,
                                      'frequency_id': 9,
                                      'source_id': 2,
                                      'start_date': '2017-01-01',
                                      'end_date': '2017-12-31',
                                      'unit_id': 15})

        Returns::

            [{  'start_date': '2017-01-01T00:00:00.000Z',
                'end_date': '2017-12-31T00:00:00.000Z',
                'value': 408913833.8019222, 'unit_id': 15,
                'reporting_date': None,
                'metric_id': 860032, 'item_id': 274, 'region_id': 1215,
                'partner_region_id': 0, 'frequency_id': 9, 'source_id': 2,
                'belongs_to': {
                    'metric_id': 860032,
                    'item_id': 274,
                    'region_id': 1215,
                    'frequency_id': 9,
                    'source_id': 2
                }
            }]

        Note: you can pass the output of :meth:`~.get_data_series` into :meth:`~.get_data_points`
        to check what series exist for some selections and then retrieve the data points for those
        series. See :sample:`quick_start.py` for an example of this.

        :meth:`~.get_data_points` also allows passing a list of ids for metric_id, item_id, and/or
        region_id to get multiple series in a single request. This can be faster if requesting many
        series.

        For example::

            client.get_data_points(**{'metric_id': 860032,
                                      'item_id': 274,
                                      'region_id': [1215,1216],
                                      'frequency_id': 9,
                                      'source_id': 2,
                                      'start_date': '2017-01-01',
                                      'end_date': '2017-12-31',
                                      'unit_id': 15})

        Returns::

            [{  'start_date': '2017-01-01T00:00:00.000Z',
                'end_date': '2017-12-31T00:00:00.000Z',
                'value': 408913833.8019222, 'unit_id': 15,
                'reporting_date': None,
                'metric_id': 860032, 'item_id': 274, 'region_id': 1215,
                'partner_region_id': 0, 'frequency_id': 9, 'source_id': 2,
                'belongs_to': {
                    'metric_id': 860032,
                    'item_id': 274,
                    'region_id': 1215,
                    'frequency_id': 9,
                    'source_id': 2
                }
            }, { 'start_date': '2017-01-01T00:00:00.000Z',
                 'end_date': '2017-12-31T00:00:00.000Z',
                 'value': 340614.19507563586, 'unit_id': 15,
                 'reporting_date': None,
                 'metric_id': 860032, 'item_id': 274, 'region_id': 1216,
                 'partner_region_id': 0, 'frequency_id': 9, 'source_id': 2,
                 'belongs_to': {
                    'metric_id': 860032,
                    'item_id': 274,
                    'region_id': 1216,
                    'frequency_id': 9,
                    'source_id': 2
                 }
            }]

        Parameters
        ----------
        metric_id : integer or list of integers
            How something is measured. e.g. "Export Value" or "Area Harvested"
        item_id : integer or list of integers
            What is being measured. e.g. "Corn" or "Rainfall"
        region_id : integer or list of integers
            Where something is being measured e.g. "United States Corn Belt" or "China"
        partner_region_id : integer or list of integers, optional
            partner_region refers to an interaction between two regions, like trade or
            transportation. For example, for an Export metric, the "region" would be the exporter
            and the "partner_region" would be the importer. For most series, this can be excluded
            or set to 0 ("World") by default.
        source_id : integer
        frequency_id : integer
        unit_id : integer, optional
        start_date : string, optional
            All points with end dates equal to or after this date
        end_date : string, optional
            All points with start dates equal to or before this date
        reporting_history : boolean, optional
            False by default. If true, will return all reporting history from the source.
        complete_history : boolean, optional
            False by default. If true, will return complete history of data points for the selection. This will include
            the reporting history from the source and revisions Gro has captured that may not have been released with an official reporting_date.
        insert_null : boolean, optional
            False by default. If True, will include a data point with a None value for each period
            that does not have data.
        at_time : string, optional
            Estimate what data would have been available via Gro at a given time in the past. See
            :sample:`at-time-query-examples.ipynb` for more details.
        include_historical : boolean, optional
            True by default, will include historical regions that are part of your selections
        available_since : string, optional
            Fetch points since last data retrieval where available date is equal to or after this date

        Returns
        -------
        list of dicts

        """
        data_points = lib.get_data_points(self.access_token, self.api_host, **selections)
        # Apply unit conversion if a unit is specified
        if "unit_id" in selections:
            return list(
                map(
                    partial(self.convert_unit, target_unit_id=selections["unit_id"]),
                    data_points,
                )
            )
        # Return data points in input units if not unit is specified
        return data_points

    def GDH(self, gdh_selection, **optional_selections):
        """Wrapper for :meth:`~.get_data_points`. with alternative input and output style.

        The data series selection to retrieve is encoded in a
        'gdh_selection' string of the form
        <metric_id>-<item_id>-<region_id>-<partner_region_id>-<frequency_id>-<source_id>

        For example, client.GDH("860032-274-1231-0-9-14") will get the
        data points for Production of Corn in China from PS&D at an
        annual frequency, e.g.
        for csv_row in client.GDH("860032-274-1231-0-9-14"):
            print csv_row

        Parameters:
        ----------
        gdh_selection: string
        optional_selections: dict, optional
            accepts optional params from :meth:`~.get_data_points`.

        Returns:
        ------
        pandas.DataFrame

            The subset of the main DataFrame :meth:`~.get_df`. with the requested series,
            indexed by the names of the selections.

        """

        entity_ids = [int(x) for x in gdh_selection.split("-")]
        selection = zip_selections(entity_ids, **optional_selections)

        self.add_single_data_series(selection)
        try:
            df = self.get_df(index_by_series=True, include_names=True).loc[[tuple(entity_ids)], :]
            df.set_index(
                [
                    entity_type_id.replace('_id', '_name')
                    for entity_type_id in intersect(DATA_SERIES_UNIQUE_TYPES_ID, df.index.names)
                ],
                inplace=True,
            )
            return df
        except KeyError:
            self._logger.warning("GDH returned no data")
            return pandas.DataFrame()

    def get_data_series_list(self):
        """Inspect the current list of saved data series contained in the GroClient.

        For use with :meth:`~.get_df`. Add new data series to the list using
        :meth:`~.add_data_series` and :meth:`~.add_single_data_series`.

        Returns
        -------
        list of dicts
            A list of data_series objects, as returned by :meth:`~.get_data_series`.

        """
        return [dict(data_series_hash) for data_series_hash in self._data_series_list]

    def add_single_data_series(self, data_series):
        """Save a data series object to the GroClient's data_series_list.

        For use with :meth:`~.get_df`.

        Parameters
        ----------
        data_series : dict
            A single data_series object, as returned by :meth:`~.get_data_series` or
            :meth:`~.find_data_series`.
            See https://developers.gro-intelligence.com/data-series-definition.html

        Returns
        -------
        None

        """
        series_hash = frozenset(dict_unnest(data_series).items())
        if series_hash not in self._data_series_list:
            self._data_series_list.add(series_hash)
            # Add a copy of the data series, in case the original is modified
            self._data_series_queue.append(dict(data_series))
            self._logger.info("Added {}".format(data_series))
        else:
            self._logger.debug("Already added: {}".format(data_series))
        return

    def find_data_series(self, result_filter=None, **kwargs):
        """Find data series matching a combination of entities specified by
        name and yield them ranked by coverage.

        Example::

            client.find_data_series(item="Corn",
                                    metric="Futures Open Interest",
                                    region="United States of America")

        will yield a sequence of dictionaries of the form::

            { 'metric_id': 15610005, 'metric_name': 'Futures Open Interest',
              'item_id': 274, 'item_name': 'Corn',
              'region_id': 1215, 'region_name': 'United States',
              'frequency_id': 15, 'source_id': 81,
              'start_date': '1972-03-01T00:00:00.000Z', ...},
            { ... },  ...


        See https://developers.gro-intelligence.com/data-series-definition.html

        :code:`result_filter` can be used to filter entity searches. For example::

            client.find_data_series(item="vegetation",
                                    metric="vegetation indices",
                                    region="Central",
                                    result_filter=lambda r: ('region_id' not in r or
                                                             r['region_id'] == 10393))

        will only consider that particular region, and not the many other regions
        with the same name.

        This method uses :meth:`~.search`, :meth:`~.get_data_series`,
        :meth:`~.get_available_timefrequency` and  :meth:`~.rank_series_by_source`.


        Parameters
        ----------
        metric : string, optional
        item : string, optional
        region : string, optional
        partner_region : string, optional
        start_date : string, optional
            YYYY-MM-DD
        end_date : string, optional
            YYYY-MM-DD
        result_filter: function, optional
            function taking data series selection dict returning boolean

        Yields
        ------
        dict
           A sequence of data series matching the input selections

        See also
        --------
        :meth:`~.get_data_series`

        """
        results = []  # [[('item_id',1),('item_id',2),...],[('metric_id" 1),...],...]
        for kw in kwargs:
            if kwargs.get(kw) is None:
                continue
            id_key = "{}_id".format(kw)
            if id_key in ENTITY_KEY_TO_TYPE:
                type_results = []  # [('item_id',1),('item_id',2),...]
                for search_result in self.search(ENTITY_KEY_TO_TYPE[id_key], kwargs[kw])[
                    : cfg.MAX_RESULT_COMBINATION_DEPTH
                ]:
                    if result_filter is None or result_filter({id_key: search_result["id"]}):
                        type_results.append((id_key, search_result["id"]))
                results.append(type_results)
        # Rank by frequency and source, while preserving search ranking in
        # permutations of search results.
        ranking_groups = set()
        for comb in itertools.product(*results):
            for data_series in self.get_data_series(**dict(comb))[: cfg.MAX_SERIES_PER_COMB]:
                self._logger.debug("Data series: {}".format(data_series))
                # remove time and frequency to rank them
                data_series.pop("start_date", None)
                data_series.pop("end_date", None)
                data_series.pop("frequency_id", None)
                data_series.pop("frequency_name", None)
                # remove source to rank them
                data_series.pop("source_id", None)
                data_series.pop("source_name", None)
                # metadata is not hashable
                data_series.pop("metadata", None)
                # estimated data count is not hashable
                data_series.pop("data_count_estimate", None)
                series_hash = frozenset(data_series.items())
                if series_hash not in ranking_groups:
                    ranking_groups.add(series_hash)
                    if kwargs.get("start_date"):
                        data_series["start_date"] = kwargs["start_date"]
                    if kwargs.get("end_date"):
                        data_series["end_date"] = kwargs["end_date"]
                    for tf in self.get_available_timefrequency(**data_series):
                        ds = dict(data_series)
                        ds["frequency_id"] = tf["frequency_id"]
                        for data_series in self.rank_series_by_source([ds]):
                            yield self.get_data_series(**data_series)[0]

    def add_data_series(self, **kwargs):
        """Adds the top result of :meth:`~.find_data_series` to the saved data series list.

        For use with :meth:`~.get_df`.

        Parameters
        ----------
        metric : string, optional
        item : string, optional
        region : string, optional
        partner_region : string, optional
        start_date : string, optional
            YYYY-MM-DD
        end_date : string, optional
            YYYY-MM-DD
        result_filter: function, optional
            function taking data series selection dict returning boolean

        Returns
        -------
        data_series object, as returned by :meth:`~.get_data_series`.
            The data_series that was added or None if none were found.

        See also
        --------
        :meth:`~.get_df`
        :meth:`~.add_single_data_series`
        :meth:`~.find_data_series`

        """
        for the_data_series in self.find_data_series(**kwargs):
            self.add_single_data_series(the_data_series)
            return the_data_series
        return

    ###
    # Discovery shortcuts
    ###
    def search_for_entity(self, entity_type, keywords):
        """Returns the first result of entity_type that matches the given keywords.

        Parameters
        ----------
        entity_type : { 'metrics', 'items', 'regions', 'sources' }
        keywords : string

        Returns
        ----------
        integer
            The id of the first search result

        """
        results = self.search(entity_type, keywords)
        for result in results:
            self._logger.debug("First result, out of {} {}: {}".format(len(results), entity_type, result["id"]))
            return result["id"]

    def get_provinces(self, country_name):
        """Given the name of a country, find its provinces.

        Parameters
        ----------
        country_name : string

        Returns
        ----------
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

        See Also
        --------
        :meth:`~.get_descendant_regions`

        """
        for region in self.search_and_lookup("regions", country_name):
            if region["level"] == lib.REGION_LEVELS["country"]:
                provinces = self.get_descendant('regions', region["id"], descendant_level=lib.REGION_LEVELS["province"])
                self._logger.debug("Provinces of {}: {}".format(country_name, provinces))
                return provinces
        return None

    def get_names_for_selection(self, selection):
        """Convert a selection into entity names.

        Parameters:
        -----------
        data_series : dict
            A single data_series object, as returned by get_data_series() or find_data_series().
            See https://github.com/gro-intelligence/api-client/wiki/Data-Series-Definition

        Returns:
        --------
        list of pairs of strings
            [('item', 'Corn'), ('region', 'China') ...]

        """
        return [
            (
                entity_key.split("_")[0],
                self.lookup(ENTITY_KEY_TO_TYPE[entity_key], entity_id)["name"],
            )
            for entity_key, entity_id in selection.items()
        ]

    def convert_unit(self, point, target_unit_id):
        """Convert the data point from one unit to another unit.

        If original or target unit is non-convertible, throw an error.

        Parameters
        ----------
        point : dict
            { value: float, unit_id: integer, ... }
        target_unit_id : integer

        Returns
        -------
        dict

            Example ::

                { value: 14.2, unit_id: 4 }

            unit_id is changed to the target, and value is converted to use the
            new unit_id. Other properties are unchanged.

        """
        if point.get("unit_id") is None or point.get("unit_id") == target_unit_id:
            return point
        from_convert_factor = self.lookup("units", point["unit_id"]).get("baseConvFactor")
        if not from_convert_factor.get("factor"):
            raise Exception("unit_id {} is not convertible".format(point["unit_id"]))
        to_convert_factor = self.lookup("units", target_unit_id).get("baseConvFactor")
        if not to_convert_factor.get("factor"):
            raise Exception("unit_id {} is not convertible".format(target_unit_id))

        if point.get("value") is not None:
            point["value"] = lib.convert_value(point["value"], from_convert_factor, to_convert_factor)
        if point.get("metadata") is not None and point["metadata"].get("conf_interval") is not None:
            point["metadata"]["conf_interval"] = lib.convert_value(
                point["metadata"]["conf_interval"], from_convert_factor, to_convert_factor
            )
        point["unit_id"] = target_unit_id
        return point

    def get_area_weighting_series_names(self):
        """Returns a list of valid series names that can be used to
            form the inputs of :meth:`~.get_area_weighted_series`.

        Returns
        -------
        list of strings

            Example::
                [   "CPC_max_temp_daily",
                    "CPC_min_temp_daily",
                    "ET_PET_monthly",
                    "GDI_daily",
                    ...
                ]
        """
        return lib.get_area_weighting_series_names(self.access_token, self.api_host)

    def get_area_weighting_weight_names(self):
        """Returns a list of valid weight names that can be used to
            form the inputs of :meth:`~.get_area_weighted_series`.

        Returns
        -------
        list of strings

            Example::
                [   "2008 RMA Corn Area Indemnified (Acres)",
                    "2008 RMA Corn Drought Indemnity Paid to Producer (USD)",
                    ...
                ]
        """
        return lib.get_area_weighting_weight_names(self.access_token, self.api_host)

    def get_area_weighted_series(self, series_name: str, weight_names: List[str], region_id: Union[int, List[int]], 
        method: str = 'sum', latest_date_only: bool = False):
        """Compute weighted average on selected series with the given weights.

        Returns a dictionary mapping dates to weighted values.

        Parameters
        ----------
        series_name: str
            Should be a tag identifying the desired Gro data series. e.g. 'NDVI_8day'
            For getting the full list of valid series names, please call :meth:`~.get_area_weighting_series_names`
        weight_names: list of strs
            List of weight names that will be used to weight the provided series. e.g. ['Barley (ha)', 'Corn (ha)']
            For getting the full list of valid weight names, please call :meth:`~.get_area_weighting_weight_names`
        region_id: integer or list of integers
            The region or regions for which the weighted series will be computed
            Supported region levels are (1, 2, 3, 4, 5, 8)
        method: str, optional
            'sum' by default. Multi-crop weights can be calculated with either 'sum' or 'normalize' method.
        latest_date_only: bool, optional
            False by default. If True, will return a single key-value pair where the key is the latested date.
            e.g. {'2000-03-12': 0.221}

        Returns
        -------
        dict

            Example::
                {'2000-02-25': 0.217, '2000-03-04': 0.217, '2000-03-12': 0.221, ...}
        """
        return lib.get_area_weighted_series(
            self.access_token, self.api_host, series_name, weight_names, region_id, method, latest_date_only
        )
