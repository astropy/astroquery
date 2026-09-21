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
import os
import re
import warnings
from io import BytesIO, StringIO
from urllib.parse import quote, quote_plus
from xml.etree import ElementTree

# Third party
import astropy.units as u
from astropy.io import ascii, votable
from astropy.io.votable.exceptions import W46
from astropy.table import MaskedColumn, Table
import numpy as np
from requests import HTTPError, Response
from requests.structures import CaseInsensitiveDict

# Local imports
from ._response_utils import response_looks_like_html, sanitize_votable_content
from ._sql import uses_legacy_metadata
from ._utils import (
    _api_error_summary,
    _configured_token_from_env as _configured_token_from_env_base,
    _oauth_redirect_url,
    _strip_optional_quotes,
    _successful_response_error,
)
from ...query import BaseQuery
from ... import log
from ...exceptions import InvalidQueryError, LoginError, RemoteServiceError, TableParseError
from . import conf


__all__ = ['Lamost', 'LamostClass']


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

    def _parse_table_response(self, response, *, verbose=False, column_schema=None):
        table = self._parse_result(response, verbose=verbose, column_schema=column_schema)
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
                values = []
                mask = []
                try:
                    for value in column:
                        missing = value is None or np.ma.is_masked(value)
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
                        mask.append(missing)
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

    def _parse_result(self, response, *, verbose=False, column_schema=None):
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
                table = Table(names=list(schema), meta=table.meta)
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
            # a null sentinel. Astropy can return an ordinary zero for it.
            xml_table = next(node for node in ElementTree.fromstring(content).iter()
                             if node.tag.rsplit('}', 1)[-1] == 'TABLE')
            fields = [node for node in xml_table if node.tag.rsplit('}', 1)[-1] == 'FIELD']
            tabledata = next((node for node in xml_table.iter()
                              if node.tag.rsplit('}', 1)[-1] == 'TABLEDATA'), None)
            if tabledata is not None:
                rows = list(tabledata)
                if (len(fields) != len(table.colnames) or len(rows) != len(table)
                        or any(row.tag.rsplit('}', 1)[-1] != 'TR' or len(row) != len(fields)
                               or any(cell.tag.rsplit('}', 1)[-1] != 'TD' or len(cell) for cell in row)
                               for row in rows)):
                    raise TableParseError('Cannot reliably map LAMOST VOTable TABLEDATA cells to columns.')
                for i, field in enumerate(fields):
                    if field.get('datatype') not in {'short', 'int', 'long', 'unsignedByte'}:
                        continue
                    missing = np.array([not (row[i].text or '').strip() for row in rows], dtype=bool)
                    if not missing.any():
                        continue
                    column = table.columns[i]
                    if field.get('arraysize') not in (None, '1') or column.ndim != 1 or column.dtype.kind not in 'iu':
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
