"""Miscellaneous utility functions for operations not specific to the API client."""

try:
    # functools are native in Python 3.2.3+
    from functools import lru_cache as memoize
except ImportError:
    from backports.functools_lru_cache import lru_cache as memoize
import re


@memoize(maxsize=None)
def str_camel_to_snake(term):
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


@memoize(maxsize=None)
def str_snake_to_kebab(term):
    """Convert a string from snake_case to kebab-case.

    Parameters
    ----------
    term : string
        A snake_case string
    Returns
    -------
    string
        A new kebab-case string

    """
    return '-'.join(term.split('_'))


@memoize(maxsize=None)
def str_kebab_to_snake(term):
    """Convert a string from kebab-case to snake_case.

    Parameters
    ----------
    term : string
        A kebab-case string
    Returns
    -------
    string
        A new snake_case string

    """
    return '_'.join(term.split('-'))


def dict_reformat_keys(obj, format_func):
    """Convert a dictionary's keys from one format to another.

    >>> dict_reformat_keys({'belongsTo': {'metricId': 4}}, camel_to_snake)
    {'belongs_to': {'metricId': 4}}

    Parameters
    ----------
    obj : dict
        A dictionary with keys that need to be reformatted
    format_func : function
        Will execute on each key on the dict

    Returns
    -------
    dict
        A new dictionary with formatted keys

    """
    return dict(format_func((key), value) for key, value in obj.items())


def list_chunk(arr, chunk_size=50):
    """Chunk an array into chunks of a given max length.

    Parameters
    ----------
    arr : list
    chunk_size : int, optional

    Returns
    -------
    list of lists

    Examples
    --------
    >>> chunk([1,2,3,4,5,6,7,8], 3)
    [[1,2,3], [4,5,6], [7,8]]
    >>> chunk([1,2,3,4,5,6,7,8,9,10,11], 5)
    [[1,2,3,4,5], [6,7,8,9,10], [11]]

    """
    return [arr[i*chunk_size:(i+1)*chunk_size] for i in range(len(arr))]
