# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LAMOST Spectroscopic Survey Query Tool
=======================================

This module provides the core implementation for querying LAMOST data.
"""

# Standard library
from collections.abc import Mapping
from copy import copy
import csv
import gzip
import os
import re
import tempfile
import warnings
from io import BytesIO, StringIO
from numbers import Integral
from urllib.parse import quote, quote_plus, urlencode
from xml.etree import ElementTree

# Third party
import astropy.units as u
import astropy.coordinates as coord
from astropy.io import ascii, fits, votable
from astropy.io.votable.exceptions import W46
from astropy.table import MaskedColumn, Table
import numpy as np
from requests import HTTPError, Response
from requests.structures import CaseInsensitiveDict

# Local imports
from ._response_utils import response_looks_like_html, sanitize_votable_content
from ._sql import EARLY_MRS, MODERN_CATALOGS, catalog_sql, spectral_catalog, uses_legacy_metadata
from ._utils import (
    _append_min_constraint,
    _append_range_constraint,
    _api_error_summary,
    _configured_token_from_env as _configured_token_from_env_base,
    _oauth_redirect_url,
    _strip_optional_quotes,
    _successful_response_error,
)
from ...query import BaseQuery
from ... import log
from ...utils import commons
from ...exceptions import InputWarning, InvalidQueryError, LoginError, RemoteServiceError, TableParseError
from . import conf


__all__ = ['Lamost', 'LamostClass',
           'parse_lrs_spectrum', 'parse_mrs_spectrum']


_TOKEN_ENV_VARS = (
    "ASTROQUERY_LAMOST_TOKEN",
    "ASTROQUERY_NADC_LAMOST_TOKEN",
    "NADC_LAMOST_TOKEN",
    "CHINAVO_LAMOST_TOKEN",
    "ASTROQUERY_LAMOST_ACCESS_TOKEN",
    "ASTROQUERY_NADC_LAMOST_ACCESS_TOKEN",
    "NADC_LAMOST_ACCESS_TOKEN",
    "CHINAVO_LAMOST_ACCESS_TOKEN",
)


_SPECTRAL_FIELDS = {
    'low': {
        'snr': 'snrg',
        'teff': 'teff',
        'logg': 'logg',
        'feh': 'feh',
    },
    'medium': {
        'snr': 'snr',
        'teff': 'teff_lasp',
        'logg': 'logg_lasp',
        'feh': 'feh_lasp',
    },
}

_SCHEMA_COLUMN_KEYS = ('column_name', 'colname', 'column', 'name')
_SCHEMA_DATATYPE_KEYS = ('datatype', 'data_type', 'type', 'dbtype', 'dtype')
_SCHEMA_UNIT_KEYS = ('unit', 'units')


def _configured_token_from_env():
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


def _table_response_text(response):
    """Decode table text without ever interpreting an empty body as a path."""
    text = response.content.decode('utf-8-sig')
    if not text.strip():
        raise TableParseError(
            "LAMOST returned an empty response body, not a valid table. "
            "A zero-row text result must still contain a column header."
        )
    return text


def _csv_delimiter(text):
    """Use only unquoted delimiters in the header to recognize legacy pipes."""
    delimiters = set()
    quoted = False
    for character in text.lstrip():
        if character == '"':
            quoted = not quoted
        elif not quoted:
            if character in '\r\n':
                break
            if character in ',|':
                delimiters.add(character)
    if len(delimiters) > 1:
        raise ValueError("Ambiguous table header: both comma and pipe delimiters occur outside quotes.")
    return delimiters.pop() if delimiters else ','


class _CsvData(ascii.Csv.data_class):
    def process_lines(self, lines):
        # Inputs are complete CSV records. Whitespace-only records can be data;
        # physical blank lines inside quoted fields must never be filtered out.
        return lines


class _CsvInputter(ascii.BaseInputter):
    def get_lines(self, table, newline=None):
        # Even a single header record may contain quoted newlines. BaseInputter
        # would split that record again instead of preserving the logical record.
        return table


class _CsvReader(ascii.Csv):
    data_class = _CsvData
    inputter_class = _CsvInputter


class LamostClass(BaseQuery):
    """
    Class for querying the LAMOST spectroscopic survey database.

    The LAMOST (Large Sky Area Multi-Object Fiber Spectroscopic Telescope)
    survey provides spectroscopic data for millions of stars and galaxies.
    This class provides methods to query the catalog, download spectra,
    and access metadata.

    Notes
    -----
    Configuration is read when an instance is created, including the
    module-level ``Lamost`` instance at import time. Changing ``conf`` does
    not update existing instances. Create a new `LamostClass` to apply it.
    Authenticated requests and streaming downloads bypass the disk cache.
    ``get_query_payload=True`` returns parameters with credentials redacted.

    Recognized authentication failures raise `~astroquery.exceptions.LoginError`.
    Other HTTP failures raise `requests.HTTPError`, service error payloads
    raise `~astroquery.exceptions.RemoteServiceError`, and malformed tables
    raise `~astroquery.exceptions.TableParseError`. Diagnostics retain
    available error details with credentials redacted.
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
            An explicit empty string forces anonymous access.
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
        Explicit pylamost-style config loading expects this format::

            token=your_token_here
            # Comments starting with # are supported

        Examples
        --------
        >>> from astroquery.nadc.lamost import LamostClass
        >>> lm = LamostClass(token='', data_release='dr10', sub_version='v2.0')
        >>> lm = LamostClass(pylamost_config='~/pylamost.ini')  # doctest: +SKIP
        """
        super().__init__()
        self.URL = conf.server.rstrip('/')
        self.TIMEOUT = conf.timeout
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

    def _redact(self, value):
        """Copy diagnostic values without authentication credentials."""
        if isinstance(value, Mapping):
            return {
                key: '<redacted>' if str(key).lower() in {
                    'token', 'access_token', 'authorization', 'cookie', 'set-cookie',
                } else self._redact(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return type(value)(self._redact(item) for item in value)
        if isinstance(value, bytes):
            return self._redact(value.decode('utf-8', 'replace')).encode('utf-8')
        if not isinstance(value, str):
            return value
        if self.token:
            for secret in {self.token, quote(self.token, safe=''), quote_plus(self.token)}:
                value = value.replace(secret, '<redacted>')
        return re.sub(
            r'''(?i)(\b(?:access_)?token["']?\s*[:=]\s*["']?)[^&\s"'<>]+''',
            r'\1<redacted>', value,
        )

    def _diagnostic_request(self, request):
        if request is None:
            return None
        sanitized = copy(request)
        sanitized.url = self._redact(request.url)
        sanitized.headers = CaseInsensitiveDict(self._redact(request.headers))
        sanitized.body = self._redact(request.body)
        sanitized._cookies = None
        return sanitized

    def _diagnostic_response(self, response):
        """Keep a safe response for parser diagnostics, without a live stream."""
        # copy(response) consumes streaming bodies through Response.__getstate__.
        # Redirect histories can also contain the response itself.
        sanitized = Response()
        sanitized.status_code = response.status_code
        sanitized.encoding = response.encoding
        sanitized.reason = self._redact(response.reason)
        sanitized.url = self._redact(getattr(response, 'url', None))
        sanitized.headers = CaseInsensitiveDict(self._redact(response.headers))
        sanitized.request = self._diagnostic_request(getattr(response, 'request', None))
        content = getattr(response, '_content', None)
        if isinstance(content, bytes):
            sanitized._content = self._redact(content)
            sanitized._content_consumed = True
        return sanitized

    def _sanitize_exception(self, error):
        """Redact attached requests and the accessible exception chain."""
        pending, seen = [error], set()
        while pending:
            current = pending.pop()
            if id(current) in seen:
                continue
            seen.add(id(current))
            current.args = tuple(self._redact(str(arg)) for arg in current.args)
            for name in ('url', 'filename', 'filename2', 'doc', 'msg', 'reason'):
                value = getattr(current, name, None)
                if isinstance(value, (str, Exception)):
                    setattr(current, name, self._redact(str(value)))
            if getattr(current, 'request', None) is not None:
                current.request = self._diagnostic_request(current.request)
            if getattr(current, 'response', None) is not None:
                current.response = self._diagnostic_response(current.response)
            pending.extend(item for item in (current.__cause__, current.__context__) if item is not None)

    def _response_hook(self, response, *args, **kwargs):
        # BaseQuery's hook logs raw URLs, headers and bodies, including tokens.
        log.debug('LAMOST HTTP %s %s: %s', response.request.method,
                  self._redact(response.request.url), response.status_code)

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
        response = None
        try:
            response = self._request(
                method,
                url,
                params=params,
                json=json,
                timeout=timeout or self.TIMEOUT,
                cache=self._safe_cache(cache, stream=stream),
                stream=stream,
            )
            context = f"LAMOST {method} {self._redact(url)} (HTTP {response.status_code})"
            self._raise_response_error(response, context, stream=stream)

            try:
                response.raise_for_status()
            except HTTPError as error:
                detail = _api_error_summary(response) or str(error)
                error.args = (f"{context}: {self._redact(detail)}",)
                raise

            return response
        except Exception as error:
            if response is None:
                response = getattr(error, 'response', None)
            if response is not None:
                self.response = self._diagnostic_response(response)
                response.close()
            self._sanitize_exception(error)
            raise

    def _raise_response_error(self, response, context, *, stream=False):
        oauth_redirect = _oauth_redirect_url(response, include_body=not stream)
        error = _successful_response_error(response) if not stream and response.status_code < 400 else None
        if (oauth_redirect is not None or response.status_code in (401, 403) or error and (
                re.match(r'(?i)^(401|403|unauthorized|unauthenticated|invalid token|expired token)(:|$)', error)
                or 'check your token' in error.lower())):
            detail = ('the service redirected to an OAuth login page' if oauth_redirect is not None
                      else error or _api_error_summary(response) or 'authentication required')
            advice = ('Check the supplied token validity, expiration and access permissions.' if self.token else
                      'Pass a token to LamostClass(token=...), or set conf.token / '
                      'ASTROQUERY_NADC_LAMOST_TOKEN before creating a new instance.')
            raise LoginError(f'{context}: Authentication failed: {self._redact(detail)}. {advice}')
        if error:
            raise RemoteServiceError(f'{context}: {self._redact(error)}')

    @staticmethod
    def _radius_in(radius, unit):
        try:
            angle = coord.Angle(radius, unit=unit)
            value = angle.to_value(unit)
            if not angle.isscalar or not np.isfinite(value) or value <= 0:
                raise ValueError
        except (TypeError, ValueError, u.UnitsError) as error:
            raise InvalidQueryError(
                f"radius must be a finite positive scalar angle; bare numbers are in {unit}."
            ) from error
        return float(value)

    @staticmethod
    def _page_integer(value, name, *, minimum=1):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < minimum:
            raise InvalidQueryError(f"{name} must be an integer >= {minimum}.")
        return int(value)

    def _parse_table_response(self, response, *, verbose=False, column_schema=None, empty_columns=None):
        table = self._parse_result(response, verbose=verbose, column_schema=column_schema,
                                   empty_columns=empty_columns)
        self.table = table
        return table

    def _response_json(self, response):
        self._validate_data_response(response)
        try:
            return response.json()
        except ValueError as error:
            self.response = self._diagnostic_response(response)
            self._sanitize_exception(error)
            raise TableParseError(f"Failed to parse LAMOST JSON response: {error}") from error

    def _validate_data_response(self, response):
        """Reject empty bodies and HTML before interpreting table or metadata formats."""
        if not response.content.removeprefix(b'\xef\xbb\xbf').strip():
            message = (
                "LAMOST returned an empty response body, not a valid table or metadata response. "
                "A zero-row text result must still contain a column header."
            )
        elif response_looks_like_html(response):
            message = (
                "Server returned HTML instead of a table response; "
                "check authentication or upstream errors."
            )
        else:
            return

        diagnostic = self.response = self._diagnostic_response(response)
        raise TableParseError(
            f"{message} HTTP {diagnostic.status_code}; URL: {diagnostic.url}; "
            f"Content-Type: {diagnostic.headers.get('Content-Type', 'unknown')}; "
            f"body: {len(response.content)} bytes."
        )

    def _normalize_tables_metadata(self, data):
        if isinstance(data, dict):
            if 'tables' in data and isinstance(data['tables'], dict):
                return data

            if 'tables' in data and isinstance(data['tables'], list):
                table_entries = data['tables']
            elif 'columns' in data:
                # One table description, not a mapping of table names.
                table_entries = [data]
            elif any(isinstance(value, dict) for value in data.values()):
                return {'tables': {str(name): value for name, value in data.items()
                                   if isinstance(value, dict)}}
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

    @staticmethod
    def _schema_value(metadata, keys):
        if not isinstance(metadata, Mapping):
            return None
        for key in keys:
            value = metadata.get(key)
            if value not in (None, ''):
                return value
        return None

    def _catalog_schema(self, catalog_name, *, cache=True):
        metadata = self.get_tables_metadata(cache=cache)
        tables = metadata.get('tables', {})
        if catalog_name not in tables:
            raise InvalidQueryError(f"Unknown LAMOST catalog: {catalog_name!r}.")

        table_metadata = tables[catalog_name]
        if not isinstance(table_metadata, Mapping):
            raise TableParseError(
                f"Metadata for LAMOST catalog {catalog_name!r} is not an object."
            )

        schema = self._columns_schema(table_metadata.get('columns'))
        if not schema:
            raise TableParseError(
                f"Metadata for LAMOST catalog {catalog_name!r} did not contain columns."
            )
        return schema

    def _legacy_metadata(self):
        return uses_legacy_metadata(self.data_release, self.sub_version)

    def _columns_schema(self, columns):
        schema = {}
        if isinstance(columns, Mapping):
            for name, column_metadata in columns.items():
                if isinstance(column_metadata, Mapping):
                    schema[str(name)] = dict(column_metadata)
                else:
                    schema[str(name)] = {'datatype': column_metadata}
        elif isinstance(columns, (list, tuple)):
            for column_metadata in columns:
                if isinstance(column_metadata, str):
                    schema[column_metadata] = {}
                    continue
                name = self._schema_value(column_metadata, _SCHEMA_COLUMN_KEYS)
                if name is not None:
                    schema[str(name)] = dict(column_metadata)

        return schema

    def _validate_catalog_query(self, catalog_name, *, columns=None,
                                column_constraints=None,
                                position_constraints=None,
                                sort_by=None, cache=True):
        schema = self._catalog_schema(catalog_name, cache=cache)
        requested = [columns] if isinstance(columns, str) else list(columns or ())
        referenced = [str(name) for name in requested]

        constraints = column_constraints or ()
        if isinstance(constraints, Mapping):
            constraints = [constraints]
        for constraint in constraints:
            if not isinstance(constraint, Mapping):
                raise InvalidQueryError("Each column constraint must be a mapping.")
            column_name = constraint.get('column_name')
            if not column_name:
                raise InvalidQueryError(
                    "Each column constraint must specify `column_name`."
                )
            referenced.append(str(column_name))

        if position_constraints:
            referenced.extend(('ra', 'dec'))
        if sort_by:
            referenced.append(str(sort_by))

        unknown = list(dict.fromkeys(name for name in referenced if name not in schema))
        if unknown:
            raise InvalidQueryError(
                "Unknown LAMOST catalog column(s): {0}.".format(
                    ", ".join(unknown)
                )
            )
        return schema

    def _apply_catalog_schema(self, table, schema):
        integer_types = {
            'bigint', 'int', 'integer', 'long', 'short', 'smallint', 'tinyint', 'int32', 'int64',
        }
        floating_types = {'decimal', 'double', 'double precision', 'float', 'numeric', 'real', 'float32', 'float64'}
        text_types = {'char', 'varchar', 'character', 'character varying', 'text', 'string', 'unicodechar',
                      'date', 'datetime', 'timestamp', 'timestamp without time zone', 'timestamp with time zone',
                      'time', 'time without time zone', 'time with time zone'}

        for name, column_metadata in schema.items():
            if name not in table.colnames:
                continue

            datatype = self._schema_value(column_metadata, _SCHEMA_DATATYPE_KEYS)
            normalized_type = str(datatype or '').lower().split('(', 1)[0].strip()
            caster = (
                int if normalized_type in integer_types
                else float if normalized_type in floating_types
                else str if normalized_type in text_types
                else bool if normalized_type in {'bool', 'boolean'}
                else None
            )
            if caster is not None:
                column = table[name]
                try:
                    if column.ndim != 1:
                        raise ValueError("Multidimensional column.")
                    values, mask = self._cast_column_values(column, caster)
                    converted = MaskedColumn(
                        values, mask=mask, name=name,
                        dtype=np.int64 if caster is int else np.float64 if caster is float
                        else np.bool_ if caster is bool else str,
                        unit=column.unit, description=column.description, meta=column.meta,
                    )
                except (TypeError, ValueError, OverflowError) as exc:
                    raise TableParseError(
                        f"Column {name!r} could not be converted to schema "
                        f"datatype {normalized_type!r}."
                    ) from exc
                table.replace_column(name, converted)

            unit = self._schema_value(column_metadata, _SCHEMA_UNIT_KEYS)
            if unit not in (None, '') and table[name].unit is None:
                try:
                    table[name].unit = u.Unit(str(unit))
                except ValueError:
                    pass

    @staticmethod
    def _cast_column_values(column, caster):
        """Return converted values and a missing-value mask for a 1-D column.

        String and numeric columns are converted with array operations; object
        columns, as produced from JSON, fall back to element-wise conversion.
        Iterating a MaskedColumn creates a masked scalar per element and is
        avoided throughout.
        """
        raw = np.asarray(column)
        mask = np.ma.getmaskarray(column)
        if raw.dtype.kind == 'S':
            raw = np.char.decode(raw, 'utf-8')
        kind = raw.dtype.kind

        if kind == 'U':
            # An empty field is missing for every type; whitespace-only fields
            # are missing for numeric and boolean types but remain string values.
            missing = mask | (raw == '')
            if caster is not str:
                missing |= np.char.strip(raw) == ''
            if caster is str:
                values = raw.copy()
                values[missing] = ''
                return LamostClass._narrow_strings(values), missing
            present = raw[~missing]
            if caster is bool:
                converted = LamostClass._booleans(np.char.lower(np.char.strip(present)))
            else:
                converted = np.array([caster(value) for value in present],
                                     dtype=np.int64 if caster is int else np.float64)
            values = np.zeros(len(raw), dtype=converted.dtype)
            values[~missing] = converted
            return values, missing

        if kind in 'iufb':
            present = raw[~mask]
            if caster is str:
                values = raw.astype(str)
                values[mask] = ''
                return LamostClass._narrow_strings(values), mask
            if caster is int:
                if kind == 'f' and (not np.isfinite(present).all() or (present != np.trunc(present)).any()):
                    raise ValueError("Non-integral value in an integer column.")
                if kind in 'fu' and (np.abs(present) >= 2.0 ** 63).any():
                    raise OverflowError("Integer value out of the int64 range.")
                values = np.zeros(len(raw), dtype=np.int64)
            elif caster is float:
                values = np.zeros(len(raw), dtype=np.float64)
            else:
                if kind == 'f' and present.size:
                    raise ValueError('Invalid boolean value.')
                if kind in 'iu' and not np.isin(present, (0, 1)).all():
                    raise ValueError('Invalid boolean value.')
                values = np.zeros(len(raw), dtype=np.bool_)
            values[~mask] = present.astype(values.dtype)
            return values, mask

        return LamostClass._cast_column_elements(raw, mask, caster)

    @staticmethod
    def _narrow_strings(values):
        # Match the minimal width a list-built string column would receive.
        width = int(np.char.str_len(values).max()) if values.size else 0
        return values.astype(f'U{max(width, 1)}')

    @staticmethod
    def _booleans(lowered):
        if not np.isin(lowered, ('true', 'false', 't', 'f', '1', '0')).all():
            raise ValueError('Invalid boolean value.')
        return np.isin(lowered, ('true', 't', '1'))

    @staticmethod
    def _cast_column_elements(raw, mask, caster):
        values = []
        missing_flags = []
        for value, masked in zip(raw, mask):
            missing = bool(masked) or value is None or np.ma.is_masked(value)
            if isinstance(value, (str, bytes)):
                missing = missing or not value or (caster is not str and not value.strip())
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            if (caster is int and not missing and isinstance(value, (float, np.floating))
                    and (not np.isfinite(value) or value != np.trunc(value))):
                raise ValueError("Non-integral value in an integer column.")
            if caster is bool and not missing:
                boolean = str(value).strip().lower()
                if boolean not in {'true', 'false', 't', 'f', '1', '0'}:
                    raise ValueError('Invalid boolean value.')
                value = boolean in {'true', 't', '1'}
            values.append(caster(value) if not missing else ('' if caster is str else 0))
            missing_flags.append(missing)
        return values, missing_flags

    def _prepare_catalog_result(self, table, *, catalog_name, columns):
        requested = [columns] if isinstance(columns, str) else list(columns or ())
        requested = [str(name) for name in requested]
        if len(table) == 0 and not table.colnames and requested:
            table = Table(names=requested)

        missing = [name for name in requested if name not in table.colnames]
        if missing:
            raise TableParseError(
                "LAMOST query result omitted requested column(s): {0}.".format(
                    ", ".join(missing)
                )
            )

        if requested:
            remaining = [name for name in table.colnames if name not in requested]
            table = table[requested + remaining]

        table.meta['catalog'] = catalog_name
        table.meta['data_release'] = self.data_release
        table.meta['sub_version'] = self.sub_version
        return table

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
            token_value = _strip_optional_quotes(config['token'])
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

        Notes
        -----
        Example config file content::

            # LAMOST API Token
            token=your_token_here
        """
        config_file = os.path.expanduser(os.fspath(config_file))
        if not os.path.exists(config_file):
            return None

        config = {}
        try:
            with open(config_file, 'r', encoding='utf-8') as fh:
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
                InputWarning
            )
            return None

        return config if config else None

    def get_dr_versions(self):
        """
        Get available Data Release versions.

        Returns
        -------
        list of dict
            Service-provided release metadata, including ``dr_version``,
            ``sub_version``, and ``public_status``. Additional fields depend
            on the service response.

        Examples
        --------
        >>> from astroquery.nadc.lamost import Lamost
        >>> versions = Lamost.get_dr_versions()  # doctest: +SKIP
        >>> for v in versions:  # doctest: +SKIP
        ...     print(f"{v['dr_version']}/{v['sub_version']}: {v['public_status']}")  # doctest: +SKIP
        """
        url = f"{self.URL.rstrip('/')}/dr_versions"
        response = self._request_raise('GET', url)
        data = self._response_json(response)
        return data.get('versions', [])

    def get_tables_metadata(self, *, cache=True):
        """
        Get metadata for all available tables in the data release.

        This method retrieves table names, column names, and data types, plus
        descriptions and units where supplied by the archive. Legacy releases
        without this endpoint use visible SQL relations; units are not inferred.
        The verified DR10/v2.0 samples supply no column units.

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
        if self._legacy_metadata():
            # pg_table_is_visible resolves the same relation as an unqualified
            # FROM name, rather than merging names from unrelated schemas.
            sql = """SELECT c.relname AS table_name, a.attname AS column_name,
                       format_type(a.atttypid, a.atttypmod) AS datatype
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                JOIN pg_attribute a ON a.attrelid=c.oid
                WHERE c.relkind IN ('r','v','m','p') AND pg_table_is_visible(c.oid)
                  AND n.nspname NOT IN ('pg_catalog','information_schema')
                  AND n.nspname NOT LIKE 'pg_toast%'
                  AND a.attnum>0 AND NOT a.attisdropped
                ORDER BY c.relname,a.attnum"""
            result = self.query_sql(sql, output_format='csv', cache=cache)
            tables = {}
            for row in result:
                name, column, datatype = (str(row[key]) for key in ('table_name', 'column_name', 'datatype'))
                columns = tables.setdefault(name, {'columns': {}})['columns']
                if column in columns:
                    raise TableParseError(f'Duplicate metadata for {name}.{column}.')
                columns[column] = {'datatype': datatype}
            if not tables:
                raise TableParseError('LAMOST SQL metadata contained no visible table columns.')
            return {'tables': tables}

        request_params = {}

        if self.token:
            request_params['token'] = self.token

        # Build URL
        url = f"{self.URL}/{self.data_release}/{self.sub_version}/tables"
        response = self._request_raise('GET', url, params=request_params, cache=cache)
        return self._normalize_tables_metadata(self._response_json(response))

    def _dr3_url(self):
        # Respect explicitly configured mirrors; these exceptions describe the
        # official gateway, not arbitrary servers sharing the same API.
        if self.data_release == 'dr3' and self.URL == 'https://www.lamost.org/openapi':
            return 'https://dr3.lamost.org'
        return None

    def _build_url(self, endpoint, resolution='low', *, obsid=None):
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
        if self._dr3_url() and resolution == 'low':
            if endpoint == 'voservice/conesearch':
                return f'{self._dr3_url()}/{endpoint}'
            if endpoint in {'spectrum/fits', 'spectrum/info'}:
                return f'{self._dr3_url()}/{endpoint}/{quote(str(obsid), safe="")}'
        res_path = 'mrs' if resolution == 'medium' else 'lrs'
        return f"{self.URL}/{self.data_release}/{self.sub_version}/{res_path}/{endpoint}"

    def _request_query_region(self, coordinates, radius, *,
                              resolution='low', output_format='csv',
                              get_query_payload=False, cache=True):
        """
        Query LAMOST catalog using cone search around given coordinates.
        """
        resolution = self._normalize_resolution(resolution)
        output_format = self._normalize_output_format(
            output_format,
            allowed=('votable', 'json', 'csv'),
        )

        c = commons.parse_coordinates(coordinates)

        request_payload = {
            'ra': c.icrs.ra.deg,
            'dec': c.icrs.dec.deg,
            'sr': self._radius_in(radius, u.deg),
            'output.fmt': output_format
        }

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return self._redact(request_payload)

        url = self._build_url('voservice/conesearch', resolution=resolution)
        return self._request_raise('GET', url, params=request_payload, cache=cache)

    def query_region(self, coordinates, radius, *,
                     resolution='low', output_format='csv',
                     get_query_payload=False, cache=True, verbose=False):
        """Query the LAMOST catalog around sky coordinates.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object
            Cone-search center.
        radius : str, float, or astropy.units.Quantity
            Positive scalar cone-search radius. Bare numbers are degrees;
            angle strings such as ``'5 arcsec'`` and angular quantities are accepted.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        output_format : {"votable", "json", "csv"}, optional
            Output format requested from the service. The default is ``'csv'``
            because some service VOTables declare string
            fields too short to represent the returned identifiers.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Query result table with catalog types and units from metadata,
            or redacted parameters when ``get_query_payload=True``. Table
            metadata identifies the catalog, release, and sub-version.

        Raises
        ------
        astroquery.exceptions.InvalidQueryError
            The radius is invalid or the requested format is unsupported.
        astroquery.exceptions.TableParseError
            The response is malformed or would truncate string values.

        Notes
        -----
        This method retrieves one response; archive row limits still apply.
        DR3 and DR8 cone services can return VOTable despite a CSV request.
        Known ``catalogue_``/``med_catalogue_`` prefixes are retained and matched to
        catalog types. Truncated string values are rejected in every format.
        """
        response = self._request_query_region(
            coordinates,
            radius,
            resolution=resolution,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        catalog_name = self._spectral_catalog_name(resolution, None)
        base_schema = self._catalog_schema(catalog_name, cache=cache)
        prefix = 'med_catalogue_' if self._normalize_resolution(resolution) == 'medium' else 'catalogue_'
        # Legacy cone services prefix column names; type both spellings, but
        # build an empty result from one of them only.
        schema = {**{prefix + name: metadata for name, metadata in base_schema.items()}, **base_schema}
        table = self._parse_table_response(response, verbose=verbose, column_schema=schema,
                                           empty_columns=list(base_schema))
        return self._prepare_catalog_result(table, catalog_name=catalog_name, columns=None)

    def query_sql_async(self, sql, *, output_format=None,
                        get_query_payload=False, cache=True):
        """Execute SQL and return the unparsed HTTP response.

        Parameters
        ----------
        sql : str
            SQL accepted by the selected release.
        output_format : {None, "json", "csv", "votable", "txt"}, optional
            Requested wire format. None selects CSV for legacy configurations
            and JSON for modern ones. Explicit formats are sent unchanged.
        get_query_payload : bool, optional
            Return redacted request parameters instead of sending the query.
        cache : bool, optional
            Use the astroquery cache for anonymous requests.

        Returns
        -------
        requests.Response or dict
            Original response, or redacted parameters. HTTP, authentication,
            and explicit service errors are checked; table parsing is deferred.

        Notes
        -----
        This follows astroquery's ``_async`` convention, not Python async/await.
        To retain a response for independent parsing, save ``response.content``
        before closing it. Raw responses may contain private data and credentials.
        """
        if output_format is None:
            output_format = 'csv' if self._legacy_metadata() else 'json'
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
            return self._redact(request_payload)

        url = (f'{self._dr3_url()}/sql/q' if self._dr3_url()
               else f"{self.URL}/{self.data_release}/{self.sub_version}/sql")
        return self._request_raise('GET', url, params=request_payload, cache=cache)

    def query_sql(self, sql, *, output_format=None, column_schema=None,
                  get_query_payload=False, cache=True, verbose=False):
        """Execute a raw SQL query on the LAMOST database.

        Parameters
        ----------
        sql : str
            SQL statement accepted by the LAMOST service.
        output_format : {None, "json", "csv", "votable", "txt"}, optional
            Requested wire format. None selects CSV for legacy configurations
            and JSON for modern ones. Save the returned table with Table.write.
        column_schema : dict, optional
            Result column names mapped to metadata dictionaries, for example
            ``{'temperature': {'datatype': 'double', 'unit': 'K'}}``.
            Use this for SQL aliases and expressions without response column
            metadata. Unannotated JSON values retain their service types.
            JSON null cells are masked, including without a schema.
            With a schema, CSV/TXT fields are read as strings before conversion;
            columns without a declared datatype remain strings. Character
            identifiers retain leading zeros. Only declared units are attached.
        get_query_payload : bool, optional
            Return the GET parameters with credentials redacted instead of
            executing the request. ``column_schema`` is local to the parser.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            SQL result table, or request payload when
            ``get_query_payload=True``.

        Raises
        ------
        astroquery.exceptions.InvalidQueryError
            ``column_schema`` is not a mapping of column metadata dictionaries.
        astroquery.exceptions.TableParseError
            A declared column is absent or cannot be converted to its datatype.
        """
        if column_schema is not None and (
            not isinstance(column_schema, Mapping)
            or any(not isinstance(value, Mapping) for value in column_schema.values())
        ):
            raise InvalidQueryError("column_schema must map result column names to metadata dictionaries.")
        response = self.query_sql_async(
            sql,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        table = self._parse_table_response(response, verbose=verbose, column_schema=column_schema)
        missing = set(column_schema or ()) - set(table.colnames)
        if missing:
            raise TableParseError(f"LAMOST SQL result omitted schema column(s): {', '.join(sorted(missing))}.")
        return table

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
                return self._redact({
                    'json': request_payload,
                    'params': {'token': self.token},
                })
            return self._redact(request_payload)

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
                      output_format=None,
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
            Service-format cone, proximity, or rectangle constraint. Cone and
            proximity queries use SQL to preserve all qualifying matches.
            Proximity results retain original input line numbers.
        columns : iterable of str, optional
            Columns to include in the result.
        sort_by : str, optional
            Column used for sorting.
        sort_order : {"asc", "desc"}, optional
            Sort order.
        max_rows : int, optional
            Maximum rows in this page. Additional pages are not fetched automatically.
        page : int, optional
            One-based page number.
        output_format : {None, "json", "csv", "votable", "txt"}, optional
            Requested wire format. None selects CSV for legacy configurations
            and JSON for modern ones. An explicit format is sent unchanged.
        get_query_payload : bool, optional
            Return the actual redacted request parameters without executing the
            data query. SQL-backed requests fetch field metadata first and
            validate columns; native request payloads are returned unvalidated.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Query result table, or request payload when
            ``get_query_payload=True``.

        Raises
        ------
        astroquery.exceptions.InvalidQueryError
            Catalog names or columns disagree with the service metadata.
        astroquery.exceptions.TableParseError
            Requested columns are missing or values disagree with their datatypes.
        """
        if columns is not None:
            columns = [columns] if isinstance(columns, str) else list(columns)
            if len(set(map(str, columns))) != len(columns):
                raise InvalidQueryError('columns must not contain duplicate names.')
        if column_constraints is not None and not isinstance(column_constraints, Mapping):
            column_constraints = list(column_constraints)
        if sort_order not in ('asc', 'desc'):
            raise InvalidQueryError('sort_order must be asc or desc.')

        if output_format is None:
            output_format = 'csv' if self._legacy_metadata() else 'json'
        max_rows = self._page_integer(max_rows, 'max_rows')
        page = self._page_integer(page, 'page')
        use_sql = self._legacy_metadata() or bool(position_constraints and (
            not isinstance(position_constraints, Mapping) or set(position_constraints) != {'rect'}))
        schema = None
        if use_sql or not get_query_payload:
            schema = self._validate_catalog_query(
                catalog_name,
                columns=columns,
                column_constraints=column_constraints,
                position_constraints=position_constraints,
                sort_by=sort_by,
                cache=cache,
            )

        if use_sql:
            sql, extras = catalog_sql(
                catalog_name, schema, constraints=column_constraints, position=position_constraints,
                columns=columns, sort_by=sort_by, sort_order=sort_order, max_rows=max_rows, page=page,
            )
            result_schema = {name: schema[name] for name in (columns or schema)}
            result_schema.update(extras)
            response = self.query_sql_async(sql, output_format=output_format,
                                            get_query_payload=get_query_payload, cache=cache)
            if get_query_payload:
                return response
            if not response.content.removeprefix(b'\xef\xbb\xbf').strip():
                # Count this page once. Never reinterpret an arbitrary user SQL
                # query or a failed count as an empty catalog.
                count = self.query_sql(
                    f'SELECT COUNT(*) AS n FROM ({sql}) AS page_rows',
                    output_format='csv', column_schema={'n': {'datatype': 'long'}}, cache=cache,
                )
                if len(count) != 1 or np.ma.is_masked(count['n'][0]) or count['n'][0] != 0:
                    self._validate_data_response(response)
                if any(not self._schema_value(meta, _SCHEMA_DATATYPE_KEYS) for meta in result_schema.values()):
                    raise TableParseError('Cannot construct an empty SQL table without reliable column types.')
                table = Table(names=list(result_schema))
                self._apply_catalog_schema(table, result_schema)
            else:
                table = self._parse_table_response(response, verbose=verbose, column_schema=result_schema)
            missing = set(result_schema) - set(table.colnames)
            if missing:
                raise TableParseError(f'LAMOST SQL result omitted column(s): {", ".join(sorted(missing))}.')
            table = self._prepare_catalog_result(table, catalog_name=catalog_name, columns=columns)
            self.table = table
            return table

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
        result_schema = schema if not columns else {name: schema[name] for name in columns}
        table = self._parse_result(response, verbose=verbose, column_schema=result_schema)
        table = self._prepare_catalog_result(
            table,
            catalog_name=catalog_name,
            columns=columns,
        )
        self.table = table
        return table

    def _build_structured_cone_constraint(self, coordinates, radius, *, nearest_only=False):
        c = commons.parse_coordinates(coordinates)
        if not isinstance(nearest_only, bool):
            raise InvalidQueryError('nearest_only must be a boolean.')

        return {
            'cone': {
                'racenter': float(c.icrs.ra.to_value(u.deg)),
                'deccenter': float(c.icrs.dec.to_value(u.deg)),
                'radius': self._radius_in(radius, u.arcsec),
                'cone_nearestonly': bool(nearest_only),
            },
        }

    def _spectral_catalog_name(self, resolution, catalog_name, *, stellar=False):
        resolution = self._normalize_resolution(resolution)
        if catalog_name is not None:
            return catalog_name
        return spectral_catalog(self.data_release, self.sub_version, resolution, stellar=stellar)

    def _spectral_fields(self, resolution):
        resolution = self._normalize_resolution(resolution)
        if resolution == 'medium' and self.sub_version in EARLY_MRS.get(self.data_release, ()):
            return {'snr': 'snr', 'teff': 'teff', 'logg': 'logg', 'feh': 'feh'}
        return _SPECTRAL_FIELDS[resolution]

    def _spectral_column_constraints(
        self,
        *,
        resolution='low',
        snr_min=None,
        snr_column=None,
        teff_range=None,
        logg_range=None,
        feh_range=None,
    ):
        fields = self._spectral_fields(resolution)
        if snr_column is None:
            snr_column = fields['snr']

        constraints = []
        if snr_min is not None:
            if not snr_column:
                raise InvalidQueryError("snr_column must be provided when snr_min is set.")
            _append_min_constraint(constraints, snr_column, snr_min)
        _append_range_constraint(constraints, fields['teff'], teff_range)
        _append_range_constraint(constraints, fields['logg'], logg_range)
        _append_range_constraint(constraints, fields['feh'], feh_range)
        return constraints or None

    def query_spectra(
        self,
        coordinates=None,
        radius=None,
        *,
        resolution='low',
        catalog_name=None,
        snr_min=None,
        snr_column=None,
        teff_range=None,
        logg_range=None,
        feh_range=None,
        columns=None,
        nearest_only=False,
        sort_by=None,
        sort_order='asc',
        max_rows=100,
        page=1,
        output_format=None,
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
            Positive scalar cone-search radius, required with ``coordinates``.
            Bare numbers are arcseconds; angle strings and angular quantities are accepted.
        resolution : {"low", "medium"}, optional
            Spectral-resolution catalog family.
        catalog_name : str, optional
            Explicit catalog endpoint name. Field-name defaults still follow
            ``resolution``.
        snr_min : float, optional
            Minimum signal-to-noise ratio.
        snr_column : str, optional
            Column used for the SNR filter. Defaults to ``snrg`` for LRS and
            ``snr`` for MRS.
        teff_range, logg_range, feh_range : sequence of float, optional
            Inclusive stellar-parameter ranges: temperature in kelvin, log10
            surface gravity in cm/s2, and [Fe/H] in dex, respectively.
        columns : iterable of str, optional
            Columns to include in the result.
        nearest_only : bool, optional
            Select the nearest row satisfying both position and physical cuts.
            Requires coordinates and page=1. False (default) returns qualifying
            matches up to max_rows, ordered by distance unless sort_by is given.
        sort_by : str, optional
            Column used for sorting.
        sort_order : {"asc", "desc"}, optional
            Sort order.
        max_rows : int, optional
            Maximum rows per page.
        page : int, optional
            One-based page number.
        output_format : {None, "json", "csv", "votable", "txt"}, optional
            Requested wire format. None selects CSV for legacy configurations
            and JSON for modern ones. An explicit format is sent unchanged.
        get_query_payload : bool, optional
            Return the actual redacted request parameters without executing the
            data query. SQL-backed requests fetch field metadata first and
            validate columns; native request payloads are returned unvalidated.
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
        if not isinstance(nearest_only, bool) or (nearest_only and coordinates is None):
            raise InvalidQueryError('nearest_only must be a boolean and True requires coordinates.')

        position_constraints = None
        if coordinates is not None:
            position_constraints = self._build_structured_cone_constraint(
                coordinates,
                radius,
                nearest_only=nearest_only,
            )

        return self.query_catalog(
            self._spectral_catalog_name(
                resolution, catalog_name,
                stellar=any(value is not None for value in (teff_range, logg_range, feh_range)),
            ),
            column_constraints=self._spectral_column_constraints(
                resolution=resolution,
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
        snr_column=None,
        teff_range=None,
        logg_range=None,
        feh_range=None,
        columns=None,
        nearest_only=False,
        sort_by=None,
        sort_order='asc',
        max_rows=100,
        page=1,
        output_format=None,
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
            Positive scalar cone-search radius, required with ``coordinates``.
            Bare numbers are arcseconds; angle strings and angular quantities are accepted.
        resolution : {"low", "medium"}, optional
            Spectral-resolution catalog family.
        catalog_name : str, optional
            Explicit catalog endpoint name. Field-name defaults still follow
            ``resolution``.
        snr_min : float, optional
            Minimum signal-to-noise ratio.
        snr_column : str, optional
            Column used for the SNR filter and included by default. Defaults
            to ``snrg`` for LRS and ``snr`` for MRS.
        teff_range, logg_range, feh_range : sequence of float, optional
            Inclusive stellar-parameter ranges: temperature in kelvin, log10
            surface gravity in cm/s2, and [Fe/H] in dex, respectively.
        columns : iterable of str, optional
            Columns to include in the result. Defaults to core stellar
            atmospheric-parameter columns.
        nearest_only : bool, optional
            Select the nearest row satisfying both position and physical cuts.
            Requires coordinates and page=1. False (default) returns qualifying
            matches up to max_rows, ordered by distance unless sort_by is given.
        sort_by : str, optional
            Column used for sorting.
        sort_order : {"asc", "desc"}, optional
            Sort order.
        max_rows : int, optional
            Maximum rows per page.
        page : int, optional
            One-based page number.
        output_format : {None, "json", "csv", "votable", "txt"}, optional
            Requested wire format. None selects CSV for legacy configurations
            and JSON for modern ones. An explicit format is sent unchanged.
        get_query_payload : bool, optional
            Return the actual redacted request parameters without executing the
            data query. SQL-backed requests fetch field metadata first and
            validate columns; native request payloads are returned unvalidated.
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
        fields = self._spectral_fields(resolution)
        if snr_column is None:
            snr_column = fields['snr']

        if columns is None:
            columns = [
                'obsid',
                'ra',
                'dec',
                fields['teff'],
                fields['logg'],
                fields['feh'],
            ]
            if snr_column:
                columns = [*columns, snr_column]

        return self.query_spectra(
            coordinates=coordinates,
            radius=radius,
            resolution=resolution,
            catalog_name=self._spectral_catalog_name(resolution, catalog_name, stellar=True),
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
        radius : str, float, or astropy.units.Quantity, optional
            Positive scalar search radius. Bare numbers are degrees;
            angle strings and angular quantities are accepted.
        ra, dec : float, optional
            Target coordinates in degrees.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.

        Returns
        -------
        dict
            Keys ``unique_id`` and ``related_obsids`` identify the service's
            target (None when absent) and its observations. ``related_obsids``
            is an unlabelled union across resolutions; it cannot determine
            the resolution needed for downloads. ``related_obsids_low`` and
            ``related_obsids_medium`` distinguish the resolution families.
            With ``get_query_payload=True``, return request parameters instead.

        Notes
        -----
        Associations follow the selected release's identity rules, not a
        client-side coordinate match. The DR3 service does not provide this
        lookup; external-catalog candidates are not substituted for its UID.
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

        if obsid is not None:
            request_payload = {'obsid': str(obsid)}
        else:
            if ra is None or dec is None or radius is None:
                raise ValueError("Either 'obsid' OR all of ('ra', 'dec', 'radius') must be provided")
            request_payload = {
                'ra': float(ra), 'dec': float(dec),
                'radius': self._radius_in(radius, u.deg),
            }
        if self.token:
            request_payload['token'] = self.token
        if get_query_payload:
            return self._redact(request_payload)

        url = f"{self.URL}/{self.data_release}/{self.sub_version}/get_unique_id_and_related_obsids"
        response = self._request_raise('GET', url, params=request_payload, cache=cache)
        return self._normalize_unique_id_result(self._response_json(response))

    def _request_metadata(self, obsid, *,
                          resolution='low', get_query_payload=False, cache=True):
        """Get metadata/information for a specific spectrum."""
        resolution = self._normalize_resolution(resolution)
        request_payload = {'obsid': str(obsid)}

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return self._redact(request_payload)

        url = self._build_url('spectrum/info', resolution=resolution, obsid=obsid)
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
            ``get_query_payload=True``. Legacy field/value records become one
            row; MRS exposure/band rows remain separate. Known catalog mappings
            supply column types; other fields retain their service types.

        Notes
        -----
        Legacy schema discovery uses SQL, which may require authentication
        even when spectrum metadata and FITS are public (observed for DR7).
        Schema failures propagate; unknown default catalog mappings keep the
        raw parsing path without inferring a catalog or column types.
        """
        response = self._request_metadata(
            obsid,
            resolution=resolution,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        data = self._response_json(response)
        if isinstance(data, Mapping) and 'response' in data:
            fields = data['response']
            if not isinstance(fields, list) or not all(
                    isinstance(field, Mapping) and isinstance(field.get('what'), str)
                    and field['what'] and 'data' in field for field in fields):
                raise TableParseError('Invalid legacy LAMOST spectrum metadata fields.')
            names = [field['what'] for field in fields]
            if len(set(names)) != len(names):
                raise TableParseError('Duplicate legacy LAMOST spectrum metadata fields.')
            table = Table([{field['what']: field['data'] for field in fields}])
            metadata = self.get_tables_metadata(cache=cache)['tables']
            # Physical and observation fields may come from separate old tables.
            for catalog in ('catalogue', 'stellar'):
                if catalog in metadata:
                    self._apply_catalog_schema(table, self._columns_schema(metadata[catalog]['columns']))
            self.table = table
            return table
        schema = None
        if self._legacy_metadata() or self.sub_version in MODERN_CATALOGS.get(self.data_release, ()):
            schema = self._catalog_schema(self._spectral_catalog_name(resolution, None), cache=cache)
        return self._parse_table_response(response, verbose=verbose, column_schema=schema)

    def get_spectra(self, obsid, *, resolution='low', get_query_payload=False,
                    verify='warn'):
        """Download spectrum FITS data for an observation ID.

        Parameters
        ----------
        obsid : str or int
            Observation ID of the spectrum.
        resolution : {"low", "medium"}, optional
            Spectral-resolution service to query.
        get_query_payload : bool, optional
            Return redacted request parameters instead of fetching files.
        verify : str, optional
            FITS verification option passed to the ``verify`` method of the
            `astropy.io.fits.HDUList`. Default is ``"warn"``.

        Returns
        -------
        list of astropy.io.fits.HDUList or dict
            A single-element list of in-memory FITS objects, or redacted parameters when
            ``get_query_payload=True``. The caller must close the HDU lists.
            HTTP responses are closed before returning.
        """
        url_list = self.get_spectrum_list(obsid, resolution=resolution,
                                          get_query_payload=get_query_payload)
        if get_query_payload:
            return url_list

        with self._request_raise('GET', url_list[0]) as response:
            with commons.get_readable_fileobj(BytesIO(response.content), encoding='binary') as source:
                spectrum = fits.HDUList.fromstring(source.read())
        try:
            spectrum.verify(verify)
        except Exception:
            spectrum.close()
            raise
        return [spectrum]

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
        list of str or dict
            A single-element list of FITS file URLs, or redacted parameters when
            ``get_query_payload=True``. Download URLs contain the token for
            authenticated clients and must not be logged or shared.
        """
        resolution = self._normalize_resolution(resolution)
        request_payload = {'obsid': str(obsid)}

        if self.token:
            request_payload['token'] = self.token

        if get_query_payload:
            return self._redact(request_payload)

        # Build URL for FITS download
        base_url = self._build_url('spectrum/fits', resolution=resolution, obsid=obsid)
        url = f"{base_url}?{urlencode(request_payload)}"

        return [url]

    def _resolve_download_path(self, response, save_dir, filename, default_name):
        if filename:
            if os.path.isabs(filename):
                return filename
            return os.path.join(save_dir, filename)

        content_disp = response.headers.get('Content-Disposition', '')
        filename_match = re.search(r'filename=([^;]+)', content_disp, re.IGNORECASE)
        resolved = default_name
        if filename_match:
            # Keep only the final path component; a header naming no file
            # (empty, "." or "..") must not turn save_dir itself into the target.
            candidate = os.path.basename(filename_match.group(1).strip(' "\''))
            if candidate not in ('', '.', '..'):
                resolved = candidate

        return os.path.join(save_dir, resolved)

    def _check_download_body(self, response, path):
        # Inspect completed text candidates, independent of network chunk boundaries.
        # FITS/gzip products only cost a prefix read; text diagnostics are bounded.
        with open(path, 'rb') as source:
            prefix = source.read(8192).removeprefix(b'\xef\xbb\xbf').lstrip()
            if prefix and not prefix.startswith((b'{', b'[', b'<')):
                return
            source.seek(0)
            content = source.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            raise TableParseError('LAMOST catalog text response exceeds the 1 MiB diagnostic limit.')
        body_response = self._diagnostic_response(response)
        body_response._content = content
        body_response._content_consumed = True
        try:
            self._raise_response_error(body_response, 'LAMOST catalog download')
            kind = 'text' if prefix else 'an empty body'
            raise TableParseError(f'LAMOST catalog download returned {kind} instead of a FITS/CSV gzip product.')
        except Exception:
            self.response = self._diagnostic_response(body_response)
            raise

    def download_catalog(self, catalog_name, *, resolution='low',
                         save_dir='./',
                         filename=None, overwrite=True, cache=True,
                         verify='exception'):
        """
        Download a catalog product (FITS, or the DR3 plan CSV gzip).

        Parameters
        ----------
        catalog_name : str
            File product name from the selected release's download page,
            for example ``dr10_v2.0_LRS_plan.fits.gz`` for DR10/v2.0 LRS.
            These names are distinct from SQL relation names in table metadata.
        resolution : str, optional
            Spectral resolution: 'low' for LRS (default) or 'medium' for MRS.
        save_dir : str, optional
            Directory to save the downloaded file. Default is current directory.
        filename : str, optional
            Override the output filename. Relative paths are resolved against
            save_dir. If None, use server-provided filename and fall back to
            "{catalog_name}.fits.gz", or "dr3_plan.csv.gz" for the native DR3 plan.
        overwrite : bool, optional
            If True, overwrite existing file. Default is True.
        cache : bool, optional
            Retained for compatibility. Streaming downloads bypass the cache.
        verify : str, optional
            FITS verification option passed to
            the ``verify`` method of `astropy.io.fits.HDUList`. The default, ``"exception"``,
            rejects non-compliant FITS products before publication. The native
            DR3 plan is validated as CSV instead; this option does not apply to it.

        Returns
        -------
        str
            Path to the downloaded catalog file, or the existing file when
            ``overwrite=False``. Existing files are not revalidated in this case.

        Notes
        -----
        The response is closed on success, skip, and failure. A temporary file
        with a unique name is validated before replacing the destination;
        a failed write or FITS
        verification preserves an existing destination.

        Examples
        --------
        >>> from astroquery.nadc.lamost import LamostClass
        >>> client = LamostClass(data_release='dr10', sub_version='v2.0')
        >>> filepath = client.download_catalog('dr10_v2.0_LRS_plan.fits.gz')  # doctest: +SKIP
        """
        resolution = self._normalize_resolution(resolution)

        request_params = {'name': catalog_name}
        dr3_plan = bool(self._dr3_url() and resolution == 'low')
        if dr3_plan:
            if catalog_name not in {'plan', 'dr3_plan', 'dr3_plan.csv.gz'}:
                raise InvalidQueryError('The verified DR3 catalog download is dr3_plan.csv.gz (catalog_name="plan").')
            request_params['name'] = 'dr3_plan.csv.gz'

        if self.token:
            request_params['token'] = self.token

        # Build URL
        url = f'{self._dr3_url()}/catdl' if dr3_plan else self._build_url('catalog', resolution=resolution)

        # Download file
        with self._request_raise(
            'GET',
            url,
            params=request_params,
            cache=cache,
            stream=True,
        ) as response:
            filepath = self._resolve_download_path(
                response, save_dir, filename, 'dr3_plan.csv.gz' if dr3_plan else f"{catalog_name}.fits.gz"
            )
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            if os.path.exists(filepath) and not overwrite:
                return filepath

            try:
                directory = os.path.dirname(os.path.abspath(filepath))
                with tempfile.TemporaryDirectory(dir=directory) as temp_dir:
                    temp_filepath = os.path.join(temp_dir, 'catalog')
                    with open(temp_filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self._check_download_body(response, temp_filepath)
                    if dr3_plan:
                        with gzip.open(temp_filepath, 'rb') as source:
                            csv_response = Response()
                            csv_response._content = source.read()
                        table = self._parse_csv_result(csv_response)
                        if not {'pid', 'planid', 'ra', 'dec'}.issubset(table.colnames):
                            raise TableParseError('DR3 plan catalog omitted required fields.')
                    else:
                        with fits.open(temp_filepath) as hdul:
                            hdul.verify(verify)
                    os.replace(temp_filepath, filepath)
            except Exception as error:
                self._sanitize_exception(error)
                raise

        return filepath

    def _parse_result(self, response, *, verbose=False, column_schema=None, empty_columns=None):
        """
        Parse response into an astropy Table based on content type.

        Supports votable, json, csv, and txt formats based on Content-Type header.

        Parameters
        ----------
        response : `requests.Response`
            HTTP response from query.
        verbose : bool, optional
            If False, suppress VOTable warnings. Default is False.
        column_schema : dict, optional
            Column metadata applied to the parsed table.
        empty_columns : list of str, optional
            Column names for a result without any columns. Defaults to the
            schema names.

        Returns
        -------
        table : `~astropy.table.Table`
            Parsed table from the response.
        """
        try:
            self._raise_response_error(response, 'LAMOST API')
            self._validate_data_response(response)

            content_type = (response.headers.get('Content-Type') or '').lower()
            prefix = response.content.removeprefix(b'\xef\xbb\xbf').lstrip()
            if prefix.startswith((b'{', b'[')):
                table = self._parse_json_result(response)
            elif prefix.startswith(b'<'):
                table = self._parse_votable_result(response, verbose=verbose)
            elif 'csv' in content_type or (not content_type and b'\n' in prefix):
                table = self._parse_csv_result(response, column_schema=column_schema)
            elif 'text/plain' in content_type:
                table = self._parse_txt_result(response, column_schema=column_schema)
            elif 'json' in content_type:
                table = self._parse_json_result(response)
            else:
                table = self._parse_votable_result(response, verbose=verbose)

            schema = self._columns_schema(table.meta.get('columns'))
            schema.update(column_schema or {})
            if not len(table) and not table.colnames and schema:
                names = list(schema) if empty_columns is None else list(empty_columns)
                table = Table(names=names, meta=table.meta)
            self._apply_catalog_schema(table, schema)
            return table
        except Exception as error:
            self.response = self._diagnostic_response(response)
            self._sanitize_exception(error)
            raise

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
        try:
            self._validate_data_response(response)

            content = sanitize_votable_content(
                response.content,
                fix_invalid_date=True,
                fix_missing_field_datatype=True,
                fix_empty_arraysize=True,
            )
            tf = BytesIO(content)
            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always')
                votable_file = votable.parse(tf, verify='warn')
                first_table = votable_file.get_first_table()
                table = first_table.to_table(use_names_over_ids=True)

            if any(issubclass(item.category, W46) for item in caught_warnings):
                raise TableParseError(
                    "LAMOST VOTable declares a string arraysize shorter than "
                    "the returned value; refusing to return truncated data."
                )
            # Some legacy TABLEDATA encodes a missing integer as <TD/> without
            # a null sentinel. Astropy can return an ordinary zero for it. Only
            # integer columns holding an unmasked zero, or with an unexpected
            # shape, need the cell-level scan of the document.
            integer_types = {'short', 'int', 'long', 'unsignedByte'}
            fields = first_table.fields
            scanned = []
            for i, field in enumerate(fields):
                if field.datatype not in integer_types:
                    continue
                column = table.columns[i]
                if column.ndim != 1 or column.dtype.kind not in 'iu' or (
                        (np.asarray(column) == 0) & ~np.ma.getmaskarray(column)).any():
                    scanned.append(i)
            empty_cells = self._votable_empty_cells(content, len(fields), scanned) if scanned else None
            if empty_cells is not None:
                if len(next(iter(empty_cells.values()), ())) != len(table):
                    raise TableParseError('Cannot reliably map LAMOST VOTable TABLEDATA cells to columns.')
                for i, missing in empty_cells.items():
                    if not missing.any():
                        continue
                    column = table.columns[i]
                    if fields[i].arraysize not in (None, '1') or column.ndim != 1 or column.dtype.kind not in 'iu':
                        raise TableParseError(f'Cannot reliably mask missing integer array in column {column.name!r}.')
                    mask = np.ma.getmaskarray(column) | missing
                    table.replace_column(column.name, MaskedColumn(column, mask=mask))
            if verbose:
                for item in caught_warnings:
                    warnings.warn(item.message)
            return table
        except TableParseError as ex:
            self.response = response
            self.table_parse_error = ex
            raise
        except Exception as ex:
            # Store response for debugging
            self.response = response
            self.table_parse_error = ex
            raise TableParseError(
                f"Failed to parse response as VOTable: {str(ex)}"
            )

    @staticmethod
    def _votable_empty_cells(content, field_count, indices):
        """Find empty TABLEDATA cells of the first TABLE for the given field indices.

        The document is streamed and each row is discarded after inspection,
        so memory stays bounded by one row. Returns ``None`` when the first
        table has no TABLEDATA; otherwise a mapping from field index to a
        boolean array of empty cells.
        """
        def local_name(element):
            return element.tag.rsplit('}', 1)[-1]

        empties = {i: [] for i in indices}
        tabledata_found = False
        for _, element in ElementTree.iterparse(BytesIO(content), events=('end',)):
            tag = local_name(element)
            if tag == 'TR':
                cells = list(element)
                if len(cells) != field_count or any(local_name(cell) != 'TD' or len(cell) for cell in cells):
                    raise TableParseError('Cannot reliably map LAMOST VOTable TABLEDATA cells to columns.')
                for i in indices:
                    empties[i].append(not (cells[i].text or '').strip())
                element.clear()
            elif tag == 'TABLEDATA':
                if any(local_name(row) != 'TR' for row in element):
                    raise TableParseError('Cannot reliably map LAMOST VOTable TABLEDATA cells to columns.')
                tabledata_found = True
                element.clear()
            elif tag == 'TABLE':
                break
        if not tabledata_found:
            return None
        return {i: np.array(flags, dtype=bool) for i, flags in empties.items()}

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
            data = self._response_json(response)

            if isinstance(data, list):
                table = Table(data)
            elif isinstance(data, dict):
                if 'rows' in data:
                    columns = data.get('columns', [])
                    rows = data['rows']
                    if not isinstance(rows, list):
                        raise ValueError("JSON response 'rows' must be a list.")
                    if 'columns' not in data and not all(isinstance(row, Mapping) for row in rows):
                        raise ValueError("JSON response without columns requires dictionary rows.")

                    column_names = []
                    if isinstance(columns, (list, tuple)):
                        for column in columns:
                            if isinstance(column, str):
                                column_names.append(column)
                            else:
                                name = self._schema_value(column, _SCHEMA_COLUMN_KEYS)
                                if name is not None:
                                    column_names.append(str(name))

                    if rows and all(isinstance(row, Mapping) for row in rows):
                        table = Table(rows)
                    elif rows and column_names:
                        table = Table(rows=rows, names=column_names)
                    elif rows:
                        table = Table(rows=rows)
                    else:
                        table = Table(names=column_names)

                    if column_names:
                        ordered = [name for name in column_names if name in table.colnames]
                        remaining = [name for name in table.colnames if name not in ordered]
                        table = table[ordered + remaining]
                    if 'columns' in data:
                        table.meta['columns'] = columns
                    if 'total' in data:
                        table.meta['total'] = data['total']
                elif 'data' in data:
                    table = Table(data['data'])
                else:
                    raise ValueError('Unrecognized JSON table object.')
            else:
                raise ValueError(f"Unexpected JSON structure: {type(data)}")

            for name in table.colnames:
                column = table[name]
                if column.dtype.kind == 'O' and column.ndim == 1:
                    missing = np.array([value is None for value in column], dtype=bool)
                    if missing.any():
                        table.replace_column(name, MaskedColumn(column, mask=np.ma.getmaskarray(column) | missing))
            return table

        except Exception as ex:
            self.response = response
            self.json_parse_error = ex
            raise TableParseError(
                f"Failed to parse response as JSON: {str(ex)}"
            )

    def _parse_csv_result(self, response, *, column_schema=None):
        """
        Parse CSV or unambiguous historical pipe-delimited table text.

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
            text = _table_response_text(response)
            delimiter = _csv_delimiter(text)
            # Astropy's CSV reader pads short rows and renames duplicate headers.
            # Validate the structure first so damaged responses cannot look valid.
            # StringIO splits only on CSV line endings, unlike str.splitlines(),
            # which also splits characters such as vertical tabs inside fields.
            lines = list(StringIO(text, newline=''))
            records = csv.reader(lines, delimiter=delimiter, strict=True)
            header = None
            logical_records = []
            previous_line = 0
            for record in records:
                original = ''.join(lines[previous_line:records.line_num])
                previous_line = records.line_num
                if not record or (header is None and len(record) == 1 and not record[0].strip()):
                    continue
                if header is None:
                    header = [name.strip() for name in record]
                    if any(not name for name in header) or len(set(header)) != len(header):
                        raise ValueError("Table header contains empty or duplicate column names.")
                elif len(record) != len(header):
                    raise ValueError(
                        f"Table record ending at line {records.line_num} has {len(record)} fields; "
                        f"expected {len(header)}."
                    )
                logical_records.append(original)
            if header is None:
                raise ValueError("Table response has no column header.")
            reader = _CsvReader()
            reader.names = header
            reader.header.splitter.delimiter = delimiter
            reader.header.splitter.process_line = None
            reader.data.splitter.delimiter = delimiter
            reader.data.splitter.process_line = None
            reader.data.splitter.process_val = None
            reader.data.splitter.skipinitialspace = False
            # Match ascii.read's empty-field masks and numeric inference, while
            # retaining strings until an explicit catalog schema is applied.
            reader.data.fill_values = [('', '0')]
            reader.outputter.converters = {'*': [ascii.convert_numpy(str)]} if column_schema else {}
            return reader.read(logical_records)
        except Exception as ex:
            self.response = response
            raise TableParseError(
                f"Failed to parse response as CSV: {str(ex)}"
            )

    def _parse_txt_result(self, response, *, column_schema=None):
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
            text = _table_response_text(response)
            return ascii.read(
                text.splitlines(keepends=True),
                format='tab',
                comment=r'\s*#',
                guess=False,
                fast_reader=False,
                converters={'*': [ascii.convert_numpy(str)]} if column_schema else {},
            )
        except Exception as ex:
            self.response = response
            raise TableParseError(
                f"Failed to parse response as plain text: {str(ex)}"
            )


# Singleton instance for module-level access
Lamost: LamostClass = LamostClass()


# Utility functions for FITS spectrum processing

def _spectrum_table_arrays(hdu, *, allow_loglam=False):
    """Read the named spectral arrays shared by LRS and MRS table HDUs."""
    if not isinstance(hdu, fits.BinTableHDU) or hdu.data is None or len(hdu.data) == 0:
        raise ValueError("Spectrum HDU must contain a nonempty binary table.")
    columns = {name.upper() for name in hdu.columns.names}
    loglam = allow_loglam and 'LOGLAM' in columns
    wavelength_column = 'LOGLAM' if loglam else 'WAVELENGTH'
    if 'FLUX' not in columns or wavelength_column not in columns:
        raise ValueError("Spectrum table requires FLUX and WAVELENGTH (or historical MRS LOGLAM) columns.")
    if loglam:
        if 'WAVELENGTH' in columns:
            raise ValueError("Spectrum table has ambiguous WAVELENGTH and LOGLAM columns.")
        # Historical MRS files store one scalar pixel per row, including coadds.
        flux = np.array(hdu.data['FLUX'], copy=True)
        wavelength = np.array(hdu.data['LOGLAM'], copy=True)
    else:
        if len(hdu.data) != 1:
            raise ValueError("FLUX and WAVELENGTH require one table row of vector arrays.")
        flux = np.array(hdu.data['FLUX'][0], copy=True)
        wavelength = np.array(hdu.data['WAVELENGTH'][0], copy=True)
    if (flux.ndim != 1 or flux.size == 0 or flux.shape != wavelength.shape
            or flux.dtype.kind not in 'iuf' or wavelength.dtype.kind not in 'iuf'):
        raise ValueError(f"FLUX and {wavelength_column} must be nonempty numeric arrays of equal length.")
    if loglam:
        invalid = np.flatnonzero(~np.isfinite(wavelength))
        if invalid.size:
            first = invalid[0]
            raise ValueError(
                f"LOGLAM must be finite; found {invalid.size} invalid pixels, "
                f"first at zero-based index {first}: {wavelength[first]!r}."
            )
        # Promote before exponentiating: float32 log wavelengths otherwise lose
        # precision unnecessarily. Do not apply RV corrections or reorder pixels.
        # The MRS parser checks the converted values, including overflow and
        # underflow to zero, and reports the extension and offending pixel.
        with np.errstate(over='ignore', under='ignore', invalid='ignore'):
            wavelength = 10.0 ** wavelength.astype(np.float64)
    return wavelength, flux


def parse_lrs_spectrum(filename):
    """
    Parse a low-resolution spectrum (LRS) FITS file.

    Read the wavelength and flux arrays without smoothing, changing flux
    precision, selecting pixels, or applying a velocity correction.

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

    Raises
    ------
    ValueError
        The file is neither a primary-HDU LRS image with COEFF0/COEFF1 nor
        a two-HDU file with FLUX and WAVELENGTH table columns.

    Notes
    -----
    This parser validates the file layout, not the scientific quality of its
    pixels. It does not reject nonfinite or nonpositive wavelength/flux values.

    Examples
    --------
    >>> wavelength, flux = parse_lrs_spectrum('spec.fits')  # doctest: +SKIP
    """
    with fits.open(filename) as hdulist:
        if len(hdulist) == 1:
            header, scidata = hdulist[0].header, hdulist[0].data
            if (scidata is None or scidata.ndim != 2 or not all(scidata.shape)
                    or 'COEFF0' not in header or 'COEFF1' not in header):
                raise ValueError("LRS primary HDU requires a flux image and COEFF0/COEFF1 header keywords.")
            flux = np.array(scidata[0], copy=True)
            wavelength = 10 ** (float(header['COEFF0']) + np.arange(flux.size) * float(header['COEFF1']))
        elif len(hdulist) == 2:
            wavelength, flux = _spectrum_table_arrays(hdulist[1])
        else:
            raise ValueError(
                f"Unsupported LRS FITS layout: found {len(hdulist)} HDUs; "
                "expected a single primary image or a primary HDU and a spectrum table."
            )

    return wavelength, flux


def parse_mrs_spectrum(filename):
    """
    Parse a medium-resolution spectrum (MRS) FITS file.

    This function reads a LAMOST medium-resolution spectrum FITS file which
    contains multiple spectral bands in separate extensions. It supports
    single-row FLUX/WAVELENGTH vectors and historical DR8/DR9 tables with
    scalar FLUX/LOGLAM pixels in successive rows. LOGLAM is converted to
    wavelength as ``10**LOGLAM`` in double precision. Pixel order, flux values,
    and extension names (including coadds and individual exposures) are kept;
    no radial-velocity or wavelength-frame correction is applied.
    Logarithmic wavelengths must be finite and the resulting wavelengths must
    be finite and positive. Flux quality selection is left to the caller.

    Parameters
    ----------
    filename : str
        Path to the MRS FITS file.

    Returns
    -------
    dict
        Dictionary with extension names as keys. Each value contains
        ``wavelength`` (array in Angstroms) and ``flux`` (spectrum flux array).

    Raises
    ------
    ValueError
        No spectrum extensions are present, or an extension is empty, lacks
        supported columns, has ambiguous wavelength columns, or does not have
        the numeric array shapes described above. Duplicate extension names
        are rejected to avoid silently losing a spectrum. Nonfinite LOGLAM or
        nonfinite/nonpositive wavelengths, including conversion overflow or
        underflow to zero, are rejected with extension and pixel diagnostics.

    Examples
    --------
    >>> data = parse_mrs_spectrum('spec_mrs.fits')  # doctest: +SKIP
    >>> for band_name, band_data in data.items():  # doctest: +SKIP
    ...     print(f"{band_name}: {len(band_data['wavelength'])} pixels")  # doctest: +SKIP
    """
    data = {}
    with fits.open(filename) as hdulist:
        if len(hdulist) < 2:
            raise ValueError(f"{filename}: MRS FITS requires at least one spectrum extension.")
        for i, hdu in enumerate(hdulist[1:], 1):
            extension_name = hdu.header.get('EXTNAME') or f'Extension_{i}'
            try:
                wavelength, flux = _spectrum_table_arrays(hdu, allow_loglam=True)
                invalid = np.flatnonzero(~np.isfinite(wavelength) | (wavelength <= 0))
                if invalid.size:
                    first = invalid[0]
                    raise ValueError(
                        f"Wavelengths must be finite and positive; found {invalid.size} invalid pixels, "
                        f"first at zero-based index {first}: {wavelength[first]!r}."
                    )
            except ValueError as error:
                raise ValueError(f"{filename}: extension {extension_name!r} (HDU {i}): {error}") from error
            if extension_name in data:
                raise ValueError(f"{filename}: duplicate spectrum extension name: {extension_name} (HDU {i}).")
            data[extension_name] = {'wavelength': wavelength, 'flux': flux}
    return data
