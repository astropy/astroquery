# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Utils
==========

Miscellaneous functions used throughout the MAST module.
"""

import warnings
import numpy as np

import requests
import json
import platform
from urllib import parse

import astropy.coordinates as coord
from astropy.table import unique, Table

from .. import log
from ..version import version
from ..exceptions import NoResultsWarning, ResolverError, InvalidQueryError
from ..utils import commons

from . import conf


__all__ = []


def parse_type(dbtype):
    """
    Takes a data type as returned by a database call and regularizes it into a
    triplet of the form (human readable datatype, python datatype, default value).

    Parameters
    ----------
    dbtype : str
        A data type, as returned by a database call (ex. 'char').

    Returns
    -------
    response : tuple
        Regularized type tuple of the form (human readable datatype, python datatype, default value).

    For example:

    _parse_type("short")
    ('integer', np.int64, -999)
    """

    dbtype = dbtype.lower()

    return {
        'char': ('string', str, ""),
        'string': ('string', str, ""),
        'datetime': ('string', str, ""),  # TODO: handle datetimes correctly
        'date': ('string', str, ""),  # TODO: handle datetimes correctly

        'double': ('float', np.float64, np.nan),
        'float': ('float', np.float64, np.nan),
        'decimal': ('float', np.float64, np.nan),

        'int': ('integer', np.int64, -999),
        'short': ('integer', np.int64, -999),
        'long': ('integer', np.int64, -999),
        'number': ('integer', np.int64, -999),

        'boolean': ('boolean', bool, None),
        'binary': ('boolean', bool, None),

        'unsignedbyte': ('byte', np.ubyte, -999)
    }.get(dbtype, (dbtype, dbtype, dbtype))


def _simple_request(url, params=None):
    """
    Light wrapper on requests.session().get basically to make monkey patched testing easier/more effective.
    """

    session = requests.session()
    headers = {"User-Agent": (f"astroquery/{version} Python/{platform.python_version()} ({platform.system()}) "
                              f"{session.headers['User-Agent']}"),
               "Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    return response


def resolve_object(objectname):
    """
    Resolves an object name to a position on the sky.

    Parameters
    ----------
    objectname : str
        Name of astronomical object to resolve.

    Returns
    -------
    response : `~astropy.coordinates.SkyCoord`
        The sky position of the given object.
    """

    request_args = {"service": "Mast.Name.Lookup",
                    "params": {'input': objectname, 'format': 'json'}}
    request_string = 'request={}'.format(parse.quote(json.dumps(request_args)))

    response = _simple_request("{}/api/v0/invoke".format(conf.server), request_string)
    result = response.json()

    if len(result['resolvedCoordinate']) == 0:
        raise ResolverError("Could not resolve {} to a sky position.".format(objectname))

    ra = result['resolvedCoordinate'][0]['ra']
    dec = result['resolvedCoordinate'][0]['decl']
    coordinates = coord.SkyCoord(ra, dec, unit="deg")

    return coordinates


def parse_input_location(coordinates=None, objectname=None):
    """
    Convenience function to parse user input of coordinates and objectname.

    Parameters
    ----------
    coordinates : str or `astropy.coordinates` object, optional
        The target around which to search. It may be specified as a
        string or as the appropriate `astropy.coordinates` object.
        One and only one of coordinates and objectname must be supplied.
    objectname : str, optional
        The target around which to search, by name (objectname="M104")
        or TIC ID (objectname="TIC 141914082").
        One and only one of coordinates and objectname must be supplied.

    Returns
    -------
    response : `~astropy.coordinates.SkyCoord`
        The given coordinates, or object's location as an `~astropy.coordinates.SkyCoord` object.
    """

    # Checking for valid input
    if objectname and coordinates:
        raise InvalidQueryError("Only one of objectname and coordinates may be specified.")

    if not (objectname or coordinates):
        raise InvalidQueryError("One of objectname and coordinates must be specified.")

    if objectname:
        obj_coord = resolve_object(objectname)

    if coordinates:
        obj_coord = commons.parse_coordinates(coordinates)

    return obj_coord


def split_list_into_chunks(input_list, chunk_size):
    """
    Splits a list into chunks of a specified size.

    Parameters
    ----------
    input_list : list
        List to be split into chunks.
    chunk_size : int
        Size of each chunk.

    Yields
    ------
    chunk : list
        A chunk of the input list.
    """
    for idx in range(0, len(input_list), chunk_size):
        yield input_list[idx:idx + chunk_size]


def mast_relative_path(mast_uri):
    """
    Given one or more MAST dataURI(s), return the associated relative path(s).

    Parameters
    ----------
    mast_uri : str, list of str
        The MAST uri(s).

    Returns
    -------
    response : str, list of str
        The associated relative path(s).
    """
    if isinstance(mast_uri, str):
        uri_list = [("uri", mast_uri)]
    else:  # mast_uri parameter is a list
        uri_list = [("uri", uri) for uri in mast_uri]

    # Split the list into chunks of 50 URIs; this is necessary
    # to avoid "414 Client Error: Request-URI Too Large".
    uri_list_chunks = list(split_list_into_chunks(uri_list, chunk_size=50))

    result = []
    for chunk in uri_list_chunks:
        response = _simple_request("https://mast.stsci.edu/api/v0.1/path_lookup/",
                                   {"uri": [mast_uri[1] for mast_uri in chunk]})

        json_response = response.json()

        for uri in chunk:
            # Chunk is a list of tuples where the tuple is
            # ("uri", "/path/to/product")
            # so we index for path (index=1)
            path = json_response.get(uri[1])["path"]
            if path is None:
                warnings.warn(f"Failed to retrieve MAST relative path for {uri[1]}. Skipping...", NoResultsWarning)
                continue
            if 'galex' in path:
                path = path.lstrip("/mast/")
            elif '/ps1/' in path:
                path = path.replace("/ps1/", "panstarrs/ps1/public/")
            elif 'hlsp' in path:
                path = path.replace("/hlsp_local/public/", "mast/")
            else:
                path = path.lstrip("/")
            result.append(path)

    # If the input was a single URI string, we return a single string
    if isinstance(mast_uri, str):
        return result[0]
    # Else, return a list of paths
    return result


def remove_duplicate_products(data_products, uri_key):
    """
    Removes duplicate data products that have the same data URI.

    Parameters
    ----------
    data_products : `~astropy.table.Table`, list
        Table containing products or list of URIs to be checked for duplicates.
    uri_key : str
        Column name representing the URI of a product.

    Returns
    -------
    unique_products : `~astropy.table.Table`
        Table containing products with unique dataURIs.
    """
    # Get unique products based on input type
    if isinstance(data_products, Table):
        unique_products = unique(data_products, keys=uri_key)
    else:  # data_products is a list
        seen = set()
        unique_products = []
        for uri in data_products:
            if uri not in seen:
                seen.add(uri)
                unique_products.append(uri)

    number = len(data_products)
    number_unique = len(unique_products)
    if number_unique < number:
        log.info(f"{number - number_unique} of {number} products were duplicates. "
                 f"Only returning {number_unique} unique product(s).")

    return unique_products
