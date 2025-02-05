#!/usr/bin/env/python

"""
utils.py: helper functions for the astropy.eso module
"""

import copy
import hashlib
import pickle
from typing import Union, List

from astroquery import log


def _split_str_as_list_of_str(column_str: str):
    if column_str == '':
        column_list = []
    else:
        column_list = list(map(lambda x: x.strip(), column_str.split(',')))
    return column_list


def adql_sanitize_val(x):
    """
    If the value is a string, put it into single quotes
    """
    if isinstance(x, str):
        return f"'{x}'"
    else:
        return f"{x}"


def are_coords_valid(ra: float = None,
                     dec: float = None,
                     radius: float = None) -> bool:
    """
    ra, dec, radius must be either present all three
    or absent all three. Moreover, they must be float
    """
    is_a_valid_combination = True
    # if either of the three is None...
    if ((ra is None)
        or (dec is None)
            or (radius is None)):
        # ...all three must be none
        is_a_valid_combination = (
            (ra is None)
            and (dec is None)
            and (radius is None))
    else:
        # They are not None --> they must be float:
        is_a_valid_combination = (
            isinstance(ra, (float, int))
            and isinstance(dec, (float, int))
            and isinstance(radius, (float, int)))
    return is_a_valid_combination


def py2adql(table: str, columns: Union[List, str] = None,
            ra: float = None, dec: float = None, radius: float = None,
            where_constraints: List = None,
            order_by: str = '', order_by_desc=True, top: int = None):
    """
    Return the adql string corresponding to the parameters passed
    See adql examples at http://archive.eso.org/tap_obs/examples
    """
    # validate ra, dec, radius
    if not are_coords_valid(ra, dec, radius):
        message = "Either all three values for (ra, dec, radius) must be present or none of them.\n"
        message += f"Values provided: ra = {ra:0.7f}, dec = {dec:0.7f}, radius = {radius:0.7f}"
        raise ValueError(message)

    # coordinates are valid
    where_circle = []
    if ra:
        where_circle += [f'intersects(s_region, circle(\'ICRS\', {ra}, {dec}, {radius}))=1']

    # Initialize / validate
    query_string = None
    # do not modify the original list
    wc = [] if where_constraints is None else where_constraints[:]
    if isinstance(columns, str):
        columns = _split_str_as_list_of_str(columns)
    if columns is None or len(columns) < 1:
        columns = ['*']

    # Build the query
    query_string = ', '.join(columns) + ' from ' + table
    if len(wc) > 0:
        where_string = ' where ' + ' and '.join(wc + where_circle)
        query_string += where_string

    if len(order_by) > 0:
        order_string = ' order by ' + order_by + (' desc ' if order_by_desc else ' asc ')
        query_string += order_string

    if top is not None:
        query_string = f"select top {top} " + query_string
    else:
        query_string = "select " + query_string

    return query_string.strip()


def eso_hash(query_str: str, url: str):
    """
    Return a hash given an adql query string and an url.
    """
    request_key = (query_str, url)
    h = hashlib.sha224(pickle.dumps(request_key)).hexdigest()
    return h


def to_cache(table, cache_file):
    """
    Dump a table to a pickle file
    """
    log.debug("Caching data to %s", cache_file)

    table = copy.deepcopy(table)
    with open(cache_file, "wb") as f:
        pickle.dump(table, f, protocol=4)
