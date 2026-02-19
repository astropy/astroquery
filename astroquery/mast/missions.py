# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Missions
=================

This module contains methods for searching MAST missions.
"""

import difflib
import json
import warnings
from collections.abc import Iterable
from json import JSONDecodeError
from pathlib import Path
from urllib.parse import quote

import astropy.units as u
from astropy.coordinates import SkyCoord, BaseCoordinateFrame, Angle
import numpy as np
from astropy.table import Table, Row, Column, vstack
from astropy.utils.decorators import deprecated_renamed_argument
from requests import HTTPError, RequestException

from astroquery import log
from astroquery.utils import commons, async_to_sync
from astroquery.utils.class_or_instance import class_or_instance
from astroquery.exceptions import InputWarning, InvalidQueryError, MaxResultsWarning, NoResultsWarning, ResolverError

from astroquery.mast import utils
from astroquery.mast.core import MastQueryWithLogin

from . import conf

__all__ = ['MastMissionsClass', 'MastMissions']


@async_to_sync
class MastMissionsClass(MastQueryWithLogin):
    """
    MastMissions search class.
    Class that allows direct programmatic access to retrieve metadata via the MAST search API for a given mission.
    """

    # Static class variables
    _search = 'search'
    _list_products = 'post_list_products'

    # Workaround so that observation_id is returned in ULLYSES queries that do not specify columns
    _default_ullyses_cols = ['target_name_ullyses', 'target_classification', 'targ_ra', 'targ_dec', 'host_galaxy_name',
                             'spectral_type', 'bmv0_mag', 'u_mag', 'b_mag', 'v_mag', 'gaia_g_mean_mag', 'star_mass',
                             'instrument', 'grating', 'filter', 'observation_id']

    # Maximum supported query radius
    _max_query_radius = 30 * u.arcmin

    # Maximum number of input targets accepted in a single query
    _max_input_targets = 100

    def __init__(self, *, mission='hst', mast_token=None):
        super().__init__(mast_token=mast_token)

        self.dataset_kwds = {  # column keywords corresponding to dataset ID
            'hst': 'sci_data_set_name',
            'jwst': 'fileSetName',
            'roman': 'fileSetName',
            'classy': 'Target',
            'ullyses': 'observation_id',
            'iue': 'iue_data_id'
        }

        # Service attributes
        self.service = self._search  # current API service
        self.service_dict = {self._search: {'path': self._search},
                             self._list_products: {'path': self._list_products}}

        # Search attributes
        self._search_option_fields = ['limit', 'offset', 'sort_by', 'search_key', 'sort_desc', 'select_cols',
                                      'skip_count', 'user_fields']
        self.mission = mission  # current mission
        self.limit = 5000  # maximum number of results
        self.columns = dict()  # columns configuration for each mission

    @property
    def mission(self):
        return self._mission

    @mission.setter
    def mission(self, value):
        # Setter that updates the service parameters if the mission is changed
        self._mission = value.lower()  # case-insensitive
        self._service_api_connection.set_service_params(self.service_dict, f'search/{self.mission}')

    def _extract_products(self, response):
        """
        Extract products from the response of a `~requests.Response` object.

        Parameters
        ----------
        response : `~requests.Response`
            The response object containing the products data.

        Returns
        -------
        list
            A list of products extracted from the response.
        """
        combined = []
        for resp in response:
            products = resp.json().get('products', [])
            # Flatten if nested
            if products and isinstance(products[0], list):
                products = products[0]
            combined.extend(products)
        return combined

    def _parse_result(self, response, *, verbose=False):  # Used by the async_to_sync decorator functionality
        """
        Parse the results of a `~requests.Response` objects and return an `~astropy.table.Table` of results.

        Parameters
        ----------
        response : `~requests.Response`
            `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False. Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        if self.service == self._search:
            results = self._service_api_connection._parse_result(response, verbose, data_key='results')

            # Warn if maximum results are returned
            if len(results) >= self.limit:
                warnings.warn("Maximum results returned, may not include all sources within radius.",
                              MaxResultsWarning)
            return results

        elif self.service == self._list_products:
            products = self._extract_products(response)
            return Table(products)

    def _validate_criteria(self, **criteria):
        """
        Check that criteria keyword arguments are valid column names for the mission.
        Raises InvalidQueryError if a criteria argument is invalid.

        Parameters
        ----------
        **criteria
            Keyword arguments representing criteria filters to apply.

        Raises
        -------
        InvalidQueryError
            If a keyword does not match any valid column names, an error is raised that suggests the closest
            matching column name, if available.
        """
        # Ensure that self.columns is populated
        self.get_column_list()

        # Check each criteria argument for validity
        valid_cols = list(self.columns[self.mission]['name']) + self._search_option_fields
        for kwd in criteria.keys():
            col = next((name for name in valid_cols if name == kwd), None)
            if not col:
                closest_match = difflib.get_close_matches(kwd, valid_cols, n=1)
                error_msg = (
                    f"Filter '{kwd}' does not exist. Did you mean '{closest_match[0]}'?"
                    if closest_match
                    else f"Filter '{kwd}' does not exist."
                )
                raise InvalidQueryError(error_msg)

    def _build_params_from_criteria(self, params, **criteria):
        """
        Build the parameters for the API request based on the provided criteria.

        Parameters
        ----------
        params : dict
            Dictionary to store the parameters for the API request.
        **criteria
            Keyword arguments representing criteria filters to apply.
        """
        # Add each criterion to the params dictionary
        params['conditions'] = []
        for prop, value in criteria.items():
            if prop not in self._search_option_fields:
                if isinstance(value, list):
                    # Convert to comma-separated string if passed as a list
                    value = ','.join(str(item) for item in value)
                params['conditions'].append({prop: value})
            else:
                if prop == 'sort_by' and isinstance(value, str):
                    # Convert to list if passed as a string
                    value = [value]
                if prop == 'sort_desc' and isinstance(value, bool):
                    # Convert to list if passed as a boolean
                    value = [value]
                params[prop] = value

    def _parse_select_cols(self, select_cols):
        """
        Parse the select_cols parameter to ensure it is in the correct format.

        Parameters
        ----------
        select_cols : iterable or str or None
            The select_cols parameter to parse.

        Returns
        -------
        list
            A list of column names to select.

        Raises
        ------
        InvalidQueryError
            If select_cols is not an iterable of strings, a comma-separated string, 'all', or '*'.
            If any individual column name is not a string.
        """
        if select_cols is None:
            if self.mission == 'ullyses':
                select_cols = self._default_ullyses_cols
            return select_cols

        # Handle special string cases first
        all_columns = self.get_column_list()['name'].value.tolist()
        if isinstance(select_cols, str):
            if (select_cols.lower() == 'all' or select_cols == '*'):
                return all_columns
            # Comma-separated string
            select_cols = select_cols.split(',')

        # Handle an iterable
        elif isinstance(select_cols, Iterable):
            # Convert to list so we can iterate multiple times safely
            select_cols = list(select_cols)

        else:
            raise InvalidQueryError(
                "`select_cols` must be an iterable of column names, a comma-separated string, "
                "'all', or '*'."
            )

        # Validate the column names
        valid_select_cols = []
        for col in select_cols:
            if not isinstance(col, str):
                raise InvalidQueryError(
                    "`select_cols` must contain only strings (column names)."
                )
            col = col.strip()
            if col not in all_columns:
                closest_match = difflib.get_close_matches(col, all_columns, n=1)
                suggestion = f' Did you mean "{closest_match[0]}"?' if closest_match else ''
                warnings.warn(f"Column '{col}' not found.{suggestion}", InputWarning)
            else:
                valid_select_cols.append(col)

        # Dataset ID column should always be returned
        dataset_col = self.dataset_kwds.get(self.mission, None)
        if dataset_col and dataset_col not in valid_select_cols:
            valid_select_cols.append(dataset_col)
        return valid_select_cols

    def _parse_multiple_locations(self, locations, *, resolver=None):
        """
        Parse multiple locations (either objectnames or coordinates) into a list of target strings.

        Parameters
        ----------
        locations : str, iterable of str, or `~astropy.coordinates` object
            Multiple locations can be specified as:
            - A comma-separated string (e.g., "M31, M51, NGC 1234")
            - An iterable of strings (e.g., ["M31", "M51", "NGC 1234"])
            - An iterable of coordinate objects or coordinate strings
            - A single string or coordinate object (will be converted to a single-item list)
        resolver : str, optional
            The resolver to use when resolving named targets into coordinates.

        Returns
        -------
        list of str
            A list of target strings in "ra dec" format for the API.
        """
        # Convert input to a list of location items
        if isinstance(locations, str):
            location_items = [loc.strip() for loc in locations.split(',') if loc.strip()]
        elif isinstance(locations, Iterable) and not isinstance(locations, (SkyCoord, BaseCoordinateFrame)):
            location_items = list(locations)
        else:
            # Single coordinate object
            location_items = [locations]

        if not location_items:
            raise InvalidQueryError("No targets were provided.")

        if len(location_items) > self._max_input_targets:
            raise InvalidQueryError(
                f'Too many input targets provided. Maximum supported is {self._max_input_targets}, '
                f'got {len(location_items)}.'
            )

        target_strings = [None] * len(location_items)
        unresolved_map = {}  # name -> list of indices

        # First pass -> attempt parsing coordinates
        for idx, item in enumerate(location_items):
            try:
                # Try to parse as coordinates
                coords = commons.parse_coordinates(item, return_frame='icrs', resolve_names=False)
                target_strings[idx] = f"{coords.ra.deg} {coords.dec.deg}"
            except (ValueError, TypeError, u.UnitsError):
                # Not coordinates; must be a string to resolve as object name
                if not isinstance(item, str):
                    raise InvalidQueryError(
                        f"Target {item} is not a valid coordinate or object name string"
                    )
                unresolved_map.setdefault(item.strip(), []).append(idx)

        # Second pass -> resolve object names in batch requests
        resolved_map = {}
        if unresolved_map:
            try:
                unresolved_names = list(unresolved_map.keys())
                resolved = utils.resolve_object(unresolved_names, resolver=resolver)
                if isinstance(resolved, SkyCoord):
                    resolved_map = {unresolved_names[0]: resolved}
                else:
                    resolved_map = resolved
            except (ResolverError) as e:
                if target_strings.count(None) == len(target_strings):
                    # If no coordinates were successfully parsed or resolved, raise the error.
                    # Otherwise, just warn and continue with the successfully parsed/resolved targets.
                    raise
                else:
                    warnings.warn(f"Object name targets could not be resolved and will be skipped: {e}", InputWarning)

        # Fill resolved names back into all matching positions (including duplicates)
        for name, indices in unresolved_map.items():
            coords = resolved_map.get(name)
            if coords is None:
                continue
            coord_str = f"{coords.ra.deg} {coords.dec.deg}"
            for idx in indices:
                target_strings[idx] = coord_str

        successful = [target for target in target_strings if target is not None]

        return successful

    @class_or_instance
    @deprecated_renamed_argument('coordinates', 'target', since='0.4.11')
    @deprecated_renamed_argument('objectname', 'target', since='0.4.11')
    def query_criteria_async(self, *, target=None, coordinates=None, objectname=None, radius=3*u.arcmin,
                             limit=5000, offset=0, select_cols=None, resolver=None, **criteria):
        """
        Given a set of search criteria, returns a list of mission metadata.

        Parameters
        ----------
        target : str, list of str, or None, optional
            Target(s) to search. Can be a specified as:
            - A single string or `~astropy.coordinates.SkyCoord` object representing either
            an object name or coordinates (e.g., "M31" or "10.0 20.0")
            - A comma-separated string of object names or coordinates (e.g., "M31, 10.0 20.0, NGC 1234")
            - An iterable of strings or `~astropy.coordinates.SkyCoord` objects (e.g., ["M31", "10.0 20.0", "NGC 1234"])
            This is the preferred way to search for targets and allows for a mix of object names and coordinates.
            If provided, this takes precedence over the `coordinates` and `objectname` parameters.
        coordinates : str or `~astropy.coordinates` object, deprecated
            Deprecated. Use `target` instead. The target around which to search. It may be specified
            as a string or as the appropriate `~astropy.coordinates` object. To search around multiple
            coordinates, use the `target` parameter instead.
        objectname : str, deprecated
            Deprecated. Use `target` instead. The name of the target around which to search. To search
            around multiple object names, use the `target` parameter instead.
        radius : str or `~astropy.units.Quantity` object
            Default is 3 arcminutes. The radius around the coordinates to search within.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `~astropy.units` may also be used.
            The maximum supported query radius is 30 arcminutes.
        limit : int
            Default is 5000. The maximum number of dataset IDs in the results.
        offset : int
            Default is 0. The number of records you wish to skip before selecting records.
        select_cols: iterable or str or None, optional
            Default is None. Names of columns that will be included in the result table.
            If None, a default set of columns will be returned.
            Can either be an iterable of column names, a comma-separated string of column names,
            or 'all'/'*' to return all available columns.
        resolver : str, optional
            Default is None. The resolver to use when resolving a named target into coordinates. Valid options are
            "SIMBAD" and "NED". If not specified, the default resolver order will be used. Please see the
            `STScI Archive Name Translation Application (SANTA) <https://mastresolver.stsci.edu/Santa-war/>`__
            for more information. Default is None.
        **criteria
            Criteria to apply. Valid criteria include coordinates, objectname, radius (as in
            `~astroquery.mast.missions.MastMissionsClass.query_region` and
            `~astroquery.mast.missions.MastMissionsClass.query_object` functions),
            and all fields listed in the column documentation for the mission being queried.
            List of all valid fields that can be used to match results on criteria can be retrieved by calling
            `~astroquery.mast.missions.MastMissionsClass.get_column_list` function.
            To filter by multiple values for a single column, pass in a list of values or
            a comma-separated string of values.

        Returns
        -------
        response : list of `~requests.Response`

        Raises
        ------
        InvalidQueryError
            If the query radius is larger than the limit (30 arcminutes).
        """

        self.limit = limit
        self.service = self._search

        # Check that criteria arguments are valid
        self._validate_criteria(**criteria)

        target_strings = None
        if target is not None:
            # Use the new target parameter - parse as multiple locations
            target_strings = self._parse_multiple_locations(target, resolver=resolver)
        elif objectname is not None or coordinates is not None:
            # Legacy behavior: use objectname or coordinates
            coordinates = utils.parse_input_location(coordinates=coordinates,
                                                     objectname=objectname,
                                                     resolver=resolver)

        # if radius is just a number we assume degrees
        radius = Angle(radius, u.arcmin)

        if radius > self._max_query_radius:
            raise InvalidQueryError(
                f"Query radius too large. Must be ≤{self._max_query_radius}, got {radius}."
            )

        # build query
        params = {"limit": self.limit, "offset": offset, 'select_cols': self._parse_select_cols(select_cols)}
        if coordinates is not None:
            params["target"] = [f"{coordinates.ra.deg} {coordinates.dec.deg}"]
            params["radius"] = radius.arcsec
            params["radius_units"] = 'arcseconds'
        if target_strings:
            params["target"] = target_strings
            params["radius"] = radius.arcsec
            params["radius_units"] = 'arcseconds'

        self._build_params_from_criteria(params, **criteria)

        return self._service_api_connection.missions_request_async(self.service, params)

    @class_or_instance
    def query_region_async(self, coordinates, *, radius=3*u.arcmin, limit=5000, offset=0,
                           select_cols=None, **criteria):
        """
        Given a sky position (or positions) and radius, returns a list of matching dataset IDs.

        Parameters
        ----------
        coordinates : str, iterable of str, or `~astropy.coordinates` object
            The target(s) around which to search. Can be specified as:
            - A single coordinate string or `~astropy.coordinates` object
            - A comma-separated string of coordinates (e.g., "10.0 20.0, 15.0 25.0")
            - An iterable of coordinate strings or `~astropy.coordinates` objects
        radius : str or `~astropy.units.Quantity` object
            Default is 3 arcminutes. The radius around the coordinates to search within.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `~astropy.units` may also be used.
            The maximum supported query radius is 30 arcminutes.
        limit : int
            Default is 5000. The maximum number of dataset IDs in the results.
        offset : int
            Default is 0. The number of records you wish to skip before selecting records.
        select_cols: iterable or str or None, optional
            Default is None. Names of columns that will be included in the result table.
            If None, a default set of columns will be returned.
            Can either be an iterable of column names, a comma-separated string of column names,
            or 'all'/'*' to return all available columns.
        **criteria
            Other mission-specific criteria arguments.
            All valid filters can be found using `~astroquery.mast.missions.MastMissionsClass.get_column_list`
            function.
            For example, one can specify the output columns(select_cols) or use other filters(conditions).
            To filter by multiple values for a single column, pass in a list of values or
            a comma-separated string of values.

        Returns
        -------
        response : list of `~requests.Response`

        Raises
        ------
        InvalidQueryError
            If the query radius is larger than the limit (30 arcminutes).
        """
        return self.query_criteria_async(target=coordinates,
                                         radius=radius,
                                         limit=limit,
                                         offset=offset,
                                         select_cols=select_cols,
                                         **criteria)

    @class_or_instance
    def query_object_async(self, objectname, *, radius=3*u.arcmin, limit=5000, offset=0,
                           select_cols=None, resolver=None, **criteria):
        """
        Given an object name (or names), returns a list of matching rows.

        Parameters
        ----------
        objectname : str or iterable of str
            The name(s) of the target(s) around which to search. Can be specified as:
            - A single object name string
            - A comma-separated string of object names (e.g., "M31, M51, NGC 1234")
            - An iterable of object name strings
        radius : str or `~astropy.units.Quantity` object, optional
            Default is 3 arcminutes. The radius around the coordinates to search within.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `~astropy.units` may also be used.
        limit : int
            Default is 5000. The maximum number of dataset IDs in the results.
        offset : int
            Default is 0. The number of records you wish to skip before selecting records.
        select_cols: iterable or str or None, optional
            Default is None. Names of columns that will be included in the result table.
            If None, a default set of columns will be returned.
            Can either be an iterable of column names, a comma-separated string of column names,
            or 'all'/'*' to return all available columns.
        resolver : str, optional
            Default is None. The resolver to use when resolving a named target into coordinates. Valid options are
            "SIMBAD" and "NED". If not specified, the default resolver order will be used. Please see the
            `STScI Archive Name Translation Application (SANTA) <https://mastresolver.stsci.edu/Santa-war/>`__
            for more information. Default is None.
        **criteria
            Other mission-specific criteria arguments.
            All valid filters can be found using `~astroquery.mast.missions.MastMissionsClass.get_column_list`
            function.
            For example, one can specify the output columns(select_cols) or use other filters(conditions).
            To filter by multiple values for a single column, pass in a list of values or
            a comma-separated string of values.

        Returns
        -------
        response : list of `~requests.Response`
        """
        return self.query_criteria_async(target=objectname,
                                         radius=radius,
                                         limit=limit,
                                         offset=offset,
                                         select_cols=select_cols,
                                         resolver=resolver,
                                         **criteria)

    @class_or_instance
    def get_product_list_async(self, datasets, *, batch_size=1000):
        """
        Given a dataset ID or list of dataset IDs, returns a list of associated data products.

        To return unique data products, use ``MastMissions.get_unique_product_list``.

        Parameters
        ----------
        datasets : str, list, `~astropy.table.Row`, `~astropy.table.Column`, `~astropy.table.Table`
            Row/Table of MastMissions query results (e.g. output from `query_object`)
            or single/list of dataset ID(s).
        batch_size : int, optional
            Default 1000. Number of dataset IDs to include in each batch request to the server.
            If you experience timeouts or connection errors, consider lowering this value.

        Returns
        -------
        response : list of `~requests.Response`
        """

        self.service = self._list_products

        if isinstance(datasets, Table) or isinstance(datasets, Row):
            dataset_kwd = self.get_dataset_kwd()
            if not dataset_kwd:
                raise InvalidQueryError(f'Dataset keyword not found for mission "{self.mission}". Please input '
                                        'dataset IDs as a string, list of strings, or `~astropy.table.Column`.')

        # Extract dataset IDs based on input type and mission
        if isinstance(datasets, Table):
            datasets = datasets[dataset_kwd].tolist()
        elif isinstance(datasets, Row):
            datasets = [datasets[dataset_kwd]]
        elif isinstance(datasets, Column):
            datasets = datasets.tolist()
        elif isinstance(datasets, str):
            datasets = [datasets]
        elif not isinstance(datasets, list):
            raise TypeError('Unsupported data type for `datasets`. Expected string, '
                            'list of strings, Astropy Row, Astropy Column, or Astropy Table.')

        # Filter out empty strings from IDs
        datasets = [item.strip() for item in datasets if item and item.strip()]
        if not datasets:
            raise InvalidQueryError("Dataset list is empty, no associated products.")

        # Filter out duplicates
        datasets = list(set(datasets))

        results = utils._batched_request(
            datasets,
            params={},
            max_batch=batch_size,
            param_key="dataset_ids",
            request_func=lambda p: self._service_api_connection.missions_request_async(self.service, p),
            extract_func=lambda r: [r],  # missions_request_async already returns one result
            desc=f"Fetching products for {len(datasets)} unique datasets"
        )

        # Return a list of responses
        return results

    def get_unique_product_list(self, datasets, *, batch_size=1000):
        """
        Given a dataset ID or list of dataset IDs, returns a list of associated data products with unique
        filenames.

        Parameters
        ----------
        datasets : str, list, `~astropy.table.Row`, `~astropy.table.Column`, `~astropy.table.Table`
            Row/Table of MastMissions query results (e.g. output from `query_object`)
            or single/list of dataset ID(s).
        batch_size : int, optional
            Default 1000. Number of dataset IDs to include in each batch request to the server.
            If you experience timeouts or connection errors, consider lowering this value.

        Returns
        -------
        unique_products : `~astropy.table.Table`
            Table containing products with unique URIs.
        """
        products = self.get_product_list(datasets, batch_size=batch_size)
        unique_products = utils.remove_duplicate_products(products, 'filename')
        if len(unique_products) < len(products):
            log.info("To return all products, use `MastMissions.get_product_list`")
        return unique_products

    def filter_products(self, products, *, extension=None, **filters):
        """
        Filters an `~astropy.table.Table` of mission data products based on given filters.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing data products to be filtered.
        extension : string or array, optional
            Default is None. Filters by file extension(s), matching any specified extensions.
        **filters :
            Column-based filters to apply to the products table.

            Each keyword corresponds to a column name in the table, with the argument being one or more
            acceptable values for that column. AND logic is applied between filters.

            Within each column's filter set:

            - Positive (non-negated) values are combined with OR logic.
            - Any negated values (prefixed with "!") are combined with AND logic against the ORed positives.
              This results in: (NOT any_negatives) AND (any_positives)
              Examples:
              ``file_suffix=['A', 'B', '!C']`` → (file_suffix != C) AND (file_suffix == A OR file_suffix == B)
              ``size=['!14400', '<20000']`` → (size != 14400) AND (size < 20000)

            For columns with numeric data types (int or float), filter values can be expressed
            in several ways:

            - A single number: ``size=100``
            - A range in the form "start..end": ``size="100..1000"``
            - A comparison operator followed by a number: ``size=">=1000"``
            - A list of expressions (OR logic): ``size=[100, "500..1000", ">=1500"]``

        Returns
        -------
        response : `~astropy.table.Table`
            Filtered Table of data products.
        """

        # Start with a mask of True for all entries
        filter_mask = np.full(len(products), True, dtype=bool)

        # Filter by file extension, if provided
        if extension:
            ext_mask = utils.apply_extension_filter(products, extension, 'filename')
            filter_mask &= ext_mask

        # Apply column-based filters
        col_mask = utils.apply_column_filters(products, filters)
        filter_mask &= col_mask

        return products[filter_mask]

    def download_file(self, uri, *, local_path=None, cache=True, verbose=True):
        """
        Downloads a single file based on the data URI.

        Parameters
        ----------
        uri : str
            The product filename or URI to be downloaded.
        local_path : str
            Directory or filename to which the file will be downloaded.  Defaults to current working directory.
        cache : bool
            Default is True. If file is found on disk, it will not be downloaded again.
        verbose : bool, optional
            Default is True. Whether to show download progress in the console.

        Returns
        -------
        status: str
            Download status message.  Either COMPLETE, SKIPPED, or ERROR.
        msg : str
            An error status message, if any.
        url : str
            The full URL download path.
        """

        # Construct the full data URL based on mission
        if self.mission in ['hst', 'jwst', 'roman', 'roman_spectra', 'roman_cgi']:
            # HST, JWST, and RST have a dedicated endpoint for retrieving products
            base_url = self._service_api_connection.MISSIONS_DOWNLOAD_URL + self.mission + '/api/v0.1/retrieve_product'
            keyword = 'product_name'
        else:
            # HLSPs use MAST download URL
            base_url = self._service_api_connection.MAST_DOWNLOAD_URL
            keyword = 'uri'
            # These files require a MAST URI and not just a filename
            if not uri.startswith('mast:'):
                raise InvalidQueryError(f'For mission "{self.mission}", a full MAST URI is required for downloading. '
                                        f'Got "{uri}".')
        data_url = base_url + f'?{keyword}=' + uri
        escaped_url = base_url + f'?{keyword}=' + quote(uri, safe='')

        # Determine local file path. Use current directory as default.
        filename = Path(uri).name
        local_path = Path(local_path or filename)
        if not local_path.suffix:  # Append filename if local path is directory
            local_path = local_path / filename
            local_path.parent.mkdir(parents=True, exist_ok=True)

        status = 'COMPLETE'
        msg = None
        url = None

        try:
            # Attempt file download
            self._download_file(escaped_url, local_path, cache=cache, verbose=verbose)

            # Check if file exists
            if not local_path.is_file() and status != 'SKIPPED':
                status = 'ERROR'
                msg = 'File was not downloaded'
                url = data_url

        except HTTPError as err:
            if err.response.status_code == 401:
                no_auth_msg = f'You are not authorized to download from {data_url}.'
                if self._authenticated:
                    no_auth_msg += ('\nYou do not have access to download this data, or your authentication '
                                    'token may be expired. You can generate a new token at '
                                    'https://auth.mast.stsci.edu/token?suggested_name=Astroquery&'
                                    'suggested_scope=mast:exclusive_access')
                else:
                    no_auth_msg += ('\nPlease authenticate yourself using the `~astroquery.mast.MastMissions.login` '
                                    'function or initialize `~astroquery.mast.MastMissions` with an authentication '
                                    'token.')
                log.warning(no_auth_msg)
            status = 'ERROR'
            msg = f'HTTPError: {err}'
            url = data_url

        return status, msg, url

    def _download_files(self, products, base_dir, *, flat=False, cache=True, verbose=True):
        """
        Downloads files listed in an `~astropy.table.Table` of data products to a specified directory.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing products to be downloaded.
        base_dir : str
            Directory in which files will be downloaded.
        flat : bool
            Default is False.  If True, all files are downloaded directly to `base_dir`, and no subdirectories
            will be created.
        cache : bool
            Default is True. If file is found on disk, it will not be downloaded again.
        verbose : bool, optional
            Default is True. Whether to show download progress in the console.

        Returns
        -------
        response : `~astropy.table.Table`
            Table containing download results for each data product file.
        """

        manifest_entries = []
        base_dir = Path(base_dir)

        for data_product in products:
            col_names = data_product.colnames
            # Determine local path for each file
            filename = data_product['filename']
            uri = data_product['uri'] if 'uri' in col_names else filename
            dataset = None
            if 'dataset' in col_names:
                dataset = data_product['dataset']
            elif 'fileset' in col_names:
                dataset = data_product['fileset']
            if not dataset and not flat:
                raise InvalidQueryError('Data product is missing "dataset" or "fileset" field required for '
                                        'constructing local download path. Specify `flat=True` to avoid this '
                                        'requirement.')
            local_path = base_dir / dataset if not flat else base_dir
            local_path.mkdir(parents=True, exist_ok=True)
            local_file_path = local_path / Path(filename).name

            # Download files and record status
            status, msg, url = self.download_file(uri,
                                                  local_path=local_file_path,
                                                  cache=cache,
                                                  verbose=verbose)
            manifest_entries.append([local_file_path, status, msg, url])

        # Return manifest as Astropy Table
        manifest = Table(rows=manifest_entries, names=('Local Path', 'Status', 'Message', 'URL'))
        return manifest

    def download_products(self, products, *, download_dir=None, flat=False,
                          cache=True, extension=None, verbose=True, **filters):
        """
        Download specified data products.

        Parameters
        ----------
        products : str, list of str, `~astropy.table.Table`, or list of dict
            Either a single or list of dataset IDs (e.g., as input for `get_product_list`),
            a Table of products (e.g., as output from `get_product_list`), or a JSON file or data from
            the MAST subscription service containing product information.
        download_dir : str or Path, optional
            Directory for file downloads.  Defaults to current directory.
        flat : bool, optional
            Default is False. If False, puts files into the standard
            directory structure of "mastDownload/<mission>/<dataset ID>/".
            If True, places files directly in ``download_dir`` without subdirectories.
        cache : bool, optional
            Default is True. If file is found on disc, it will not be downloaded again.
        extension : string or list, optional
            Default is None. Filter by file extension.
        verbose : bool, optional
            Default is True. Whether to show download progress in the console.
        **filters :
            Column-based filters to be applied.
            Each keyword corresponds to a column name in the table, with the argument being one or more
            acceptable values for that column. AND logic is applied between filters, OR logic within
            each filter set.
            For example: type="science", extension=["fits","jpg"]

        Returns
        -------
        manifest : `~astropy.table.Table`
            A table manifest showing downloaded file locations and statuses.
        """
        if not products:
            raise InvalidQueryError('No products specified for download.')

        # Ensure `products` is a Table, collecting products if necessary
        if (isinstance(products, str) and products.endswith('.json')) or isinstance(products, Path):
            # Products coming from local JSON filepath from subscription service
            try:
                with open(products, 'r') as f:
                    json_data = json.load(f)
            except JSONDecodeError as ex:
                raise InvalidQueryError(f'Failed to decode JSON file at {products}: {ex}')

            if not isinstance(json_data, (list, tuple)):
                raise InvalidQueryError(f'Expected a list of product rows in JSON file at {products}.')
            products = Table(rows=json_data)
        elif isinstance(products, (list)) and all(isinstance(prod, dict) for prod in products):
            # Products coming from JSON data from subscription service
            products = Table(rows=products)
        elif isinstance(products, (str, list)):
            # Products given as dataset ID(s)
            products = [products] if isinstance(products, str) else products
            products = vstack([self.get_product_list(oid) for oid in products])
        elif isinstance(products, Row):
            # Single row of products
            products = Table(products, masked=True)

        # Apply filters
        products = self.filter_products(products, extension=extension, **filters)

        # Remove duplicates
        products = utils.remove_duplicate_products(products, 'filename')

        if not len(products):
            warnings.warn("No products to download after applying filters.", NoResultsWarning)
            return

        # Set up base directory for downloads
        download_dir = Path(download_dir or '.')
        base_dir = download_dir if flat else download_dir / 'mastDownload' / self.mission

        # Download files
        manifest = self._download_files(products,
                                        base_dir=base_dir,
                                        flat=flat,
                                        cache=cache,
                                        verbose=verbose)

        return manifest

    @class_or_instance
    def get_column_list(self):
        """
        For a mission, return a list of all searchable columns and their descriptions

        Returns
        -------
        response : `~astropy.table.Table` that contains columns names, types, and descriptions
        """
        if not self.columns.get(self.mission):
            try:
                # Send server request to get column list for current mission
                params = {'mission': self.mission}
                resp = utils._simple_request(f'{conf.server}/search/util/api/v0.1/column_list', params)

                # Parse JSON and extract necessary info
                results = resp.json()
                rows = [
                    (result['column_name'], result['qual_type'], result['description'])
                    for result in results
                ]

                # Create Table with parsed data
                col_table = Table(rows=rows, names=('name', 'data_type', 'description'))
                self.columns[self.mission] = col_table
            except JSONDecodeError as ex:
                raise JSONDecodeError(f'Failed to decode JSON response while attempting to get column list'
                                      f' for mission {self.mission}: {ex}')
            except RequestException as ex:
                raise ConnectionError(f'Failed to connect to the server while attempting to get column list'
                                      f' for mission {self.mission}: {ex}')
            except KeyError as ex:
                raise KeyError(f'Expected key not found in response data while attempting to get column list'
                               f' for mission {self.mission}: {ex}')
            except Exception as ex:
                raise RuntimeError(f'An unexpected error occurred while attempting to get column list'
                                   f' for mission {self.mission}: {ex}')

        return self.columns[self.mission]

    def get_dataset_kwd(self):
        """
        Return the Dataset ID keyword for the selected mission. If the keyword is unknown, returns None.

        Returns
        -------
        keyword : str or None
            Dataset ID keyword or None if unknown.
        """
        if self.mission not in self.dataset_kwds:
            log.warning('The mission "%s" does not have a known dataset ID keyword.', self.mission)
            return None

        return self.dataset_kwds[self.mission]


MastMissions = MastMissionsClass()
