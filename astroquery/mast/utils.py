# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Utils
==========

Miscellaneous functions used throughout the MAST module.
"""

import re
import warnings

import numpy as np
import requests
import platform
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.utils.console import ProgressBarOrSpinner
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


def _batched_request(
    items,
    params,
    max_batch,
    param_key,
    request_func,
    extract_func,
    desc="Fetching items",
):
    """
    Generic helper for batching API requests.

    Parameters
    ----------
    items : list
        List of items to process in batches.
    params : dict
        Dictionary of parameters to include in the request.
    max_batch : int
        Maximum number of items to include in a single batch.
    param_key : str
        Key in the params dictionary that will hold the batch of items.
    request_func : callable
        Function to call for each batch request.
    extract_func : callable
        Function to extract the relevant data from the response.
    desc : str
        Description of the operation for progress reporting.

    Returns
    -------
    results : list
        List of results extracted from the responses.
    """
    if len(items) > max_batch:
        chunks = list(split_list_into_chunks(items, max_batch))
        results = []
        with ProgressBarOrSpinner(len(items), f"{desc} in {len(chunks)} batches ...") as pb:
            fetched = 0
            pb.update(0)
            for chunk in chunks:
                params[param_key] = chunk
                resp = request_func(params)
                resp.raise_for_status()

                # Extend results with new response
                new_resp = extract_func(resp)
                results.extend(new_resp)

                # Update progress bar
                fetched += len(chunk)
                pb.update(fetched)
        return results
    else:
        params[param_key] = items
        resp = request_func(params)
        resp.raise_for_status()
        return extract_func(resp)


def resolve_object(objectname, *, resolver=None, resolve_all=False):
    """
    Resolves one or more object names to a position on the sky.

    Parameters
    ----------
    objectname : str
        Name(s) of astronomical object(s) to resolve.
    resolver : str, optional
        The resolver to use when resolving a named target into coordinates. Valid options are "SIMBAD" and "NED".
        If not specified, the default resolver order will be used. Please see the
        `STScI Archive Name Translation Application (SANTA) <https://mastresolver.stsci.edu/Santa-war/>`__
        for more information. If ``resolve_all`` is True, this parameter will be ignored. Default is None.
    resolve_all : bool, optional
        If True, will try to resolve the object name using all available resolvers ("NED", "SIMBAD").
        Default is False.

    Returns
    -------
    response : `~astropy.coordinates.SkyCoord`, dict
        If ``resolve_all`` is False and a single object is passed, returns a `~astropy.coordinates.SkyCoord` object with
        the resolved coordinates.
        If ``resolve_all`` is True and a single object is passed, returns a dictionary where the keys are the resolver
        names and the values are `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.
        If ``resolve_all`` is False and multiple objects are passed, returns a dictionary where the keys are the object
        names and the values are `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.
        If ``resolve_all`` is True and multiple objects are passed, returns a dictionary where the keys are the object
        names and the values are nested dictionaries where the keys are the resolver names and the values are
        `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.
    """
    # Normalize input
    object_names = [objectname] if isinstance(objectname, str) else list(objectname)
    single = len(object_names) == 1

    is_catalog = False  # Flag to check if object name belongs to a MAST catalog
    catalog = None  # Variable to store the catalog name
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
            for object in object_names:
                if object.startswith(prefix):
                    is_catalog = True
                    catalog = name
                    break

    # Send request to STScI Archive Name Translation Application (SANTA)
    params = {'outputFormat': 'json',
              'resolveAll': resolve_all or is_catalog}  # Always set resolveAll to True for MAST catalogs
    if resolver and not params['resolveAll']:
        params['resolver'] = resolver

    # Fetch results (batching if necessary)
    results = _batched_request(
        object_names,
        params,
        max_batch=30,
        param_key="name",
        request_func=lambda p: _simple_request("http://mastresolver.stsci.edu/Santa-war/query", p),
        extract_func=lambda r: r.json().get("resolvedCoordinate") or [],
        desc=f"Resolving {len(object_names)} object names")

    resolved_coords = {}
    for object in object_names:
        obj_results = [res for res in results if res.get('searchString') == object.lower()]
        # If a resolver is specified and resolve_all is False, find and return the result for that resolver
        if resolver and not resolve_all:
            resolver_result = next((res for res in obj_results if res.get('resolver') == resolver), None)
            if not resolver_result:
                msg = (f'Could not resolve "{object}" to a sky position using resolver "{resolver}". '
                       'Please try another resolver or set `resolver=None` to use the first '
                       'compatible resolver.')
                if single:
                    raise ResolverError(msg)
                else:
                    warnings.warn(msg, InputWarning)
                    continue
            resolver_coord = SkyCoord(resolver_result['ra'], resolver_result['decl'], unit='deg')

            # If object belongs to a MAST catalog, check the separation between the coordinates from the
            # resolver and the catalog
            if is_catalog:
                catalog_result = next((res for res in obj_results if res.get('resolver') == catalog), None)
                if catalog_result:
                    catalog_coord = SkyCoord(catalog_result['ra'], catalog_result['decl'], unit='deg')
                    if resolver_coord.separation(catalog_coord) > 1 * u.arcsec:
                        # Warn user if the coordinates differ by more than 1 arcsec
                        warnings.warn(f'Resolver {resolver} returned coordinates that differ from MAST '
                                      f'{catalog} catalog by more than 1 arcsec. ', InputWarning)

            log.debug(f'Coordinates resolved using {resolver}: {resolver_coord}')
            resolved_coords[object] = resolver_coord
            continue

        if not obj_results:
            msg = f'Could not resolve "{object}" to a sky position.'
            if single:
                raise ResolverError(msg)
            else:
                warnings.warn(msg, InputWarning)
                continue

        # Return results for all compatible resolvers
        if resolve_all:
            # Return results for all compatible resolvers
            coords = {
                res['resolver']: SkyCoord(res['ra'], res['decl'], unit='deg')
                for res in obj_results
            }
            resolved_coords[object] = coords
            continue

        # Case when resolve_all is False and no resolver is specified
        # SANTA returns result from first compatible resolver
        coord = SkyCoord(obj_results[0]['ra'], obj_results[0]['decl'], unit='deg')
        log.debug(f'Coordinates resolved using {obj_results[0]["resolver"]}: {coord}')
        resolved_coords[object] = coord

    # If no objects could be resolved, raise an error
    if not resolved_coords:
        raise ResolverError("Could not resolve any of the given object names to sky positions.")

    # If input was a single object name, return a single SkyCoord object or dict
    return list(resolved_coords.values())[0] if single else resolved_coords


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
        The given coordinates, or object's location as an `~astropy.coordinates.SkyCoord` object
        in the ICRS frame.
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

    # Parse coordinates, if given
    if coordinates:
        obj_coord = commons.parse_coordinates(coordinates, return_frame='icrs')

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


def _combine_positive_negative_masks(mask_funcs):
    """
    Combines a list of mask functions into a single mask according to:
    - OR logic among positive masks
    - AND logic among negative masks applied after positives

    Parameters
    ----------
    mask_funcs : list of tuples (func, is_negated)
        Each element is a tuple where:
        - func: a callable that takes an array and returns a boolean mask
        - is_negated: boolean, True if the mask should be negated before combining

    Returns
    -------
    combined_mask : np.ndarray
        Combined boolean mask.
    """
    def combined(col):
        positive_masks = [f(col) for f, neg in mask_funcs if not neg]
        negative_masks = [~f(col) for f, neg in mask_funcs if neg]

        # Use OR logic between positive masks
        pos_mask = np.logical_or.reduce(positive_masks) if positive_masks else np.ones(len(col), dtype=bool)

        # Use AND logic between negative masks
        neg_mask = np.logical_and.reduce(negative_masks) if negative_masks else np.ones(len(col), dtype=bool)

        # Use AND logic to combine positive and negative masks
        return pos_mask & neg_mask

    return combined


def parse_numeric_product_filter(vals):
    """
    Parses a numeric product filter value and returns a function that can be used to filter
    a column of a product table.

    Parameters
    ----------
    val : str or list of str
        The filter value(s). Each entry can be:
        - A single number (e.g., "100")
        - A range in the form "start..end" (e.g., "100..200")
        - A comparison operator followed by a number (e.g., ">=10", "<5", ">100.5")

    Returns
    -------
    response : function
        A function that takes a column of a product table and returns a boolean mask indicating
        which rows satisfy the filter condition.
    """
    # Regular expression to match range patterns
    range_pattern = re.compile(r'[+-]?(\d+(\.\d*)?|\.\d+)\.\.[+-]?(\d+(\.\d*)?|\.\d+)')

    def base_condition(cond_str):
        """Create a mask function for a numeric condition string (no negation handling here)."""
        if isinstance(cond_str, (int, float)):
            return lambda col: col == float(cond_str)
        elif cond_str.startswith('>='):
            return lambda col: col >= float(cond_str[2:])
        elif cond_str.startswith('<='):
            return lambda col: col <= float(cond_str[2:])
        elif cond_str.startswith('>'):
            return lambda col: col > float(cond_str[1:])
        elif cond_str.startswith('<'):
            return lambda col: col < float(cond_str[1:])
        elif range_pattern.fullmatch(cond_str):
            start, end = map(float, cond_str.split('..'))
            return lambda col: (col >= start) & (col <= end)
        else:
            return lambda col: col == float(cond_str)

    vals = [vals] if not isinstance(vals, list) else vals
    mask_funcs = []
    for v in vals:
        # Check if the value is negated and strip the negation if present
        is_negated = isinstance(v, str) and v.startswith('!')
        v = v[1:] if is_negated else v

        func = base_condition(v)
        mask_funcs.append((func, is_negated))

    return _combine_positive_negative_masks(mask_funcs)


def apply_column_filters(products, filters):
    """
    Applies column-based filters to a product table.

    Parameters
    ----------
    products : `~astropy.table.Table`
        The product table to filter.
    filters : dict
        A dictionary where keys are column names and values are the filter values.

    Returns
    -------
    col_mask : `numpy.ndarray`
        A boolean mask indicating which rows of the product table satisfy the filter conditions.
    """
    col_mask = np.ones(len(products), dtype=bool)  # Start with all True mask

    # Applying column-based filters
    for colname, vals in filters.items():
        if colname not in products.colnames:
            raise InvalidQueryError(f"Column '{colname}' not found in product table.")

        col_data = products[colname]
        # If the column is an integer or float, accept numeric filters
        if col_data.dtype.kind in ['i', 'f']:  # 'i' for integer, 'f' for float
            try:
                this_mask = parse_numeric_product_filter(vals)(col_data)
            except ValueError:
                raise InvalidQueryError(f"Could not parse numeric filter '{vals}' for column '{colname}'.")
        else:  # Assume string or list filter
            vals = [vals] if isinstance(vals, str) else vals
            mask_funcs = []
            for val in vals:
                # Check if the value is negated and strip the negation if present
                is_negated = isinstance(val, str) and val.startswith('!')
                v = val[1:] if is_negated else val

                def func(col, v=v):
                    return np.isin(col, [v])
                mask_funcs.append((func, is_negated))

            this_mask = _combine_positive_negative_masks(mask_funcs)(col_data)

        # AND logic across different columns
        col_mask &= this_mask

    return col_mask
