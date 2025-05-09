# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Utils
==========

Miscellaneous functions used throughout the MAST module.
"""

import warnings
import numpy as np

import requests
import platform

from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy import units as u

from .. import log
from ..version import version
from ..exceptions import InputWarning, NoResultsWarning, ResolverError, InvalidQueryError
from ..utils import commons


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


def resolve_object(objectname, *, resolver=None, resolve_all=False):
    """
    Resolves an object name to a position on the sky.

    Parameters
    ----------
    objectname : str
        Name of astronomical object to resolve.
    resolver : str, optional
        The resolver to use when resolving a named target into coordinates. Valid options are "SIMBAD" and "NED".
        If not specified, the default resolver order will be used. Please see the
        `STScI Archive Name Translation Application (SANTA) <https://mastresolver.stsci.edu/Santa-war/>`__
        for more information. If ``resolve_all`` is True, this parameter will be ignored. Default is None.
    resolve_all : bool, optional
        If True, will try to resolve the object name using all available resolvers ("NED", "SIMBAD").
        Function will return a dictionary where the keys are the resolver names and the values are the
        resolved coordinates. Default is False.

    Returns
    -------
    response : `~astropy.coordinates.SkyCoord`, dict
        If ``resolve_all`` is False, returns a `~astropy.coordinates.SkyCoord` object with the resolved coordinates.
        If ``resolve_all`` is True, returns a dictionary where the keys are the resolver names and the values are
        `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.
    """
    is_catalog = False  # Flag to check if object name belongs to a MAST catalog
    catalog = None  # Variable to store the catalog name
    objectname = objectname.strip()
    catalog_prefixes = {
        'TIC ': 'TIC',
        'KIC ': 'KEPLER',
        'EPIC ': 'K2'
    }

    if resolver:
        # Check that resolver is valid
        resolver = resolver.upper()
        if resolver not in ('NED', 'SIMBAD'):
            raise ResolverError('Invalid resolver. Must be "NED" or "SIMBAD".')

        if resolve_all:
            # Warn if user is trying to use a resolver with resolve_all
            warnings.warn('The resolver parameter is ignored when resolve_all is True. '
                          'Coordinates will be resolved using all available resolvers.', InputWarning)

        # Check if object belongs to a MAST catalog
        for prefix, name in catalog_prefixes.items():
            if objectname.startswith(prefix):
                is_catalog = True
                catalog = name
                break

    # Whether to set resolveAll to True when making the HTTP request
    # Should be True when resolve_all = True or when object name belongs to a MAST catalog (TIC, KIC, EPIC, K2)
    use_resolve_all = resolve_all or is_catalog

    # Send request to STScI Archive Name Translation Application (SANTA)
    params = {'name': objectname,
              'outputFormat': 'json',
              'resolveAll': use_resolve_all}
    if resolver and not use_resolve_all:
        params['resolver'] = resolver
    response = _simple_request('http://mastresolver.stsci.edu/Santa-war/query', params)
    response.raise_for_status()  # Raise any errors
    result = response.json().get('resolvedCoordinate', [])

    # If a resolver is specified and resolve_all is False, find and return the result for that resolver
    if resolver and not resolve_all:
        resolver_result = next((res for res in result if res.get('resolver') == resolver), None)
        if not resolver_result:
            raise ResolverError(f'Could not resolve {objectname} to a sky position using {resolver}. '
                                'Please try another resolver or set ``resolver=None`` to use the first '
                                'compatible resolver.')
        resolver_coord = SkyCoord(resolver_result['ra'], resolver_result['decl'], unit='deg')

        # If object belongs to a MAST catalog, check the separation between the coordinates from the
        # resolver and the catalog
        if is_catalog:
            catalog_result = next((res for res in result if res.get('resolver') == catalog), None)
            if catalog_result:
                catalog_coord = SkyCoord(catalog_result['ra'], catalog_result['decl'], unit='deg')
                if resolver_coord.separation(catalog_coord) > 1 * u.arcsec:
                    # Warn user if the coordinates differ by more than 1 arcsec
                    warnings.warn(f'Resolver {resolver} returned coordinates that differ from MAST {catalog} catalog '
                                  'by more than 1 arcsec. ', InputWarning)

        log.debug(f'Coordinates resolved using {resolver}: {resolver_coord}')
        return resolver_coord

    if not result:
        raise ResolverError('Could not resolve {} to a sky position.'.format(objectname))

    # Return results for all compatible resolvers
    if resolve_all:
        return {
            res['resolver']: SkyCoord(res['ra'], res['decl'], unit='deg')
            for res in result
        }

    # Case when resolve_all is False and no resolver is specified
    # SANTA returns result from first compatible resolver
    coord = SkyCoord(result[0]['ra'], result[0]['decl'], unit='deg')
    log.debug(f'Coordinates resolved using {result[0]["resolver"]}: {coord}')
    return coord


def parse_input_location(*, coordinates=None, objectname=None, resolver=None):
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
    resolver : str, optional
        The resolver to use when resolving a named target into coordinates. Valid options are "SIMBAD" and "NED".
        If not specified, the default resolver order will be used. Please see the
        `STScI Archive Name Translation Application (SANTA) <https://mastresolver.stsci.edu/Santa-war/>`__
        for more information. Default is None.

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

    if not objectname and resolver:
        warnings.warn("Resolver is only used when resolving object names and will be ignored.", InputWarning)

    if objectname:
        obj_coord = resolve_object(objectname, resolver=resolver)

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


def mast_relative_path(mast_uri, *, verbose=True):
    """
    Given one or more MAST dataURI(s), return the associated relative path(s).

    Parameters
    ----------
    mast_uri : str, list of str
        The MAST uri(s).
    verbose : bool, optional
        Default True. Whether to issue warnings if the MAST relative path cannot be found for a product.

    Returns
    -------
    response : str, list of str
        The associated relative path(s).
    """
    if isinstance(mast_uri, str):
        uri_list = [mast_uri]
    else:
        uri_list = list(mast_uri)

    # Split the list into chunks of 50 URIs; this is necessary
    # to avoid "414 Client Error: Request-URI Too Large".
    uri_list_chunks = list(split_list_into_chunks(uri_list, chunk_size=50))

    result = []
    for chunk in uri_list_chunks:
        response = _simple_request("https://mast.stsci.edu/api/v0.1/path_lookup/",
                                   {"uri": [mast_uri for mast_uri in chunk]})

        json_response = response.json()

        for uri in chunk:
            # Chunk is a list of tuples where the tuple is
            # ("uri", "/path/to/product")
            # so we index for path (index=1)
            path = json_response.get(uri)["path"]
            if path is None:
                if verbose:
                    warnings.warn(f"Failed to retrieve MAST relative path for {uri}. Skipping...", NoResultsWarning)
            elif 'galex' in path:
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
        _, unique_indices = np.unique(data_products[uri_key], return_index=True)
        unique_products = data_products[np.sort(unique_indices)]
    else:  # list of URIs
        seen = set()
        unique_products = [uri for uri in data_products if not (uri in seen or seen.add(uri))]

    duplicates_removed = len(data_products) - len(unique_products)
    if duplicates_removed > 0:
        log.info(f"{duplicates_removed} of {len(data_products)} products were duplicates. "
                 f"Only returning {len(unique_products)} unique product(s).")

    return unique_products
