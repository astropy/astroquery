# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Utils
==========

Miscellaneous functions used throughout the MAST module.
"""

import numpy as np

import requests
import json
import platform
from urllib import parse

import astropy.coordinates as coord

from ..version import version
from ..exceptions import ResolverError, InvalidQueryError
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


def _simple_request(url, params):
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


def mast_relative_path(mast_uri):
    """
    Given a MAST dataURI, return the associated relative path.

    Parameters
    ----------
    mast_uri : str
        The MAST uri.

    Returns
    -------
    response : str
        The associated relative path.
    """

    response = _simple_request("https://mast.stsci.edu/api/v0.1/path_lookup/",
                               {"uri": mast_uri})
    result = response.json()
    uri_result = result.get(mast_uri)

    return uri_result["path"]
