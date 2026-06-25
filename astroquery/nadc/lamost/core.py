# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LAMOST Spectroscopic Survey Query Tool
=======================================

This module provides the core implementation for querying LAMOST data.
"""

# Standard library
import os
import warnings
from io import BytesIO

# Third party
import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table
from astropy.io import fits, votable
import numpy as np

# Local imports
from .._response_utils import response_looks_like_html, sanitize_votable_content
from .. import QUERY_DATA_SHARED_TOKEN_ENV_VARS
from .._query_data import (
    _append_min_constraint,
    _append_range_constraint,
    _configured_token_from_env as _configured_token_from_env_base,
    _strip_optional_quotes,
)
from ...query import BaseQuery
from ...utils import commons
from ...exceptions import InvalidQueryError, TableParseError
from . import conf


__all__ = ['Lamost', 'LamostClass',
           'parse_lrs_spectrum', 'parse_mrs_spectrum', 'plot_spectrum']


_TOKEN_ENV_VARS = (
    "ASTROQUERY_LAMOST_TOKEN",
    "ASTROQUERY_NADC_LAMOST_TOKEN",
    "NADC_LAMOST_TOKEN",
    "CHINAVO_LAMOST_TOKEN",
    "ASTROQUERY_LAMOST_ACCESS_TOKEN",
    "ASTROQUERY_NADC_LAMOST_ACCESS_TOKEN",
    "NADC_LAMOST_ACCESS_TOKEN",
    "CHINAVO_LAMOST_ACCESS_TOKEN",
    *QUERY_DATA_SHARED_TOKEN_ENV_VARS,
)


def _configured_token_from_env():
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


def _median_filter_1d_zero_padded(values, kernel_size):
    """
    A lightweight replacement for ``scipy.signal.medfilt`` for 1D arrays.

    Astroquery avoids introducing new hard dependencies for individual modules.
    The original implementation used ``scipy.signal.medfilt`` to provide a
    median-filtered (robustly smoothed) spectrum. This helper replicates the key
    behavior we rely on here:

    - 1D median filter
    - odd kernel size
    - zero-padding at the array edges
    """
    kernel_size = int(kernel_size)
    if kernel_size < 1 or kernel_size % 2 == 0:
        raise ValueError("kernel_size must be a positive odd integer.")

    values = np.asanyarray(values)
    if values.ndim != 1:
        raise ValueError("Only 1D inputs are supported.")

    if values.size < kernel_size:
        warnings.warn(
            f"Input size ({values.size}) is smaller than median filter kernel_size ({kernel_size}).",
            UserWarning
        )

    pad = kernel_size // 2
    padded = np.pad(values, pad_width=pad, mode='constant', constant_values=0)
    windows = np.lib.stride_tricks.sliding_window_view(padded, kernel_size)
    filtered = np.median(windows, axis=-1)
    return filtered.astype(values.dtype, copy=False)


class LamostClass(BaseQuery):
    """
    Class for querying the LAMOST spectroscopic survey database.

    The LAMOST (Large Sky Area Multi-Object Fiber Spectroscopic Telescope)
    survey provides spectroscopic data for millions of stars and galaxies.
    This class provides methods to query the catalog, download spectra,
    and access metadata.
    """

    URL = conf.server
    TIMEOUT = conf.timeout

    def __init__(
        self,
        *,
        token=None,
        data_release=None,
        sub_version=None,
        pylamost_config=None,
    ):
        """
        Initialize a LAMOST query instance.

        Parameters
        ----------
        token : str, optional
            Authentication token for LAMOST API access. Preferred ways to
            provide it are passing ``token`` directly, configuring
            ``astroquery.nadc.lamost.conf.token`` / astroquery.cfg, setting an
            environment variable such as ``ASTROQUERY_NADC_LAMOST_TOKEN``.
        data_release : str, optional
            Data release version (e.g., 'dr10', 'dr11', 'dr12').
            Defaults to value from conf.data_release.
        sub_version : str, optional
            API sub-version (e.g., 'v2.0', 'v1.0').
            Defaults to value from conf.sub_version.
        pylamost_config : str or path-like, optional
            Explicit path to a pylamost-style config file. The file is only
            read when this argument is provided and no token was found from
            ``token``, ``conf.token``, or the environment.

        Notes
        -----
        Explicit pylamost-style config loading expects this format:

            token=your_token_here
            # Comments starting with # are supported

        Examples
        --------
        >>> # Method 1: Use the singleton instance with default settings
        >>> from astroquery.nadc.lamost import Lamost
        >>> result = Lamost.query_region(...)  # doctest: +SKIP

        >>> # Method 2: Create custom instance with specific data release
        >>> from astroquery.nadc.lamost import LamostClass
        >>> lm = LamostClass(data_release='dr10', sub_version='v2.0')  # doctest: +SKIP
        >>> result = lm.query_region(...)  # doctest: +SKIP

        >>> # Method 3: Create instance with token
        >>> lm = LamostClass(token='your_token')  # doctest: +SKIP

        >>> # Method 4: Use an environment variable such as ASTROQUERY_NADC_LAMOST_TOKEN

        >>> # Method 5: Explicitly read a pylamost.ini file
        >>> lm = LamostClass(pylamost_config='~/pylamost.ini')  # doctest: +SKIP
        """
        super().__init__()
        explicit_token = token is not None
        if token is not None:
            self.token = _strip_optional_quotes(token) or None
        else:
            self.token = (
                _strip_optional_quotes(conf.token or "")
                or _configured_token_from_env()
            )
        self.data_release = data_release or conf.data_release
        self.sub_version = sub_version or conf.sub_version

        if self.token is None and not explicit_token and pylamost_config is not None:
            self._detect_token(pylamost_config)

    def _safe_cache(self, cache, *, stream=False):
        """
        Return a cache flag safe to pass to ``BaseQuery._request``.

        Notes
        -----
        - When using authenticated requests (token provided), caching is disabled
          to avoid persisting credentials to disk via request/response caching.
        - When streaming downloads, caching is disabled to avoid pickling large
          responses and to prevent issues with partially-consumed streams.
        """
        if stream:
            return False
        if self.token:
            return False
        return cache

    def _normalize_resolution(self, resolution):
        normalized = str(resolution).strip().lower()
        if normalized not in {'low', 'medium'}:
            raise InvalidQueryError("resolution must be one of: low, medium.")
        return normalized

    def _normalize_output_format(self, output_format, *, allowed):
        normalized = str(output_format).strip().lower().lstrip('.')
        if normalized not in allowed:
            raise InvalidQueryError(
                "output_format must be one of: {0}.".format(", ".join(allowed))
            )
        return normalized

    def _request_raise(self, method, url, *, params=None, json=None,
                       timeout=None, cache=True, stream=False):
        response = self._request(
            method,
            url,
            params=params,
            json=json,
            timeout=timeout or self.TIMEOUT,
            cache=self._safe_cache(cache, stream=stream),
            stream=stream,
        )
        raise_for_status = getattr(response, 'raise_for_status', None)
        if callable(raise_for_status):
            raise_for_status()
        return response

    def _parse_table_response(self, response, *, verbose=False):
        table = self._parse_result(response, verbose=verbose)
        self.table = table
        return table

    def _normalize_tables_metadata(self, data):
        if isinstance(data, dict):
            if 'tables' in data and isinstance(data['tables'], dict):
                return data

            if 'tables' in data and isinstance(data['tables'], list):
                table_entries = data['tables']
            elif any(isinstance(value, dict) for value in data.values()):
                return {'tables': data}
            else:
                table_entries = [data]
        elif isinstance(data, list):
            table_entries = data
        else:
            raise TableParseError(
                "Expected a JSON object or list for table metadata."
            )

        tables = {}
        for entry in table_entries:
            if not isinstance(entry, dict):
                continue
            table_name = (
                entry.get('table_name')
                or entry.get('name')
                or entry.get('table')
                or entry.get('tablename')
            )
            if table_name is None:
                continue
            tables[str(table_name)] = dict(entry)

        return {'tables': tables}

    def _normalize_unique_id_result(self, data):
        if not isinstance(data, dict):
            raise TableParseError(
                "Expected a JSON object for unique-id lookup results."
            )

        normalized = dict(data)
        unique_id = normalized.get('unique_id', normalized.get('uid'))

        related_obsids = normalized.get('related_obsids')
        if related_obsids is None:
            related_obsids = []
        elif isinstance(related_obsids, (list, tuple, set)):
            related_obsids = list(related_obsids)
        else:
            related_obsids = [related_obsids]

        low_obsids = normalized.get(
            'related_obsids_low',
            normalized.get('obsid-low', normalized.get('obsid_low', [])),
        )
        medium_obsids = normalized.get(
            'related_obsids_medium',
            normalized.get('obsid-medium', normalized.get('obsid_medium', [])),
        )

        for key, value in (
            ('related_obsids_low', low_obsids),
            ('related_obsids_medium', medium_obsids),
        ):
            if isinstance(value, (list, tuple, set)):
                normalized[key] = list(value)
            elif value in (None, ''):
                normalized[key] = []
            else:
                normalized[key] = [value]

        if not related_obsids:
            merged_obsids = []
            for sequence in (
                normalized['related_obsids_low'],
                normalized['related_obsids_medium'],
            ):
                for obsid in sequence:
                    if obsid not in merged_obsids:
                        merged_obsids.append(obsid)
            related_obsids = merged_obsids

        if unique_id is not None:
            normalized['unique_id'] = unique_id
        normalized['related_obsids'] = related_obsids
        return normalized

    def _detect_token(self, config_file):
        """
        Load authentication token from an explicit pylamost-style config file.

        If the config file doesn't exist or doesn't contain a token, no error
        is raised to allow queries for public data.
        """
        config = self._get_config(config_file)
        if config and 'token' in config:
            token_value = config['token'].strip()
            if token_value:  # Only set if token is not empty
                self.token = token_value

    def _get_config(self, config_file):
        """
        Read configuration from an explicit pylamost-style config file.

        The config file format supports:
        - key=value pairs
        - Comments starting with #
        - Empty lines (ignored)

        Returns
        -------
        dict or None
            Configuration dictionary with key-value pairs, or None if file doesn't exist
            or cannot be read.

        Examples
        --------
        Example config file content:
            # LAMOST API Token
            token=your_token_here
        """
        config_file = os.path.expanduser(os.fspath(config_file))
        if not os.path.exists(config_file):
            return None

        config = {}
        try:
            with open(config_file, 'r') as fh:
                for line_num, line in enumerate(fh, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                    else:
                        # Skip malformed lines silently for compatibility
                        continue
        except Exception as e:
            # If config file cannot be read, return None to allow public data queries
            warnings.warn(
                f"Could not read config file {config_file}: {e}. "
                "Continuing without token (public data only).",
                UserWarning
            )
            return None

        return config if config else None

    def get_dr_versions(self):
        """
        Get available Data Release versions.

        Returns
        -------
        list of dict
            List of available data release versions with their metadata.
            Each dict contains:
            - dr_version: Data release main version (e.g., 'dr10', 'dr11')
            - sub_version: Sub version (e.g., 'v2.0', 'v1.0')
            - has_mrs: Whether this release has medium-resolution spectra
            - public_status: 'public' or 'internal'
            - base_url: Base URL for this release

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> versions = Lamost.get_dr_versions()  # doctest: +SKIP
        >>> for v in versions:  # doctest: +SKIP
        ...     print(f"{v['dr_version']}/{v['sub_version']}: {v['public_status']}")  # doctest: +SKIP
        """
        url = f"{self.URL.rstrip('/openapi')}/openapi/dr_versions"
        response = self._request_raise('GET', url)
        data = response.json()
        return data.get('versions', [])

    def get_unique_id_and_related_obsids(self, *, obsid=None, ra=None, dec=None, radius=None,
                                         get_query_payload=False, cache=True):
        """
        Get unique ID and related observation IDs for a target.

        This method finds all observations of the same astronomical object,
        which is useful for tracking multiple observations of the same target.

        Parameters
        ----------
        obsid : str or int, optional
            Observation ID to query. Either obsid OR (ra, dec, radius) must be provided.
        ra : float, optional
            Right ascension in degrees. Required if obsid is not provided.
        dec : float, optional
            Declination in degrees. Required if obsid is not provided.
        radius : float, optional
            Search radius in degrees. Required if obsid is not provided.
        cache : bool, optional
            If True, cache the query result. Default is True.

        Returns
        -------
        dict
            Dictionary containing normalized keys:
            - unique_id: Unique identifier for the astronomical object
            - related_obsids: Combined list of all related observation IDs
            - related_obsids_low: Related low-resolution observation IDs, if available
            - related_obsids_medium: Related medium-resolution observation IDs, if available

        Raises
        ------
        ValueError
            If neither obsid nor (ra, dec, radius) are provided.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> # Query by obsid
        >>> result = Lamost.get_unique_id_and_related_obsids(obsid='101001')  # doctest: +SKIP
        >>> print(result['unique_id'])  # doctest: +SKIP
        >>> print(result['related_obsids'])  # doctest: +SKIP

        >>> # Query by coordinates
        >>> result = Lamost.get_unique_id_and_related_obsids(  # doctest: +SKIP
        ...     ra=10.0, dec=40.0, radius=0.001  # doctest: +SKIP
        ... )  # doctest: +SKIP
        """
        if obsid is None and (ra is None or dec is None or radius is None):
            raise ValueError(
                "Either 'obsid' OR all of ('ra', 'dec', 'radius') must be provided"
            )

        request_payload = {}

        if obsid is not None:
            request_payload['obsid'] = str(obsid)

        if ra is not None:
            request_payload['ra'] = float(ra)

        if dec is not None:
            request_payload['dec'] = float(dec)

        if radius is not None:
            request_payload['radius'] = float(radius)

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        # Build URL
        url = f"{self.URL}/{self.data_release}/{self.sub_version}/get_unique_id_and_related_obsids"
        response = self._request_raise('GET', url, params=request_payload, cache=cache)
        return self._normalize_unique_id_result(response.json())

    def get_query_result_count(self, sqlid, *, ismed=None, cache=True):
        """
        Get the total count of results for a query identified by sqlid.

        This is used for managing large query results that are processed
        asynchronously on the server.

        Parameters
        ----------
        sqlid : int
            SQL query ID returned from a previous query.
        ismed : bool, optional
            Deprecated pylamost-style parameter (unused). Included for
            compatibility only.
        cache : bool, optional
            If True, cache the query result. Default is True.

        Returns
        -------
        int
            Total number of rows in the query result.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> count = Lamost.get_query_result_count(12345)  # doctest: +SKIP
        >>> print(f"Total results: {count}")  # doctest: +SKIP
        """
        request_payload = {'sqlid': int(sqlid)}

        if self.token:
            request_payload['token'] = self.token

        # Build URL
        url = f"{self.URL}/{self.data_release}/{self.sub_version}/get_query_result_count"
        response = self._request_raise('GET', url, params=request_payload, cache=cache)
        data = response.json()
        if isinstance(data, dict) and 'total' in data:
            return int(data['total'])
        return data

    def get_query_result_by_page(self, sqlid, count, *, rows=10000, page=1,
                                 output_format='json', fmt=None, cache=True):
        """
        Get a specific page of query results.

        This method is used to retrieve large query results in chunks.

        Parameters
        ----------
        sqlid : int
            SQL query ID.
        count : int
            Total number of results (from get_query_result_count).
        rows : int, optional
            Number of rows per page. Default is 10000.
        page : int, optional
            Page number (1-indexed). Default is 1.
        output_format : str, optional
            Output format: 'json', 'csv', 'votable', or 'txt'. Default is 'json'.
        fmt : str, optional
            Deprecated alias for output_format.
        cache : bool, optional
            If True, cache the query result. Default is True.

        Returns
        -------
        `~astropy.table.Table` or list
            Query results for the requested page. Returns empty list/table if
            page number exceeds total pages.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> count = Lamost.get_query_result_count(12345)  # doctest: +SKIP
        >>> page1 = Lamost.get_query_result_by_page(12345, count, rows=1000, page=1)  # doctest: +SKIP
        """
        if fmt is not None:
            output_format = fmt
        output_format = self._normalize_output_format(
            output_format,
            allowed=('json', 'csv', 'votable', 'txt'),
        )

        if page > (count // rows + (1 if count % rows else 0)):
            # Page exceeds total pages
            if output_format == 'json':
                return []
            else:
                return Table()

        # Adjust rows for last page
        if page * rows > count:
            rows = count - (page - 1) * rows

        request_payload = {
            'sqlid': int(sqlid),
            'rows': int(rows),
            'page': int(page),
            'output.fmt': output_format
        }

        if self.token:
            request_payload['token'] = self.token

        # Build URL
        url = f"{self.URL}/{self.data_release}/{self.sub_version}/get_query_result"
        response = self._request_raise('GET', url, params=request_payload, cache=cache)

        # Parse based on format
        if output_format == 'json':
            return response.json()
        else:
            return self._parse_result(response)

    def get_query_result(self, sqlid, *, output_format='json', fmt=None,
                         page_size=10000, cache=True):
        """
        Get complete query results by automatically fetching all pages.

        This is a convenience method that handles pagination automatically
        for large result sets.

        Parameters
        ----------
        sqlid : int
            SQL query ID.
        output_format : str, optional
            Output format: 'json', 'csv', 'votable', or 'txt'. Default is 'json'.
        fmt : str, optional
            Deprecated alias for output_format.
        page_size : int, optional
            Number of rows per page. Default is 10000.
        cache : bool, optional
            If True, cache the query results. Default is True.

        Returns
        -------
        `~astropy.table.Table` or list
            Complete query results.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> full_result = Lamost.get_query_result(12345)  # doctest: +SKIP
        >>> print(f"Retrieved {len(full_result)} rows")  # doctest: +SKIP
        """
        if fmt is not None:
            output_format = fmt
        output_format = self._normalize_output_format(
            output_format,
            allowed=('json', 'csv', 'votable', 'txt'),
        )

        # Get total count
        count = self.get_query_result_count(sqlid, cache=cache)

        # Calculate number of pages
        total_pages = count // page_size + (1 if count % page_size else 0)

        if output_format == 'json':
            # For JSON, accumulate list of dicts
            result = []
            for page in range(1, total_pages + 1):
                page_result = self.get_query_result_by_page(
                    sqlid, count, rows=page_size, page=page,
                    output_format=output_format, cache=cache
                )
                result.extend(page_result)
            return result
        else:
            # For table formats, stack tables
            from astropy.table import vstack
            tables = []
            for page in range(1, total_pages + 1):
                page_result = self.get_query_result_by_page(
                    sqlid, count, rows=page_size, page=page,
                    output_format=output_format, cache=cache
                )
                if len(page_result) > 0:
                    tables.append(page_result)

            if len(tables) == 0:
                return Table()
            elif len(tables) == 1:
                return tables[0]
            else:
                return vstack(tables)

    def download_query_result(self, sqlid, filename, *, output_format='csv',
                              fmt=None, page_size=10000, cache=True):
        """
        Download complete query results to a file.

        Parameters
        ----------
        sqlid : int
            SQL query ID.
        filename : str
            Path to save the results.
        output_format : str, optional
            Output format: 'csv' (default), 'json', 'votable', or 'txt'.
        fmt : str, optional
            Deprecated alias for output_format.
        page_size : int, optional
            Number of rows per page for fetching. Default is 10000.
        cache : bool, optional
            If True, cache the query results. Default is True.

        Returns
        -------
        str
            Path to the saved file.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> filepath = Lamost.download_query_result(12345, 'results.csv')  # doctest: +SKIP
        """
        import csv

        if fmt is not None:
            output_format = fmt
        output_format = self._normalize_output_format(
            output_format,
            allowed=('json', 'csv', 'votable', 'txt'),
        )

        # Get all results
        results = self.get_query_result(
            sqlid, output_format='json', page_size=page_size, cache=cache
        )

        if output_format == 'csv':
            # Write as CSV
            with open(filename, 'w', newline='') as f:
                if len(results) > 0:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
        elif output_format == 'json':
            # Write as JSON
            import json
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            # Get as table and write
            table_result = self.get_query_result(
                sqlid, output_format=output_format, page_size=page_size, cache=cache
            )
            table_result.write(filename, format=output_format, overwrite=True)

        return filename

    def get_tables_metadata(self, *, cache=True):
        """
        Get metadata for all available tables in the data release.

        This method retrieves information about the database schema, including
        table names, column names, data types, descriptions, and units.

        Parameters
        ----------
        cache : bool, optional
            If True, cache the query result. Default is True.

        Returns
        -------
        dict
            Dictionary containing metadata for all tables under ``result['tables']``.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> metadata = Lamost.get_tables_metadata()  # doctest: +SKIP
        >>> for table_name, table_info in metadata['tables'].items():  # doctest: +SKIP
        ...     print(f"Table: {table_name}")  # doctest: +SKIP
        ...     print(f"  Columns: {table_info.get('columns', [])}")  # doctest: +SKIP
        """
        request_params = {}

        if self.token:
            request_params['token'] = self.token

        # Build URL
        url = f"{self.URL}/{self.data_release}/{self.sub_version}/tables"
        response = self._request_raise('GET', url, params=request_params, cache=cache)
        return self._normalize_tables_metadata(response.json())

    def get_tap_url(self, *, cache=True):
        """
        Get the IVOA TAP (Table Access Protocol) service URL.

        This URL can be used with TAP clients for advanced queries following
        the IVOA TAP standard.

        Parameters
        ----------
        cache : bool, optional
            If True, cache the query result. Default is True.

        Returns
        -------
        dict
            Dictionary containing the TAP service URL and related information.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> tap_info = Lamost.get_tap_url()  # doctest: +SKIP
        >>> print(tap_info['tap_url'])  # doctest: +SKIP
        """
        request_params = {}

        if self.token:
            request_params['token'] = self.token

        # Build URL - TAP doesn't use resolution path
        url = f"{self.URL}/{self.data_release}/{self.sub_version}/voservice/tap_url"
        response = self._request_raise('GET', url, params=request_params, cache=cache)
        return response.json()

    def get_footprint(self, *, resolution='low', cache=True):
        """
        Get the LAMOST observation footprint image.

        This provides a visual representation of the sky coverage for
        the specified resolution.

        Parameters
        ----------
        resolution : str, optional
            Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
        cache : bool, optional
            If True, cache the image. Default is True.

        Returns
        -------
        bytes
            Footprint image data (typically PNG or JPEG format).

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> footprint_img = Lamost.get_footprint(resolution='low')  # doctest: +SKIP
        >>> # Save to file
        >>> with open('footprint.png', 'wb') as f:  # doctest: +SKIP
        ...     f.write(footprint_img)  # doctest: +SKIP
        """
        resolution = self._normalize_resolution(resolution)
        request_params = {}

        if self.token:
            request_params['token'] = self.token

        # Build URL
        url = self._build_url('footprint', resolution=resolution)
        response = self._request_raise('GET', url, params=request_params, cache=cache)
        return response.content

    def _build_url(self, endpoint, resolution='low'):
        """
        Build complete API URL for a given endpoint.

        Parameters
        ----------
        endpoint : str
            API endpoint path (e.g., 'voservice/conesearch', 'spectrum/fits')
        resolution : str, optional
            Spectral resolution: 'low' for LRS or 'medium' for MRS.
            Default is 'low'.

        Returns
        -------
        str
            Complete URL for the API request
        """
        resolution = self._normalize_resolution(resolution)
        res_path = 'mrs' if resolution == 'medium' else 'lrs'
        return f"{self.URL}/{self.data_release}/{self.sub_version}/{res_path}/{endpoint}"

    def _request_query_region(self, coordinates, radius, *,
                              resolution='low', output_format='votable', fmt=None,
                              get_query_payload=False, cache=True):
        """
        Query LAMOST catalog using cone search around given coordinates.
        """
        if fmt is not None:
            import warnings
            warnings.warn(
                "The 'fmt' parameter is deprecated. Use 'output_format' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            output_format = fmt
        resolution = self._normalize_resolution(resolution)
        output_format = self._normalize_output_format(
            output_format,
            allowed=('votable', 'json', 'csv'),
        )

        c = commons.parse_coordinates(coordinates)

        if not isinstance(radius, u.Quantity):
            radius = coord.Angle(radius)

        request_payload = {
            'ra': c.icrs.ra.deg,
            'dec': c.icrs.dec.deg,
            'sr': radius.to(u.deg).value,
            'output.fmt': output_format
        }

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        url = self._build_url('voservice/conesearch', resolution=resolution)
        return self._request_raise('GET', url, params=request_payload, cache=cache)

    def query_region(self, coordinates, radius, *,
                     resolution='low', output_format='votable', fmt=None,
                     get_query_payload=False, cache=True, verbose=False):
        """Query the LAMOST catalog around sky coordinates.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object
            Cone-search center.
        radius : str, float, or astropy.units.Quantity
            Cone-search radius.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        output_format : {"votable", "json", "csv"}, optional
            Output format requested from the service.
        fmt : str, optional
            Deprecated alias for ``output_format``.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Query result table, or request payload when
            ``get_query_payload=True``.
        """
        response = self._request_query_region(
            coordinates,
            radius,
            resolution=resolution,
            output_format=output_format,
            fmt=fmt,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_query_ssap(self, coordinates, radius, *,
                            resolution='low', output_format='votable', fmt=None,
                            get_query_payload=False, cache=True):
        """Query LAMOST using IVOA Simple Spectral Access Protocol (SSAP)."""
        if fmt is not None:
            import warnings
            warnings.warn(
                "The 'fmt' parameter is deprecated. Use 'output_format' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            output_format = fmt
        resolution = self._normalize_resolution(resolution)
        output_format = self._normalize_output_format(
            output_format,
            allowed=('votable', 'json', 'csv'),
        )

        c = commons.parse_coordinates(coordinates)

        if not isinstance(radius, u.Quantity):
            radius = coord.Angle(radius)

        request_payload = {
            'pos': f"{c.icrs.ra.deg},{c.icrs.dec.deg}",
            'size': radius.to(u.deg).value,
            'output.fmt': output_format
        }

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        url = self._build_url('voservice/ssap', resolution=resolution)
        return self._request_raise('GET', url, params=request_payload, cache=cache)

    def query_ssap(self, coordinates, radius, *,
                   resolution='low', output_format='votable', fmt=None,
                   get_query_payload=False, cache=True, verbose=False):
        """Query LAMOST with the IVOA Simple Spectral Access Protocol.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object
            Search center.
        radius : str, float, or astropy.units.Quantity
            Search radius.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        output_format : {"votable", "json", "csv"}, optional
            Output format requested from the service.
        fmt : str, optional
            Deprecated alias for ``output_format``.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            SSAP result table, or request payload when
            ``get_query_payload=True``.
        """
        response = self._request_query_ssap(
            coordinates,
            radius,
            resolution=resolution,
            output_format=output_format,
            fmt=fmt,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_query_sql(self, sql, *, output_format='json',
                           get_query_payload=False, cache=True):
        """Execute a raw SQL query on the LAMOST database."""
        output_format = self._normalize_output_format(
            output_format,
            allowed=('json', 'csv', 'votable', 'txt'),
        )
        request_payload = {
            'sql': sql,
            'output.fmt': output_format
        }

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        url = f"{self.URL}/{self.data_release}/{self.sub_version}/sql"
        return self._request_raise('GET', url, params=request_payload, cache=cache)

    def query_sql(self, sql, *, output_format='json',
                  get_query_payload=False, cache=True, verbose=False):
        """Execute a raw SQL query on the LAMOST database.

        Parameters
        ----------
        sql : str
            SQL statement accepted by the LAMOST service.
        output_format : {"json", "csv", "votable", "txt"}, optional
            Output format requested from the service.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.  For
            authenticated requests, the returned mapping separates the JSON
            body under ``"json"`` from URL query parameters under ``"params"``.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            SQL result table, or request payload when
            ``get_query_payload=True``.
        """
        response = self._request_query_sql(
            sql,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_query_catalog(self, catalog_name, *,
                               column_constraints=None,
                               position_constraints=None,
                               columns=None,
                               sort_by=None,
                               sort_order='asc',
                               max_rows=100,
                               page=1,
                               output_format='json',
                               get_query_payload=False,
                               cache=True):
        """Advanced parametric table query with constraints."""
        output_format = self._normalize_output_format(
            output_format,
            allowed=('json', 'csv', 'votable', 'txt'),
        )
        request_payload = {
            'rows': max_rows,
            'page': page,
            'output.fmt': output_format,
            'order': sort_order
        }

        if column_constraints:
            request_payload['column_constraints'] = column_constraints

        if position_constraints:
            request_payload['pos'] = position_constraints
            request_payload['pos_group'] = 'ra,dec'

        if columns:
            request_payload['showcol'] = columns

        if sort_by:
            request_payload['sort'] = sort_by

        if get_query_payload:
            if self.token:
                return {
                    'json': request_payload,
                    'params': {'token': self.token},
                }
            return request_payload

        url = f"{self.URL}/{self.data_release}/{self.sub_version}/query/{catalog_name}"
        return self._request_raise(
            'POST',
            url,
            json=request_payload,
            params={'token': self.token} if self.token else None,
            cache=cache,
        )

    def query_catalog(self, catalog_name, *,
                      column_constraints=None,
                      position_constraints=None,
                      columns=None,
                      sort_by=None,
                      sort_order='asc',
                      max_rows=100,
                      page=1,
                      output_format='json',
                      get_query_payload=False,
                      cache=True,
                      verbose=False):
        """Query a LAMOST catalog with structured constraints.

        Parameters
        ----------
        catalog_name : str
            LAMOST catalog endpoint name.
        column_constraints : list of dict, optional
            Service-format column constraints.
        position_constraints : dict, optional
            Service-format spatial constraint.
        columns : iterable of str, optional
            Columns to include in the result.
        sort_by : str, optional
            Column used for sorting.
        sort_order : {"asc", "desc"}, optional
            Sort order.
        max_rows : int, optional
            Maximum rows per page.
        page : int, optional
            One-based page number.
        output_format : {"json", "csv", "votable", "txt"}, optional
            Output format requested from the service.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Query result table, or request payload when
            ``get_query_payload=True``.
        """
        response = self._request_query_catalog(
            catalog_name,
            column_constraints=column_constraints,
            position_constraints=position_constraints,
            columns=columns,
            sort_by=sort_by,
            sort_order=sort_order,
            max_rows=max_rows,
            page=page,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _build_structured_cone_constraint(self, coordinates, radius, *, nearest_only=False):
        c = commons.parse_coordinates(coordinates)

        if isinstance(radius, u.Quantity):
            radius_arcsec = radius.to(u.arcsec).value
        else:
            radius_arcsec = float(radius)

        return {
            'cone': {
                'racenter': float(c.icrs.ra.to_value(u.deg)),
                'deccenter': float(c.icrs.dec.to_value(u.deg)),
                'radius': float(radius_arcsec),
                'cone_nearestonly': bool(nearest_only),
            },
        }

    def _spectral_catalog_name(self, resolution, catalog_name):
        if catalog_name is not None:
            return catalog_name
        resolution = self._normalize_resolution(resolution)
        return 'med_combined' if resolution == 'medium' else 'combined'

    def _spectral_column_constraints(
        self,
        *,
        snr_min=None,
        snr_column='snr',
        teff_range=None,
        logg_range=None,
        feh_range=None,
    ):
        constraints = []
        if snr_min is not None:
            if not snr_column:
                raise InvalidQueryError("snr_column must be provided when snr_min is set.")
            _append_min_constraint(constraints, snr_column, snr_min)
        _append_range_constraint(constraints, 'teff', teff_range)
        _append_range_constraint(constraints, 'logg', logg_range)
        _append_range_constraint(constraints, 'feh', feh_range)
        return [constraint.to_dict() for constraint in constraints] or None

    def query_spectra(
        self,
        coordinates=None,
        radius=None,
        *,
        resolution='low',
        catalog_name=None,
        snr_min=None,
        snr_column='snr',
        teff_range=None,
        logg_range=None,
        feh_range=None,
        columns=None,
        nearest_only=False,
        sort_by=None,
        sort_order='asc',
        max_rows=100,
        page=1,
        output_format='json',
        get_query_payload=False,
        cache=True,
        verbose=False,
    ):
        """Query LAMOST spectral catalog rows with common quality filters.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        resolution : {"low", "medium"}, optional
            Spectral-resolution catalog family.
        catalog_name : str, optional
            Explicit catalog name overriding ``resolution``.
        snr_min : float, optional
            Minimum signal-to-noise ratio.
        snr_column : str, optional
            Column used for the SNR filter.
        teff_range, logg_range, feh_range : sequence of float, optional
            Inclusive stellar-parameter ranges.
        columns : iterable of str, optional
            Columns to include in the result.
        nearest_only : bool, optional
            Return only the nearest match for spatial queries.
        sort_by : str, optional
            Column used for sorting.
        sort_order : {"asc", "desc"}, optional
            Sort order.
        max_rows : int, optional
            Maximum rows per page.
        page : int, optional
            One-based page number.
        output_format : {"json", "csv", "votable", "txt"}, optional
            Output format requested from the service.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Query result table, or request payload when
            ``get_query_payload=True``.
        """
        if (coordinates is None) ^ (radius is None):
            raise InvalidQueryError("coordinates and radius must be provided together.")

        position_constraints = None
        if coordinates is not None:
            position_constraints = self._build_structured_cone_constraint(
                coordinates,
                radius,
                nearest_only=nearest_only,
            )

        return self.query_catalog(
            self._spectral_catalog_name(resolution, catalog_name),
            column_constraints=self._spectral_column_constraints(
                snr_min=snr_min,
                snr_column=snr_column,
                teff_range=teff_range,
                logg_range=logg_range,
                feh_range=feh_range,
            ),
            position_constraints=position_constraints,
            columns=columns,
            sort_by=sort_by,
            sort_order=sort_order,
            max_rows=max_rows,
            page=page,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_stellar_parameters(
        self,
        coordinates=None,
        radius=None,
        *,
        resolution='low',
        catalog_name=None,
        snr_min=None,
        snr_column='snr',
        teff_range=None,
        logg_range=None,
        feh_range=None,
        columns=None,
        nearest_only=False,
        sort_by=None,
        sort_order='asc',
        max_rows=100,
        page=1,
        output_format='json',
        get_query_payload=False,
        cache=True,
        verbose=False,
    ):
        """Query LAMOST rows focused on stellar atmospheric parameters.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        resolution : {"low", "medium"}, optional
            Spectral-resolution catalog family.
        catalog_name : str, optional
            Explicit catalog name overriding ``resolution``.
        snr_min : float, optional
            Minimum signal-to-noise ratio.
        snr_column : str, optional
            Column used for the SNR filter and included by default.
        teff_range, logg_range, feh_range : sequence of float, optional
            Inclusive stellar-parameter ranges.
        columns : iterable of str, optional
            Columns to include in the result. Defaults to core stellar
            atmospheric-parameter columns.
        nearest_only : bool, optional
            Return only the nearest match for spatial queries.
        sort_by : str, optional
            Column used for sorting.
        sort_order : {"asc", "desc"}, optional
            Sort order.
        max_rows : int, optional
            Maximum rows per page.
        page : int, optional
            One-based page number.
        output_format : {"json", "csv", "votable", "txt"}, optional
            Output format requested from the service.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Query result table, or request payload when
            ``get_query_payload=True``.
        """
        if columns is None:
            columns = ['obsid', 'ra', 'dec', 'teff', 'logg', 'feh']
            if snr_column:
                columns = [*columns, snr_column]

        return self.query_spectra(
            coordinates=coordinates,
            radius=radius,
            resolution=resolution,
            catalog_name=catalog_name,
            snr_min=snr_min,
            snr_column=snr_column,
            teff_range=teff_range,
            logg_range=logg_range,
            feh_range=feh_range,
            columns=columns,
            nearest_only=nearest_only,
            sort_by=sort_by,
            sort_order=sort_order,
            max_rows=max_rows,
            page=page,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_repeat_observations(
        self,
        *,
        obsid=None,
        coordinates=None,
        radius=None,
        ra=None,
        dec=None,
        get_query_payload=False,
        cache=True,
    ):
        """Query related LAMOST observation IDs for one target.

        Parameters
        ----------
        obsid : str or int, optional
            Observation ID to resolve.
        coordinates : str or astropy.coordinates object, optional
            Target position. Mutually exclusive with ``ra`` and ``dec``.
        radius : float or astropy.units.Quantity, optional
            Search radius in degrees, or a quantity convertible to degrees.
        ra, dec : float, optional
            Target coordinates in degrees.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.

        Returns
        -------
        dict
            Related-observation payload, or request payload when
            ``get_query_payload=True``.
        """
        has_coordinate_values = coordinates is not None or ra is not None or dec is not None or radius is not None
        if obsid is not None and has_coordinate_values:
            raise InvalidQueryError("Provide either obsid or coordinates/radius, not both.")

        if coordinates is not None:
            if ra is not None or dec is not None:
                raise InvalidQueryError("Use coordinates or ra/dec, not both.")
            c = commons.parse_coordinates(coordinates)
            ra = float(c.icrs.ra.to_value(u.deg))
            dec = float(c.icrs.dec.to_value(u.deg))

        if isinstance(radius, u.Quantity):
            radius = radius.to(u.deg).value

        return self.get_unique_id_and_related_obsids(
            obsid=obsid,
            ra=ra,
            dec=dec,
            radius=radius,
            get_query_payload=get_query_payload,
            cache=cache,
        )

    def _request_metadata(self, obsid, *,
                          resolution='low', get_query_payload=False, cache=True):
        """Get metadata/information for a specific spectrum."""
        resolution = self._normalize_resolution(resolution)
        request_payload = {'obsid': str(obsid)}

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        url = self._build_url('spectrum/info', resolution=resolution)
        return self._request_raise('GET', url, params=request_payload, cache=cache)

    def get_metadata(self, obsid, *, resolution='low',
                     get_query_payload=False, cache=True, verbose=False):
        """Get metadata for a specific LAMOST spectrum.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Metadata table, or request payload when
            ``get_query_payload=True``.
        """
        response = self._request_metadata(
            obsid,
            resolution=resolution,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    # Data download methods following NED's image pattern
    def get_spectra(self, obsid, *, resolution='low', get_query_payload=False):
        """Download spectrum FITS data for an observation ID.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        get_query_payload : bool, optional
            Return the download URL list instead of fetching files.

        Returns
        -------
        list
            FITS objects, or download URLs when ``get_query_payload=True``.
        """
        readable_objs = self._get_spectrum_handles(
            obsid,
            resolution=resolution,
            get_query_payload=get_query_payload,
        )
        if get_query_payload:
            return readable_objs

        return [obj.get_fits() for obj in readable_objs]

    def _get_spectrum_handles(self, obsid, *, resolution='low', get_query_payload=False):
        """Get handles to spectrum FITS files for lazy download."""
        url_list = self.get_spectrum_list(obsid, resolution=resolution,
                                          get_query_payload=get_query_payload)
        if get_query_payload:
            return url_list

        file_cache = self._safe_cache(True)
        return [
            commons.FileContainer(url, encoding='binary', show_progress=True, cache=file_cache)
            for url in url_list
        ]

    def get_spectrum_list(self, obsid, *, resolution='low', get_query_payload=False):
        """
        Get list of spectrum FITS file URLs without downloading.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : str, optional
            Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
        get_query_payload : bool, optional
            If True, return the request parameters dict without executing the query.

        Returns
        -------
        list of str
            List of FITS file URLs.
        """
        resolution = self._normalize_resolution(resolution)
        request_payload = {'obsid': str(obsid)}

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        # Build URL for FITS download
        from urllib.parse import urlencode
        base_url = self._build_url('spectrum/fits', resolution=resolution)
        url = f"{base_url}?{urlencode(request_payload)}"

        # Return as single-item list for consistency with get_images pattern
        return [url]

    def get_fits_csv(self, obsid, *, resolution='low', ismed=None, cache=True):
        """
        Get spectrum data in CSV format.

        This method retrieves the spectrum data as CSV text, which is useful
        for quick preview and data processing without downloading FITS files.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : str, optional
            Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
        ismed : bool, optional
            Deprecated pylamost-style resolution flag. If True, uses MRS.
        cache : bool, optional
            If True, cache the query result. Default is True.

        Returns
        -------
        str
            CSV-formatted spectrum data as text.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> csv_data = Lamost.get_fits_csv('101001', resolution='low')  # doctest: +SKIP
        >>> print(csv_data[:100])  # doctest: +SKIP
        """
        if ismed is not None:
            resolution = 'medium' if ismed else 'low'
        resolution = self._normalize_resolution(resolution)

        request_payload = {'obsid': str(obsid)}

        if self.token:
            request_payload['token'] = self.token

        # Build URL for CSV export
        url = self._build_url('spectrum/fits2csv', resolution=resolution)
        response = self._request_raise('GET', url, params=request_payload, cache=cache)
        return response.text

    def get_images(self, obsid, *, resolution='low', get_query_payload=False):
        """Download spectrum PNG images for an observation ID.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        get_query_payload : bool, optional
            Return the download URL list instead of fetching files.

        Returns
        -------
        list
            PNG image bytes, or download URLs when
            ``get_query_payload=True``.
        """
        readable_objs = self._get_image_handles(
            obsid,
            resolution=resolution,
            get_query_payload=get_query_payload,
        )
        if get_query_payload:
            return readable_objs

        return [obj.get_string() for obj in readable_objs]

    def _get_image_handles(self, obsid, *, resolution='low', get_query_payload=False):
        """Get handles to spectrum PNG images for lazy download."""
        url_list = self.get_image_list(obsid, resolution=resolution,
                                       get_query_payload=get_query_payload)
        if get_query_payload:
            return url_list

        file_cache = self._safe_cache(True)
        return [
            commons.FileContainer(url, encoding='binary', show_progress=True, cache=file_cache)
            for url in url_list
        ]

    def get_image_list(self, obsid, *, resolution='low', get_query_payload=False):
        """
        Get list of spectrum PNG image URLs without downloading.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : str, optional
            Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
        get_query_payload : bool, optional
            If True, return the request parameters dict without executing the query.

        Returns
        -------
        list of str
            List of PNG image URLs.
        """
        resolution = self._normalize_resolution(resolution)
        request_payload = {'obsid': str(obsid)}

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return request_payload

        # Build URL for PNG download
        from urllib.parse import urlencode
        base_url = self._build_url('spectrum/png', resolution=resolution)
        url = f"{base_url}?{urlencode(request_payload)}"

        # Return as single-item list
        return [url]

    def _resolve_download_path(self, response, save_dir, filename, default_name):
        import os
        import re

        if filename:
            if os.path.isabs(filename):
                return filename
            return os.path.join(save_dir, filename)

        content_disp = response.headers.get('Content-Disposition', '')
        filename_match = re.search(r'filename=([^;]+)', content_disp, re.IGNORECASE)
        if filename_match:
            resolved = filename_match.group(1).strip(' "\'')
            resolved = os.path.basename(resolved)
        else:
            resolved = default_name

        return os.path.join(save_dir, resolved)

    def download_catalog(self, catalog_name, *, resolution='low',
                         save_dir='./', savedir=None, ismed=None,
                         filename=None, overwrite=True, cache=True):
        """
        Download complete catalog FITS.GZ file.

        Parameters
        ----------
        catalog_name : str
            Name of the catalog to download.
        resolution : str, optional
            Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
        save_dir : str, optional
            Directory to save the downloaded file. Default is current directory.
        savedir : str, optional
            Deprecated alias for save_dir.
        ismed : bool, optional
            Deprecated pylamost-style resolution flag. If True, uses MRS.
        filename : str, optional
            Override the output filename. Relative paths are resolved against
            save_dir. If None, use server-provided filename and fall back to
            "{catalog_name}.fits.gz".
        overwrite : bool, optional
            If True, overwrite existing file. Default is True.
        cache : bool, optional
            If True, cache the download. Default is True.

        Returns
        -------
        str
            Path to the downloaded catalog file.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> filepath = Lamost.download_catalog('catalog_v1', resolution='low')  # doctest: +SKIP
        """
        if savedir is not None:
            save_dir = savedir

        if ismed is not None:
            resolution = 'medium' if ismed else 'low'
        resolution = self._normalize_resolution(resolution)

        request_params = {'name': catalog_name}

        if self.token:
            request_params['token'] = self.token

        # Build URL
        url = self._build_url('catalog', resolution=resolution)

        # Download file
        response = self._request_raise(
            'GET',
            url,
            params=request_params,
            cache=cache,
            stream=True,
        )

        # Save to disk
        import os
        filepath = self._resolve_download_path(
            response,
            save_dir,
            filename,
            f"{catalog_name}.fits.gz"
        )

        os.makedirs(os.path.dirname(filepath) or save_dir, exist_ok=True)

        if os.path.exists(filepath) and not overwrite:
            return filepath

        # Write with temp file for atomic operation
        temp_filepath = filepath + '.temp'
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Rename to final filename
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(temp_filepath, filepath)

        return filepath

    def _parse_result(self, response, *, verbose=False):
        """
        Parse response into an astropy Table based on content type.

        Supports votable, json, csv, and txt formats based on Content-Type header.

        Parameters
        ----------
        response : `requests.Response`
            HTTP response from query.
        verbose : bool, optional
            If False, suppress VOTable warnings. Default is False.

        Returns
        -------
        table : `~astropy.table.Table`
            Parsed table from the response.
        """
        content_type = response.headers.get('Content-Type', '').lower()

        # Determine format from Content-Type header
        if 'json' in content_type:
            return self._parse_json_result(response)
        elif 'csv' in content_type:
            return self._parse_csv_result(response)
        elif 'votable' in content_type or 'xml' in content_type:
            return self._parse_votable_result(response, verbose=verbose)
        elif 'text/plain' in content_type:
            return self._parse_txt_result(response)
        else:
            # Default to votable for backward compatibility
            return self._parse_votable_result(response, verbose=verbose)

    def _parse_votable_result(self, response, *, verbose=False):
        """
        Parse VOTable response into an astropy Table.

        Parameters
        ----------
        response : `requests.Response`
            HTTP response from query.
        verbose : bool, optional
            If False, suppress VOTable warnings. Default is False.

        Returns
        -------
        table : `~astropy.table.Table`
            Parsed table from the response.
        """
        if not verbose:
            commons.suppress_vo_warnings()

        try:
            if response_looks_like_html(response):
                raise TableParseError(
                    "Server returned HTML instead of a table response; check authentication or upstream errors."
                )

            content = sanitize_votable_content(
                response.content,
                fix_invalid_date=True,
                fix_missing_field_datatype=True,
                fix_empty_arraysize=True,
            )
            tf = BytesIO(content)
            votable_file = votable.parse(tf, verify='warn')
            first_table = votable_file.get_first_table()
            table = first_table.to_table(use_names_over_ids=True)
            return table
        except Exception as ex:
            # Store response for debugging
            self.response = response
            self.table_parse_error = ex
            raise TableParseError(
                f"Failed to parse response as VOTable: {str(ex)}"
            )

    def _parse_json_result(self, response):
        """
        Parse JSON response into an astropy Table.

        Parameters
        ----------
        response : `requests.Response`
            HTTP response from query with JSON content.

        Returns
        -------
        table : `~astropy.table.Table`
            Parsed table from the JSON response.
        """
        try:
            data = response.json()

            # Handle different JSON structures
            if isinstance(data, list):
                # List of dictionaries
                if len(data) == 0:
                    return Table()
                return Table(data)
            elif isinstance(data, dict):
                # Single result or structured response
                if 'data' in data:
                    # Structured response with 'data' field
                    return Table(data['data'])
                else:
                    # Single result
                    return Table([data])
            else:
                raise ValueError(f"Unexpected JSON structure: {type(data)}")

        except Exception as ex:
            self.response = response
            self.json_parse_error = ex
            raise TableParseError(
                f"Failed to parse response as JSON: {str(ex)}"
            )

    def _parse_csv_result(self, response):
        """
        Parse CSV response into an astropy Table.

        Parameters
        ----------
        response : `requests.Response`
            HTTP response from query with CSV content.

        Returns
        -------
        table : `~astropy.table.Table`
            Parsed table from the CSV response.
        """
        try:
            from io import BytesIO
            # Strip UTF-8 BOM if present to ensure consistent behavior across platforms
            content = response.content
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
            return Table.read(BytesIO(content), format='csv')
        except Exception as ex:
            self.response = response
            raise TableParseError(
                f"Failed to parse response as CSV: {str(ex)}"
            )

    def _parse_txt_result(self, response):
        """
        Parse plain text response into an astropy Table.

        Parameters
        ----------
        response : `requests.Response`
            HTTP response from query with plain text content.

        Returns
        -------
        table : `~astropy.table.Table`
            Parsed table from the text response.
        """
        try:
            from io import BytesIO
            # Use BytesIO with response.content (bytes) for consistency with CSV parser
            return Table.read(BytesIO(response.content), format='ascii')
        except Exception as ex:
            self.response = response
            raise TableParseError(
                f"Failed to parse response as plain text: {str(ex)}"
            )


# Singleton instance for module-level access
Lamost: LamostClass = LamostClass()


# Utility functions for FITS spectrum processing

def parse_lrs_spectrum(filename):
    """
    Parse a low-resolution spectrum (LRS) FITS file.

    This function reads a LAMOST low-resolution spectrum FITS file and extracts
    wavelength, flux, and smoothed flux data.

    Parameters
    ----------
    filename : str
        Path to the LRS FITS file.

    Returns
    -------
    wavelength : `~numpy.ndarray`
        Wavelength array in Angstroms.
    flux : `~numpy.ndarray`
        Spectrum flux array.
    flux_smooth_7 : `~numpy.ndarray`
        Median-filtered flux with window size 7.
    flux_smooth_15 : `~numpy.ndarray`
        Median-filtered flux with window size 15.

    Examples
    --------
    >>> wavelength, flux, smooth7, smooth15 = parse_lrs_spectrum('spec.fits')  # doctest: +SKIP
    """
    hdulist = fits.open(filename)
    num_extensions = len(hdulist)

    if num_extensions == 1:
        # Old format: single extension with header keywords
        header = hdulist[0].header
        scidata = hdulist[0].data

        coeff0 = header['COEFF0']
        coeff1 = header['COEFF1']
        pixel_num = header['NAXIS1']

        flux = scidata[0, :].astype(np.float32)

        # Generate wavelength from coefficients
        wavelength = np.linspace(0, pixel_num - 1, pixel_num)
        wavelength = np.power(10, (coeff0 + wavelength * coeff1))

    elif num_extensions == 2:
        # New format: data in second extension
        scidata = hdulist[1].data
        wavelength = scidata[0][2]
        flux = scidata[0][0].astype(np.float32)

    hdulist.close()

    # Apply median filtering for smoothing
    flux_smooth_7 = _median_filter_1d_zero_padded(flux, 7)
    flux_smooth_15 = _median_filter_1d_zero_padded(flux, 15)

    return wavelength, flux, flux_smooth_7, flux_smooth_15


def parse_mrs_spectrum(filename):
    """
    Parse a medium-resolution spectrum (MRS) FITS file.

    This function reads a LAMOST medium-resolution spectrum FITS file which
    contains multiple spectral bands in separate extensions.

    Parameters
    ----------
    filename : str
        Path to the MRS FITS file.

    Returns
    -------
    data : dict
        Dictionary with extension names as keys, each containing:
        - 'wavelength': wavelength array in Angstroms
        - 'flux': spectrum flux array

    Examples
    --------
    >>> data = parse_mrs_spectrum('spec_mrs.fits')  # doctest: +SKIP
    >>> for band_name, band_data in data.items():  # doctest: +SKIP
    ...     print(f"{band_name}: {len(band_data['wavelength'])} pixels")  # doctest: +SKIP
    """
    hdulist = fits.open(filename)
    num_extensions = len(hdulist)

    data = {}
    for i in range(1, num_extensions):
        header = hdulist[i].header
        scidata = hdulist[i].data

        flux = scidata[0][0]
        wavelength = scidata[0][2]

        extension_name = header.get('EXTNAME', f'Extension_{i}')
        data[extension_name] = {
            'wavelength': wavelength,
            'flux': flux
        }

    hdulist.close()
    return data


def plot_spectrum(filename, resolution='low', show=True, **kwargs):
    """
    Plot a LAMOST spectrum from a FITS file.

    Parameters
    ----------
    filename : str
        Path to the FITS file.
    resolution : str, optional
        Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
    show : bool, optional
        If True (default), display the plot. If False, return the figure object.
    **kwargs
        Additional keyword arguments passed to matplotlib.pyplot.plot().

    Returns
    -------
    fig : `~matplotlib.figure.Figure`
        Matplotlib figure object (if ``show`` is False).

    Examples
    --------
    >>> plot_spectrum('spec.fits', resolution='low')  # doctest: +SKIP
    >>> plot_spectrum('spec_mrs.fits', resolution='medium', show=False)  # doctest: +SKIP
    """
    import matplotlib.pyplot as plt

    resolution = str(resolution).strip().lower()
    if resolution not in {'low', 'medium'}:
        raise InvalidQueryError("resolution must be one of: low, medium.")

    fig = plt.figure(figsize=(18.5, 6.5))

    if resolution == 'low':
        # Parse and plot LRS
        wavelength, flux, _, _ = parse_lrs_spectrum(filename)
        plt.plot(wavelength, flux, **kwargs)

    elif resolution == 'medium':
        # Parse and plot all MRS bands
        data = parse_mrs_spectrum(filename)
        for band_name, band_data in data.items():
            plt.plot(band_data['wavelength'], band_data['flux'],
                     label=band_name, **kwargs)
        if len(data) > 1:
            plt.legend()

    plt.xlabel('Wavelength [Ångströms]')
    plt.ylabel('Flux')
    plt.title(f'LAMOST Spectrum: {filename}')

    if show:
        plt.show()
        return None
    else:
        return fig
