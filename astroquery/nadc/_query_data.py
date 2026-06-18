# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Internal helpers for NADC Query Data Access OpenAPI modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Literal, Mapping, MutableMapping, Optional, Sequence, Tuple, Union
from urllib.parse import unquote

import astropy.units as u
from astropy.io import ascii
from astropy.io.votable import parse as parse_votable
from astropy.io.votable import parse_single_table
from astropy.table import Table, vstack
from requests import HTTPError

from . import conf as nadc_conf
from ._response_utils import response_looks_like_html, sanitize_votable_content
from ..exceptions import InvalidQueryError, TableParseError
from ..query import BaseQuery
from ..utils import commons


_QUERY_DATA_OPENAPI_PREFIX = "/query/openapi"


def _drop_none(d: MutableMapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _table_from_list_of_dicts(rows: List[Mapping[str, Any]]) -> Table:
    if not rows:
        return Table()
    keys: List[str] = sorted({k for row in rows for k in row.keys()})
    columns = {k: [row.get(k) for row in rows] for k in keys}
    return Table(columns)


def _strip_optional_quotes(value: str) -> str:
    value = str(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _configured_token_from_env(env_var_names: Iterable[str]) -> Optional[str]:
    for env_name in env_var_names:
        env_value = os.environ.get(env_name)
        if env_value:
            token = _strip_optional_quotes(env_value)
            if token:
                return token
    return None


def _preferred_votable_field_name(field: Any) -> Optional[str]:
    name = getattr(field, "name", None)
    if name is not None:
        text = str(name).strip()
        if text:
            return text

    field_id = getattr(field, "ID", None)
    if field_id is not None:
        text = str(field_id).strip()
        if text:
            return text

    return None


def _rename_votable_columns_from_fields(table: Table, votable_table: Any) -> Table:
    fields = list(getattr(votable_table, "fields", ()) or ())
    if not fields or len(fields) != len(table.colnames):
        return table

    taken_names = set(table.colnames)
    rename_pairs = []
    for current_name, field in zip(list(table.colnames), fields):
        preferred_name = _preferred_votable_field_name(field)
        if not preferred_name or preferred_name == current_name:
            continue
        if preferred_name in taken_names:
            continue
        rename_pairs.append((current_name, preferred_name))
        taken_names.remove(current_name)
        taken_names.add(preferred_name)

    for current_name, preferred_name in rename_pairs:
        table.rename_column(current_name, preferred_name)

    return table


def _votable_table_to_astropy_table(votable_table: Any) -> Table:
    try:
        table = votable_table.to_table(use_names_over_ids=True)
    except TypeError as exc:
        if "use_names_over_ids" not in str(exc):
            raise
        table = votable_table.to_table()

    return _rename_votable_columns_from_fields(table, votable_table)


def _parse_first_votable_table(content: bytes) -> Table:
    votable = parse_votable(BytesIO(content))
    for table in votable.iter_tables():
        return _votable_table_to_astropy_table(table)
    raise TableParseError("VOTable document contained no tables.")


def _response_debug_summary(response, *, preview_limit: int = 200) -> str:
    status_code = getattr(response, "status_code", None)
    content_type = ""
    headers = getattr(response, "headers", {}) or {}
    if isinstance(headers, Mapping):
        content_type = str(headers.get("Content-Type") or "")
    url = getattr(response, "url", None)
    text = getattr(response, "text", "") or ""
    preview = " ".join(str(text).split())
    if len(preview) > preview_limit:
        preview = preview[:preview_limit] + " ..."
    return (
        f"status={status_code}, content_type={content_type!r}, "
        f"url={url!r}, preview={preview!r}"
    )


def _response_status_code(response) -> Optional[int]:
    status_code = getattr(response, "status_code", None)
    try:
        return int(status_code) if status_code is not None else None
    except Exception:
        return None


def _response_json_payload(response) -> Optional[Mapping[str, Any]]:
    content_type = (response.headers.get("Content-Type") or "").lower()
    text = getattr(response, "text", "") or ""
    if "application/json" not in content_type and not text.strip().startswith(("{", "[")):
        return None

    try:
        data = response.json()
    except Exception:
        return None

    return data if isinstance(data, Mapping) else None


def _stringify_error_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, Mapping):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return str(value)
    if isinstance(value, (list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def _api_error_summary(response, *, preview_limit: int = 240) -> Optional[str]:
    data = _response_json_payload(response)
    if data is not None:
        label = (
            _stringify_error_value(data.get("error"))
            or _stringify_error_value(data.get("error_code"))
            or "api_error"
        )
        message = (
            _stringify_error_value(data.get("message"))
            or _stringify_error_value(data.get("detail"))
        )
        if label and message:
            return f"{label}: {message}"
        return label or message

    text = (response.text or "").strip()
    if text:
        preview = " ".join(text.split())
        if len(preview) > preview_limit:
            preview = preview[:preview_limit] + " ..."
        return preview

    return None


def _api_error_debug_context(response) -> Optional[str]:
    data = _response_json_payload(response)
    if data is not None:
        method = _stringify_error_value(data.get("method"))
        path = _stringify_error_value(data.get("path"))
        status = _stringify_error_value(data.get("status_code"))

        bits = []
        if method:
            bits.append(method)
        if path:
            bits.append(path)
        if status:
            bits.append(f"status={status}")
        if bits:
            return " ".join(bits)

    return _response_debug_summary(response)


def _http_error_message(response, *, error_label: str, debug: bool = False) -> str:
    status_code = _response_status_code(response)
    detail = _api_error_summary(response)
    prefix = error_label
    if status_code is not None:
        prefix += f" ({status_code})"

    message = f"{prefix}: {detail}" if detail else prefix
    if debug:
        context = _api_error_debug_context(response)
        if context:
            message += f" [{context}]"
    return message


def _normalize_catalog_name(value: Any) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    return str(value).strip().lower()


# -----------------------------------------------------------------------
# ColumnConstraint – typed factory for column_constraints payloads
# -----------------------------------------------------------------------

#: Allowed operation names for column constraints.
ConstraintOperation = Literal[
    "equal", "notequal",
    "less", "lessequal",
    "greater", "greaterequal",
    "between",
    "contains",
    "in",
]


@dataclass(frozen=True)
class ColumnConstraint:
    """A single column-level filter for catalog queries.

    Instead of building raw dicts, use factory class methods such as
    `ColumnConstraint.equal("year", "1960")` for validation and clearer
    examples.

    Parameters
    ----------
    column_name : str
        Column name to filter on (e.g. ``"year"``, ``"observat"``).
    operation : str
        One of ``equal``, ``notequal``, ``less``, ``lessequal``, ``greater``,
        ``greaterequal``, ``between``, ``contains``, ``in``.
    constraint : str or None
        Value for single-value operations (``equal``, ``notequal``, etc.).
    min : float or None
        Lower bound for ``between``.
    max : float or None
        Upper bound for ``between``.
    textarea : str or None
        Newline-separated values for the ``in`` operation.

    Examples
    --------
    >>> from astroquery.nadc import ColumnConstraint
    >>> cc = ColumnConstraint.equal("observat", "Naoc")
    >>> cc.to_dict()
    {'column_name': 'observat', 'operation': 'equal', 'constraint': 'Naoc'}
    >>> cc2 = ColumnConstraint.between("year", 1950, 1970)
    >>> cc2.to_dict()
    {'column_name': 'year', 'operation': 'between', 'min': 1950, 'max': 1970}
    """

    column_name: str
    operation: ConstraintOperation
    constraint: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    textarea: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the constraint to the API wire format.

        Returns
        -------
        dict
            Dictionary accepted by the Query Data ``column_constraints``
            request field.
        """
        d: Dict[str, Any] = {
            "column_name": self.column_name,
            "operation": self.operation,
        }
        if self.constraint is not None:
            d["constraint"] = self.constraint
        if self.min is not None:
            d["min"] = self.min
        if self.max is not None:
            d["max"] = self.max
        if self.textarea is not None:
            d["textarea"] = self.textarea
        return d

    # -- factory class methods -----------------------------------------

    @classmethod
    def equal(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create an equality constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Required column value.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name == value``.
        """
        return cls(column_name=column_name, operation="equal", constraint=str(value))

    @classmethod
    def notequal(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create an inequality constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Disallowed column value.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name != value``.
        """
        return cls(column_name=column_name, operation="notequal", constraint=str(value))

    @classmethod
    def less(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create a less-than constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Exclusive upper bound.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name < value``.
        """
        return cls(column_name=column_name, operation="less", constraint=str(value))

    @classmethod
    def lessequal(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create a less-than-or-equal constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Inclusive upper bound.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name <= value``.
        """
        return cls(column_name=column_name, operation="lessequal", constraint=str(value))

    @classmethod
    def greater(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create a greater-than constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Exclusive lower bound.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name > value``.
        """
        return cls(column_name=column_name, operation="greater", constraint=str(value))

    @classmethod
    def greaterequal(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create a greater-than-or-equal constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Inclusive lower bound.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name >= value``.
        """
        return cls(column_name=column_name, operation="greaterequal", constraint=str(value))

    @classmethod
    def between(cls, column_name: str, min_val: float, max_val: float) -> "ColumnConstraint":
        """Create an inclusive range constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        min_val : float
            Inclusive lower bound.
        max_val : float
            Inclusive upper bound.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``min_val <= column_name <= max_val``.
        """
        return cls(column_name=column_name, operation="between", min=min_val, max=max_val)

    @classmethod
    def contains(cls, column_name: str, value: str) -> "ColumnConstraint":
        """Create a substring-matching constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        value : object
            Substring that must occur in the column value.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name LIKE '%value%'``.
        """
        return cls(column_name=column_name, operation="contains", constraint=str(value))

    @classmethod
    def in_(cls, column_name: str, values: Iterable[str]) -> "ColumnConstraint":
        """Create a membership constraint.

        Parameters
        ----------
        column_name : str
            Column to constrain.
        values : iterable
            Accepted column values.

        Returns
        -------
        ColumnConstraint
            Constraint representing ``column_name IN values``.
        """
        textarea = "\n".join(str(v) for v in values)
        return cls(column_name=column_name, operation="in", textarea=textarea)


def _append_equal_constraint(
    constraints: List[ColumnConstraint],
    column_name: str,
    value: Optional[Any],
) -> List[ColumnConstraint]:
    if value is not None:
        constraints.append(ColumnConstraint.equal(column_name, value))
    return constraints


def _append_contains_constraint(
    constraints: List[ColumnConstraint],
    column_name: str,
    value: Optional[Any],
) -> List[ColumnConstraint]:
    if value is not None:
        constraints.append(ColumnConstraint.contains(column_name, value))
    return constraints


def _append_range_constraint(
    constraints: List[ColumnConstraint],
    column_name: str,
    value_range: Optional[Sequence[Any]],
) -> List[ColumnConstraint]:
    if value_range is None:
        return constraints

    if not isinstance(value_range, Sequence) or isinstance(value_range, (str, bytes)) or len(value_range) != 2:
        raise InvalidQueryError(f"{column_name} range must be a 2-item sequence.")

    min_value, max_value = value_range
    constraints.append(ColumnConstraint.between(column_name, min_value, max_value))
    return constraints


def _append_max_constraint(
    constraints: List[ColumnConstraint],
    column_name: str,
    max_value: Optional[Any],
) -> List[ColumnConstraint]:
    if max_value is not None:
        constraints.append(ColumnConstraint.lessequal(column_name, max_value))
    return constraints


def _append_min_constraint(
    constraints: List[ColumnConstraint],
    column_name: str,
    min_value: Optional[Any],
) -> List[ColumnConstraint]:
    if min_value is not None:
        constraints.append(ColumnConstraint.greaterequal(column_name, min_value))
    return constraints


class QueryDataBaseQuery(BaseQuery):
    """
    Internal base class for NADC Query Data Access OpenAPI modules.
    """

    CONF = None
    TOKEN_ENV_VARS: Tuple[str, ...] = ()
    ERROR_LABEL = "NADC Query Data API error"
    _CATALOG_NAME_COLUMNS = ("catname", "catalog", "name", "shortname", "dbname")
    _TABLE_NAME_COLUMNS = ("tblname", "table_name", "table", "name")
    _COLUMN_NAME_COLUMNS = ("colname", "column_name", "column", "name")
    _DATATYPE_COLUMNS = ("datatype", "data_type", "type", "dbtype", "dtype")
    _UNIT_COLUMNS = ("unit", "units")
    _UCD_COLUMNS = ("ucd",)
    _DESCRIPTION_COLUMNS = ("description", "desc", "comment", "remarks")
    _RECORDS_COLUMNS = ("records", "rows", "row_count", "nrows")

    def __init__(
        self,
        *,
        catalog: Optional[str] = None,
        token: Optional[str] = None,
        auth_method: Optional[str] = None,
        debug: Optional[bool] = None,
    ):
        super().__init__()
        self.URL = self._config_value("server", getattr(self.__class__, "URL", None))
        self.TIMEOUT = self._config_value("timeout", getattr(self.__class__, "TIMEOUT", None))
        self.catalog = catalog or self._config_value("catalog", None)
        if token is not None:
            self.token = _strip_optional_quotes(token) or None
        else:
            configured_token = _strip_optional_quotes(self._config_value("token", "") or "")
            self.token = (
                configured_token
                or self._shared_config_token()
                or self._configured_token_from_environment()
                or None
            )
        self.auth_method = (auth_method or self._config_value("auth_method", "query") or "query").lower()
        self.debug = bool(self._config_value("debug", False)) if debug is None else bool(debug)

        if self.auth_method not in {"query", "bearer"}:
            raise ValueError('auth_method must be "query" or "bearer".')

    @staticmethod
    def _parse_coordinates(value):
        return commons.parse_coordinates(value)

    def _config(self):
        if self.CONF is None:
            raise NotImplementedError("QueryDataBaseQuery subclasses must define CONF.")
        return self.CONF

    def _config_value(self, name: str, default: Any = None):
        return getattr(self._config(), name, default)

    def _config_list_value(self, name: str) -> List[str]:
        value = self._config_value(name, None)
        if value is None:
            return []
        if isinstance(value, str):
            raw_values = [part.strip() for part in value.split(",")]
        else:
            try:
                raw_values = list(value)
            except TypeError:
                raw_values = [value]

        values = []
        for item in raw_values:
            text = str(item).strip()
            if text:
                values.append(text)
        return values

    def _configured_token_from_environment(self) -> Optional[str]:
        return _configured_token_from_env(self.TOKEN_ENV_VARS)

    def _shared_config_token(self) -> Optional[str]:
        configured_token = _strip_optional_quotes(getattr(nadc_conf, "token", "") or "")
        return configured_token or None

    def _default_row_limit(self) -> int:
        return int(self._config_value("row_limit", 10000))

    def _default_pos_group(self) -> Optional[str]:
        value = self._config_value("pos_group", None)
        return str(value).strip() if value else None

    def _supported_catalogs(self) -> List[str]:
        return self._config_list_value("supported_catalogs")

    def _safe_cache(self, cache: bool, *, stream: bool = False) -> bool:
        if stream:
            return False
        if self.token:
            return False
        return cache

    def _service_url(self, path: str) -> str:
        return f"{str(self.URL).rstrip('/')}/{path.lstrip('/')}"

    def _openapi_path(self, path: str) -> str:
        return f"{_QUERY_DATA_OPENAPI_PREFIX}/{path.lstrip('/')}"

    def _openapi_url(self, path: str) -> str:
        return self._service_url(self._openapi_path(path))

    def _auth_params_headers(
        self,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        out_params = dict(params or {})
        out_headers = dict(headers or {})

        if self.token:
            if self.auth_method == "bearer":
                out_headers.setdefault("Authorization", f"Bearer {self.token}")
            else:
                out_params.setdefault("token", self.token)

        return out_params, out_headers

    def _request_raise(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
        timeout: Optional[int] = None,
        cache: bool = True,
        stream: bool = False,
    ):
        req_params, req_headers = self._auth_params_headers(params=params, headers=headers)
        response = self._request(
            method,
            url,
            params=req_params or None,
            headers=req_headers or None,
            json=json,
            timeout=timeout or self.TIMEOUT,
            cache=self._safe_cache(cache, stream=stream),
            stream=stream,
        )
        try:
            response.raise_for_status()
        except HTTPError as exc:
            raise HTTPError(
                _http_error_message(response, error_label=self.ERROR_LABEL, debug=self.debug),
                response=response,
            ) from exc

        if getattr(response, "status_code", 200) >= 400:
            raise HTTPError(
                _http_error_message(response, error_label=self.ERROR_LABEL, debug=self.debug),
                response=response,
            )

        return response

    def _parse_table_response(self, response, *, verbose: bool = False):
        table = self._parse_result(response, verbose=verbose)
        self.table = table
        return table

    def _catalog_name_column(self, table: Table) -> Optional[str]:
        for colname in self._CATALOG_NAME_COLUMNS:
            if colname in table.colnames:
                return colname
        return None

    @staticmethod
    def _truthy_catalog_value(value: Any) -> bool:
        if value is None:
            return False
        mask = getattr(value, "mask", False)
        if isinstance(mask, (bool, int)) and bool(mask):
            return False
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "t", "yes", "y"}
        return bool(value)

    def _filter_supported_catalogs(self, table: Table) -> Table:
        supported_catalogs = self._supported_catalogs()
        if not supported_catalogs or len(table) == 0:
            self.table = table
            return table

        catalog_column = self._catalog_name_column(table)
        if catalog_column is None:
            self.table = table
            return table

        supported = {_normalize_catalog_name(value) for value in supported_catalogs}
        mask = [_normalize_catalog_name(value) in supported for value in table[catalog_column]]
        filtered = table[mask]
        self.table = filtered
        return filtered

    def _filter_queryable_catalogs(self, table: Table) -> Table:
        if len(table) == 0:
            self.table = table
            return table

        if "queryable" in table.colnames:
            capability_columns = ("queryable",)
        else:
            capability_columns = tuple(
                colname for colname in ("catalog_query_supported", "table_query_supported")
                if colname in table.colnames
            )

        if not capability_columns:
            self.table = table
            return table

        mask = [
            any(self._truthy_catalog_value(table[colname][row_index]) for colname in capability_columns)
            for row_index in range(len(table))
        ]
        filtered = table[mask]
        self.table = filtered
        return filtered

    def _table_name_column(self, table: Table) -> Optional[str]:
        for colname in self._TABLE_NAME_COLUMNS:
            if colname in table.colnames:
                return colname
        return None

    @staticmethod
    def _is_blank_schema_value(value: Any) -> bool:
        if value is None:
            return True
        mask = getattr(value, "mask", False)
        if isinstance(mask, (bool, int)) and bool(mask):
            return True
        return str(value).strip() in {"", "--"}

    def _first_schema_value(
        self,
        table: Table,
        row_index: int,
        candidates: Iterable[str],
        *,
        default: Any = None,
    ) -> Any:
        for colname in candidates:
            if colname not in table.colnames:
                continue
            value = table[colname][row_index]
            if not self._is_blank_schema_value(value):
                return value
        return default

    def _schema_table_name(self, tables: Table, row_index: int) -> str:
        table_name = self._first_schema_value(tables, row_index, self._TABLE_NAME_COLUMNS)
        if table_name is None:
            raise InvalidQueryError(
                "Cannot determine table name from catalog metadata response."
            )
        return str(table_name)

    def list_schema(
        self,
        *,
        catalog: Optional[str] = None,
        cache: bool = True,
        verbose: bool = False,
    ) -> Table:
        """List all tables and columns for a Query Data catalog.

        Parameters
        ----------
        catalog : str, optional
            Catalog name. Defaults to this client's configured catalog.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table
            Flattened schema table with one row per catalog column.
        """
        catname = catalog or self.catalog
        tables = self.list_tables(catalog=catalog, cache=cache, verbose=verbose)
        table_names = [self._schema_table_name(tables, index) for index in range(len(tables))]
        rows: List[Dict[str, Any]] = []

        for table_index, table_name in enumerate(table_names):
            table_description = self._first_schema_value(
                tables,
                table_index,
                self._DESCRIPTION_COLUMNS,
            )
            table_records = self._first_schema_value(
                tables,
                table_index,
                self._RECORDS_COLUMNS,
            )
            columns = self.list_columns(
                table_name,
                catalog=catalog,
                cache=cache,
                verbose=verbose,
            )
            if len(columns) == 0:
                rows.append(
                    {
                        "catalog": catname,
                        "table": table_name,
                        "column": None,
                        "datatype": None,
                        "unit": None,
                        "ucd": None,
                        "description": None,
                        "table_description": table_description,
                        "table_records": table_records,
                    }
                )
                continue

            for column_index in range(len(columns)):
                rows.append(
                    {
                        "catalog": catname,
                        "table": table_name,
                        "column": self._first_schema_value(
                            columns,
                            column_index,
                            self._COLUMN_NAME_COLUMNS,
                        ),
                        "datatype": self._first_schema_value(
                            columns,
                            column_index,
                            self._DATATYPE_COLUMNS,
                        ),
                        "unit": self._first_schema_value(
                            columns,
                            column_index,
                            self._UNIT_COLUMNS,
                        ),
                        "ucd": self._first_schema_value(
                            columns,
                            column_index,
                            self._UCD_COLUMNS,
                        ),
                        "description": self._first_schema_value(
                            columns,
                            column_index,
                            self._DESCRIPTION_COLUMNS,
                        ),
                        "table_description": table_description,
                        "table_records": table_records,
                    }
                )

        schema = _table_from_list_of_dicts(rows)
        schema.meta["catalog"] = catname
        schema.meta["tables"] = table_names
        self.table = schema
        return schema

    def _resolve_single_table(self, *, catalog: Optional[str] = None, cache: bool = True) -> str:
        """Auto-resolve table name when catalog has exactly one table."""
        tables = self.list_tables(catalog=catalog, cache=cache)
        if len(tables) == 0:
            raise InvalidQueryError(
                "Cannot auto-detect table: catalog has no tables. "
                "Specify the `table` parameter explicitly."
            )
        if len(tables) == 1:
            col = self._table_name_column(tables)
            if col is not None:
                return str(tables[col][0])
        if len(tables) > 1:
            col = self._table_name_column(tables)
            names = list(tables[col]) if col else []
            raise InvalidQueryError(
                f"Catalog has {len(tables)} tables ({names}); "
                "specify the `table` parameter explicitly."
            )
        raise InvalidQueryError("Cannot determine table name from the response.")

    def _resolve_table_for_request(
        self,
        table: Optional[str],
        *,
        catalog: Optional[str] = None,
        cache: bool = True,
        get_query_payload: bool = False,
    ) -> str:
        if table is None and get_query_payload:
            raise InvalidQueryError(
                "`table` is required when get_query_payload=True; "
                "auto-detecting a table requires a service request."
            )
        return table or self._resolve_single_table(catalog=catalog, cache=cache)

    # -----------------------------
    # Service discovery / metadata
    # -----------------------------

    def _request_ping(self, *, get_query_payload: bool = False, cache: bool = True):
        url = self._openapi_url("ping")
        if get_query_payload:
            return {"method": "GET", "url": url}
        return self._request_raise("GET", url, cache=cache)

    def ping(self, *, get_query_payload: bool = False, cache: bool = True, verbose: bool = False):
        response = self._request_ping(get_query_payload=get_query_payload, cache=cache)
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_list_catalogs(self, *, get_query_payload: bool = False, cache: bool = True):
        url = self._openapi_url("get_catalogs")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def list_catalogs(
        self,
        *,
        queryable_only: bool = True,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        """List catalogs surfaced by the current module.

        Parameters
        ----------
        queryable_only : bool, optional
            Return only catalogs whose discovery metadata declares query
            support. This uses the ``queryable`` field when available,
            otherwise it falls back to ``catalog_query_supported`` or
            ``table_query_supported``. Default is `True`.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Catalog table, or the request payload when
            ``get_query_payload=True``.
        """
        if get_query_payload:
            return self._request_list_catalogs(get_query_payload=True, cache=cache)

        response = self._request_list_catalogs(cache=cache)
        table = self._parse_table_response(response, verbose=verbose)
        table = self._filter_supported_catalogs(table)
        if queryable_only:
            return self._filter_queryable_catalogs(table)
        return table

    def _request_catalog_metadata(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def get_catalog_metadata(
        self,
        *,
        catalog: Optional[str] = None,
        include_capabilities: bool = True,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        """Return service metadata for a single Query Data catalog.

        The response is returned as a mapping because catalog metadata can
        include nested service capabilities such as file-download products.
        When ``include_capabilities`` is `True`, the returned mapping includes
        a ``capabilities_summary`` key with normalized capability flags.
        """
        del verbose
        response = self._request_catalog_metadata(
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response

        data = _response_json_payload(response)
        if data is None:
            raise TableParseError("Catalog metadata endpoint did not return JSON.")
        metadata = dict(data)
        if include_capabilities:
            metadata["capabilities_summary"] = self._normalized_catalog_capabilities(
                metadata,
                catalog=catalog,
            )
        return metadata

    @staticmethod
    def _metadata_mapping(value: Any) -> Mapping[str, Any]:
        return value if isinstance(value, Mapping) else {}

    def _metadata_capability(
        self,
        metadata: Mapping[str, Any],
        top_key: str,
        capability_key: str,
        *,
        nested_mapping: Optional[Mapping[str, Any]] = None,
        nested_key: Optional[str] = None,
    ) -> bool:
        if top_key in metadata:
            return self._truthy_catalog_value(metadata.get(top_key))

        capabilities = self._metadata_mapping(metadata.get("capabilities"))
        if capability_key in capabilities:
            return self._truthy_catalog_value(capabilities.get(capability_key))

        if nested_mapping is not None and nested_key is not None and nested_key in nested_mapping:
            return self._truthy_catalog_value(nested_mapping.get(nested_key))

        return False

    def _normalized_catalog_capabilities(
        self,
        metadata: Mapping[str, Any],
        catalog: Optional[str] = None,
    ) -> Dict[str, Any]:
        file_download = self._metadata_mapping(metadata.get("file_download"))
        query_status = self._metadata_mapping(metadata.get("query_status"))
        categories = file_download.get("categories") or []

        return {
            "catname": metadata.get("catname", catalog or self.catalog),
            "queryable": self._metadata_capability(metadata, "queryable", "queryable"),
            "catalog_query_supported": self._metadata_capability(
                metadata, "catalog_query_supported", "catalog_query"
            ),
            "table_query_supported": self._metadata_capability(
                metadata, "table_query_supported", "table_query"
            ),
            "table_metadata_available": self._metadata_capability(
                metadata, "table_metadata_available", "table_metadata_available"
            ),
            "conesearch_supported": self._metadata_capability(metadata, "conesearch_supported", "conesearch"),
            "siap_supported": self._metadata_capability(metadata, "siap_supported", "siap"),
            "ssap_supported": self._metadata_capability(metadata, "ssap_supported", "ssap"),
            "docs_supported": self._metadata_capability(metadata, "docs_supported", "docs"),
            "file_download_supported": self._metadata_capability(
                metadata,
                "file_download_supported",
                "file_download",
                nested_mapping=file_download,
                nested_key="supported",
            ),
            "file_download_categories": list(categories) if isinstance(categories, list) else [],
            "query_status_code": query_status.get("code"),
            "query_status_reason": query_status.get("reason"),
        }

    def _request_list_tables(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/tables")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def list_tables(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        response = self._request_list_tables(
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_list_columns(
        self,
        table: str,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/tables/{table}/columns")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def list_columns(
        self,
        table: Optional[str] = None,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        table = self._resolve_table_for_request(
            table,
            catalog=catalog,
            cache=cache,
            get_query_payload=get_query_payload,
        )
        response = self._request_list_columns(
            table,
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_coordinate_groups(
        self,
        table: str,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/tables/{table}/coordinate_groups")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def _parse_coordinate_groups_response(self, response) -> Table:
        data = _response_json_payload(response)
        if data is None:
            raise TableParseError("Coordinate-group discovery did not return JSON.")

        groups = data.get("groups")
        if groups is None:
            groups = []
        if not isinstance(groups, list):
            raise TableParseError("Coordinate-group discovery JSON did not contain a valid 'groups' array.")

        table = _table_from_list_of_dicts([
            group for group in groups if isinstance(group, Mapping)
        ])
        table.meta.update(
            {
                "default_group_id": data.get("default_group_id"),
                "status": data.get("status"),
                "requires_selection": data.get("requires_selection"),
                "spatial_query_supported": data.get("spatial_query_supported"),
                "metadata_quality": data.get("metadata_quality"),
                "warnings": list(data.get("warnings") or []),
            }
        )
        self.table = table
        return table

    def list_coordinate_groups(
        self,
        table: Optional[str] = None,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        del verbose
        table = self._resolve_table_for_request(
            table,
            catalog=catalog,
            cache=cache,
            get_query_payload=get_query_payload,
        )
        response = self._request_coordinate_groups(
            table,
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_coordinate_groups_response(response)

    def _request_table_links(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/table_links")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def _parse_table_links_response(self, response) -> Table:
        data = _response_json_payload(response)
        if data is None:
            raise TableParseError("Table-links discovery did not return JSON.")

        links = data.get("links")
        if links is None:
            links = []
        if not isinstance(links, list):
            raise TableParseError("Table-links JSON did not contain a valid 'links' array.")

        table = _table_from_list_of_dicts([
            link for link in links if isinstance(link, Mapping)
        ])
        table.meta["is_single_table"] = data.get("is_single_table")
        self.table = table
        return table

    def list_table_links(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        del verbose
        response = self._request_table_links(
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_links_response(response)

    def _request_list_docs(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/docs")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def list_docs(
        self,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        del verbose
        response = self._request_list_docs(
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response

        data = _response_json_payload(response)
        if data is None:
            raise TableParseError("Catalog docs listing did not return JSON.")

        rows = data.get("rows") or []
        if not isinstance(rows, list):
            raise TableParseError("Catalog docs JSON did not contain a valid 'rows' array.")

        table = _table_from_list_of_dicts([row for row in rows if isinstance(row, Mapping)])
        table.meta["total"] = data.get("total")
        self.table = table
        return table

    def _request_get_doc(
        self,
        docid: str,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/docs/{docid}")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def get_doc(
        self,
        docid: str,
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        del verbose
        response = self._request_get_doc(
            docid,
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response

        data = _response_json_payload(response)
        if data is None:
            raise TableParseError("Catalog document endpoint did not return JSON.")
        return dict(data)

    # -----------------------------
    # VO protocol helpers
    # -----------------------------

    def _request_conesearch(
        self,
        ra: float,
        dec: float,
        radius: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        verb: Optional[int] = None,
        output_format: str = "votable",
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"vo/{catname}/conesearch")

        output_format = str(output_format).lower()
        if output_format not in {"txt", "csv", "json", "votable"}:
            raise InvalidQueryError(
                "conesearch output_format must be one of: txt, csv, json, votable."
            )

        if isinstance(radius, u.Quantity):
            sr_deg = float(radius.to_value(u.deg))
        else:
            sr_deg = float(radius) * u.arcsec.to(u.deg)

        params: Dict[str, Any] = _drop_none(
            {
                "RA": float(ra),
                "DEC": float(dec),
                "SR": sr_deg,
                "VERB": verb,
                "output.fmt": output_format,
            }
        )

        if get_query_payload:
            params, headers = self._auth_params_headers(params=params)
            return {"method": "GET", "url": url, "params": params, "headers": headers}

        return self._request_raise("GET", url, params=params, cache=cache)

    def conesearch(
        self,
        ra: float,
        dec: float,
        radius: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        verb: Optional[int] = None,
        output_format: str = "votable",
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        response = self._request_conesearch(
            ra,
            dec,
            radius,
            catalog=catalog,
            verb=verb,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _request_table_conesearch(
        self,
        ra: float,
        dec: float,
        radius: Union[u.Quantity, float],
        *,
        table: str,
        catalog: Optional[str] = None,
        coordinate_group: Optional[str] = None,
        verb: Optional[int] = None,
        output_format: str = "votable",
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"catalogs/{catname}/tables/{table}/vo/conesearch")

        output_format = str(output_format).lower()
        if output_format not in {"txt", "csv", "json", "votable"}:
            raise InvalidQueryError(
                "table conesearch output_format must be one of: txt, csv, json, votable."
            )

        if isinstance(radius, u.Quantity):
            sr_deg = float(radius.to_value(u.deg))
        else:
            sr_deg = float(radius) * u.arcsec.to(u.deg)

        params: Dict[str, Any] = _drop_none(
            {
                "RA": float(ra),
                "DEC": float(dec),
                "SR": sr_deg,
                "VERB": verb,
                "output.fmt": output_format,
                "coordinate_group": coordinate_group,
            }
        )

        if get_query_payload:
            params, headers = self._auth_params_headers(params=params)
            return {"method": "GET", "url": url, "params": params, "headers": headers}

        return self._request_raise("GET", url, params=params, cache=cache)

    def query_table_cone(
        self,
        coordinates,
        radius: Union[u.Quantity, float],
        *,
        table: Optional[str] = None,
        catalog: Optional[str] = None,
        coordinate_group: Optional[str] = None,
        output_format: str = "votable",
        verb: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        table = self._resolve_table_for_request(
            table,
            catalog=catalog,
            cache=cache,
            get_query_payload=get_query_payload,
        )

        c = self._parse_coordinates(coordinates)
        response = self._request_table_conesearch(
            float(c.icrs.ra.to_value(u.deg)),
            float(c.icrs.dec.to_value(u.deg)),
            radius,
            table=table,
            catalog=catalog,
            coordinate_group=coordinate_group,
            verb=verb,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def query_table_rectangle(
        self,
        ra_min: Union[u.Quantity, float],
        ra_max: Union[u.Quantity, float],
        dec_min: Union[u.Quantity, float],
        dec_max: Union[u.Quantity, float],
        *,
        table: Optional[str] = None,
        catalog: Optional[str] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        return self.query_table(
            table=table,
            catalog=catalog,
            pos=self._build_rectangle_pos(ra_min, ra_max, dec_min, dec_max),
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_table_proximity(
        self,
        positions: Union[str, Iterable[Any]],
        *,
        table: Optional[str] = None,
        catalog: Optional[str] = None,
        default_radius: Optional[Union[u.Quantity, float]] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        return self.query_table(
            table=table,
            catalog=catalog,
            pos=self._build_proximity_pos(
                positions,
                default_radius=default_radius,
                nearest_only=nearest_only,
            ),
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def _request_siap(
        self,
        ra: float,
        dec: float,
        size: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        output_format: str = "votable",
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        url = self._openapi_url(f"vo/{catname}/siap")
        fmt = self._normalize_output_format(output_format)
        size_deg = self._to_degree(size, name="size")

        params: Dict[str, Any] = {
            "POS": f"{float(ra)},{float(dec)}",
            "SIZE": size_deg,
            "format": fmt,
        }

        if get_query_payload:
            params, headers = self._auth_params_headers(params=params)
            return {"method": "GET", "url": url, "params": params, "headers": headers}

        return self._request_raise("GET", url, params=params, cache=cache)

    def query_siap(
        self,
        coordinates,
        size: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        output_format: str = "votable",
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        c = self._parse_coordinates(coordinates)
        response = self._request_siap(
            float(c.icrs.ra.to_value(u.deg)),
            float(c.icrs.dec.to_value(u.deg)),
            size,
            catalog=catalog,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    # -----------------------------
    # Query submission + results
    # -----------------------------

    def _submit_query_response(
        self,
        payload: Mapping[str, Any],
        *,
        catalog: Optional[str] = None,
        table: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        catname = catalog or self.catalog
        if table is not None:
            url = self._openapi_url(f"catalogs/{catname}/tables/{table}/query")
        else:
            url = self._openapi_url(f"catalogs/{catname}/query")
        json_payload = dict(payload)
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "POST", "url": url, "params": params, "headers": headers, "json": json_payload}
        return self._request_raise("POST", url, json=json_payload, cache=cache)

    def submit_query(
        self,
        payload: Mapping[str, Any],
        *,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        response = self._submit_query_response(
            payload,
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_submit_response(response, verbose=verbose)

    def submit_table_query(
        self,
        payload: Mapping[str, Any],
        *,
        table: Optional[str] = None,
        catalog: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        table = self._resolve_table_for_request(
            table,
            catalog=catalog,
            cache=cache,
            get_query_payload=get_query_payload,
        )
        response = self._submit_query_response(
            payload,
            catalog=catalog,
            table=table,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_submit_response(response, verbose=verbose)

    def _get_results_response(
        self,
        sqlid: Union[int, str],
        *,
        fmt: str = "votable",
        page: Optional[int] = 1,
        rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        if max_rows is not None:
            if rows is not None and rows != max_rows:
                raise InvalidQueryError("Provide either `rows` or `max_rows`, not both with different values.")
            rows = max_rows

        fmt = str(fmt).lower().lstrip(".")
        url = self._openapi_url(f"sqlid/{sqlid}/results.{fmt}")
        params: Dict[str, Any] = _drop_none(
            {
                "page": page,
                "rows": rows,
                "sort": sort,
                "order": order,
            }
        )
        if get_query_payload:
            params, headers = self._auth_params_headers(params=params)
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, params=params, cache=cache)

    def get_results(
        self,
        sqlid: Union[int, str],
        *,
        fmt: str = "votable",
        page: Optional[int] = 1,
        rows: Optional[int] = None,
        max_rows: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        response = self._get_results_response(
            sqlid,
            fmt=fmt,
            page=page,
            rows=rows,
            max_rows=max_rows,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _get_count_response(
        self,
        sqlid: Union[int, str],
        *,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        url = self._openapi_url(f"sqlid/{sqlid}/count")
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {"method": "GET", "url": url, "params": params, "headers": headers}
        return self._request_raise("GET", url, cache=cache)

    def get_count(
        self,
        sqlid: Union[int, str],
        *,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        response = self._get_count_response(
            sqlid,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def _filename_from_response_headers(self, response, *, default_name: str) -> str:
        content_disp = response.headers.get("Content-Disposition") or ""
        match = re.search(
            r"filename\*?=(?:UTF-8''|\")?([^\";]+)",
            content_disp,
            re.IGNORECASE,
        )
        if not match:
            return default_name

        filename = unquote(match.group(1)).strip().strip("\"'")
        filename = os.path.basename(filename)
        return filename or default_name

    def _resolve_download_path(
        self,
        response,
        *,
        out_path: Optional[Union[str, os.PathLike[str]]],
        default_name: str,
    ) -> Path:
        resolved_name = self._filename_from_response_headers(response, default_name=default_name)

        if out_path is None:
            return Path(self.cache_location) / "downloads" / resolved_name

        path = Path(out_path)
        raw_path = os.fspath(out_path)
        if raw_path.endswith(os.sep) or (path.exists() and path.is_dir()):
            return path / resolved_name
        return path

    def _write_stream_response(
        self,
        response,
        destination: Path,
        *,
        overwrite: bool = True,
    ) -> str:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not overwrite:
            return str(destination.resolve())

        temp_path = destination.parent / f"{destination.name}.tmp"
        with open(temp_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)

        if destination.exists():
            destination.unlink()
        temp_path.replace(destination)
        return str(destination.resolve())

    def _endpoint_from_metadata(
        self,
        endpoint: Optional[str],
        *,
        default_path: str,
    ) -> str:
        if not endpoint:
            return self._service_url(default_path)
        endpoint_text = str(endpoint)
        if re.match(r"^https?://", endpoint_text):
            return endpoint_text
        return self._service_url(endpoint_text)

    def _file_download_metadata(
        self,
        *,
        catalog: Optional[str] = None,
        cache: bool = True,
    ) -> Mapping[str, Any]:
        catname = catalog or self.catalog
        metadata = self.get_catalog_metadata(catalog=catname, cache=cache)
        file_download = metadata.get("file_download")
        if not isinstance(file_download, Mapping):
            raise InvalidQueryError(
                f"Catalog {catname!r} does not declare file-download metadata."
            )
        if file_download.get("supported") is not True:
            raise InvalidQueryError(f"Catalog {catname!r} does not support file download.")
        return file_download

    @staticmethod
    def _normalize_categories(categories: Optional[Iterable[str]]) -> Optional[List[str]]:
        if categories is None:
            return None
        if isinstance(categories, (str, bytes)):
            values = [str(categories)]
        else:
            values = [str(value) for value in categories]
        values = [value.strip() for value in values if value.strip()]
        if not values:
            raise InvalidQueryError("categories must not be empty when provided.")
        return values

    @staticmethod
    def _metadata_categories(file_download: Mapping[str, Any]) -> Optional[List[str]]:
        categories = file_download.get("categories")
        if categories is None:
            return None
        if isinstance(categories, (str, bytes)):
            return [str(categories)]
        try:
            return [str(value) for value in categories]
        except TypeError:
            return None

    @staticmethod
    def _download_id_column_candidates(file_download: Optional[Mapping[str, Any]]) -> List[str]:
        candidates: List[str] = []
        id_source = (file_download or {}).get("id_source")
        if isinstance(id_source, Mapping):
            for key in ("result_field", "column", "parameter"):
                value = id_source.get(key)
                if value is not None:
                    text = str(value).strip()
                    if text:
                        candidates.append(text)
        candidates.append("id")

        unique_candidates: List[str] = []
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            unique_candidates.append(candidate)
        return unique_candidates

    @staticmethod
    def _download_id_parameter(file_download: Optional[Mapping[str, Any]]) -> str:
        id_source = (file_download or {}).get("id_source")
        if isinstance(id_source, Mapping):
            parameter = id_source.get("parameter")
            if parameter is not None:
                text = str(parameter).strip()
                if text:
                    return text
        return "id"

    def _validate_download_categories(
        self,
        categories: Optional[Iterable[str]],
        *,
        catalog: Optional[str] = None,
        file_download: Optional[Mapping[str, Any]] = None,
    ) -> Optional[List[str]]:
        normalized = self._normalize_categories(categories)
        if normalized is None:
            return None

        metadata = file_download or self._file_download_metadata(catalog=catalog)
        supported = self._metadata_categories(metadata)
        if supported is None:
            return normalized

        supported_set = set(supported)
        unsupported = [value for value in normalized if value not in supported_set]
        if unsupported:
            catname = catalog or self.catalog
            raise InvalidQueryError(
                "Unsupported file category for catalog {0!r}: {1}. "
                "Supported categories are: {2}.".format(
                    catname,
                    ", ".join(unsupported),
                    ", ".join(supported),
                )
            )
        return normalized

    def _file_download_request_config(
        self,
        *,
        catalog: Optional[str] = None,
        category: Optional[str] = None,
        cache: bool = True,
    ) -> Tuple[str, Dict[str, Any], str]:
        catname = catalog or self.catalog
        file_download = self._file_download_metadata(catalog=catname, cache=cache)

        query_by_category = file_download.get("single_file_query_by_category") or {}
        if query_by_category is not None and not isinstance(query_by_category, Mapping):
            raise TableParseError(
                "Catalog file-download metadata field "
                "'single_file_query_by_category' is not a mapping."
            )

        selected_category = None if category is None else str(category)
        category_params: Dict[str, Any] = {}
        if selected_category is None:
            supported = self._metadata_categories(file_download) or []
            if len(supported) == 1:
                selected_category = supported[0]
            elif len(query_by_category) == 1:
                selected_category = str(next(iter(query_by_category)))
            elif supported or query_by_category:
                raise InvalidQueryError(
                    "Specify `category` for catalog {0!r}. Supported categories are: {1}.".format(
                        catname,
                        ", ".join(supported or [str(value) for value in query_by_category]),
                    )
                )

        if selected_category is not None:
            self._validate_download_categories(
                [selected_category],
                catalog=catname,
                file_download=file_download,
            )
            if selected_category in query_by_category:
                params = query_by_category[selected_category]
                if not isinstance(params, Mapping):
                    raise TableParseError(
                        "Catalog file-download metadata for category "
                        f"{selected_category!r} is not a mapping."
                    )
                category_params.update(params)
            else:
                category_params["category"] = selected_category

        endpoint = file_download.get("single_file_endpoint")
        url = self._endpoint_from_metadata(
            endpoint,
            default_path=self._openapi_path(f"catalogs/{catname}/file"),
        )
        return url, category_params, self._download_id_parameter(file_download)

    def _request_download_file(
        self,
        file_id: str,
        *,
        catalog: Optional[str] = None,
        category: Optional[str] = None,
        file_params: Optional[Mapping[str, Any]] = None,
        get_query_payload: bool = False,
        cache: bool = False,
    ):
        catname = catalog or self.catalog
        if get_query_payload:
            if category is not None and not file_params:
                raise InvalidQueryError(
                    "`file_params` is required with get_query_payload=True "
                    "when `category` is set; resolving category metadata requires "
                    "a service request."
                )
            url = self._openapi_url(f"catalogs/{catname}/file")
            params = _drop_none({"id": file_id, **dict(file_params or {})})
        else:
            url, metadata_params, id_parameter = self._file_download_request_config(
                catalog=catname,
                category=category,
                cache=cache,
            )
            params = _drop_none({id_parameter: file_id, **metadata_params, **dict(file_params or {})})
        if get_query_payload:
            params, headers = self._auth_params_headers(params=params)
            return {
                "method": "GET",
                "url": url,
                "params": params,
                "headers": headers,
                "stream": True,
            }
        return self._request_raise("GET", url, params=params, cache=cache, stream=True)

    def download_file(
        self,
        file_id: str,
        *,
        catalog: Optional[str] = None,
        category: Optional[str] = None,
        file_params: Optional[Mapping[str, Any]] = None,
        out_path: Optional[Union[str, os.PathLike[str]]] = None,
        overwrite: bool = True,
        get_query_payload: bool = False,
        cache: bool = False,
        verbose: bool = False,
    ):
        del verbose
        response = self._request_download_file(
            file_id,
            catalog=catalog,
            category=category,
            file_params=file_params,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response

        destination = self._resolve_download_path(
            response,
            out_path=out_path,
            default_name=f"{file_id}.bin",
        )
        return self._write_stream_response(response, destination, overwrite=overwrite)

    def _request_batch_download(
        self,
        payload: Mapping[str, Any],
        *,
        catalog: Optional[str] = None,
        stream: bool = False,
        endpoint: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = False,
    ):
        catname = catalog or self.catalog
        url = self._endpoint_from_metadata(
            endpoint,
            default_path=self._openapi_path(f"catalogs/{catname}/download"),
        )
        json_payload = dict(payload)
        if get_query_payload:
            params, headers = self._auth_params_headers()
            return {
                "method": "POST",
                "url": url,
                "params": params,
                "headers": headers,
                "json": json_payload,
                "stream": stream,
            }
        return self._request_raise("POST", url, json=json_payload, cache=cache, stream=stream)

    def batch_download(
        self,
        *,
        catalog: Optional[str] = None,
        fmt: str,
        id_list: Optional[Iterable[str]] = None,
        sqlid: Optional[Union[int, str]] = None,
        categories: Optional[Iterable[str]] = None,
        out_path: Optional[Union[str, os.PathLike[str]]] = None,
        overwrite: bool = True,
        get_query_payload: bool = False,
        cache: bool = False,
        verbose: bool = False,
    ):
        del verbose
        fmt = str(fmt).lower()
        if fmt not in {"targz", "urllist", "samba"}:
            raise InvalidQueryError("fmt must be one of: targz, urllist, samba.")

        if (id_list is None) == (sqlid is None):
            raise InvalidQueryError("Provide exactly one of `id_list` or `sqlid`.")

        payload: Dict[str, Any] = {"fmt": fmt}
        endpoint = None
        normalized_categories = self._normalize_categories(categories)
        if not get_query_payload:
            file_download = self._file_download_metadata(catalog=catalog, cache=cache)
            endpoint = file_download.get("batch_download_endpoint")
            normalized_categories = self._validate_download_categories(
                normalized_categories,
                catalog=catalog,
                file_download=file_download,
            )
        if id_list is not None:
            serialized_ids = [str(value) for value in id_list]
            if not serialized_ids:
                raise InvalidQueryError("id_list must not be empty.")
            payload["id_list"] = serialized_ids
        if sqlid is not None:
            payload["sqlid"] = int(sqlid)
        if normalized_categories is not None:
            payload["categories"] = normalized_categories

        stream = fmt in {"targz", "urllist"}
        response = self._request_batch_download(
            payload,
            catalog=catalog,
            stream=stream,
            endpoint=endpoint,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response

        if fmt == "samba":
            data = _response_json_payload(response)
            if data is None:
                raise TableParseError("Samba batch-download response did not return JSON.")
            return dict(data)

        default_name = (
            f"{catalog or self.catalog}-download.tar.gz"
            if fmt == "targz"
            else f"{catalog or self.catalog}-download.txt"
        )
        destination = self._resolve_download_path(
            response,
            out_path=out_path,
            default_name=default_name,
        )
        return self._write_stream_response(response, destination, overwrite=overwrite)

    def _ids_from_download_products(
        self,
        products,
        *,
        id_column: Optional[str] = None,
        file_download: Optional[Mapping[str, Any]] = None,
    ) -> List[str]:
        id_column_candidates = [id_column] if id_column is not None else self._download_id_column_candidates(file_download)

        def select_id_column(available_columns: Iterable[str], *, source: str) -> str:
            available = set(available_columns)
            for candidate in id_column_candidates:
                if candidate in available:
                    return candidate
            raise InvalidQueryError(
                "Download product {0} has none of the expected ID columns: {1}.".format(
                    source,
                    ", ".join(repr(candidate) for candidate in id_column_candidates),
                )
            )

        if isinstance(products, Table):
            selected_column = select_id_column(products.colnames, source="table")
            values = list(products[selected_column])
        elif isinstance(products, Mapping):
            selected_column = select_id_column(products.keys(), source="mapping")
            values = [products[selected_column]]
        elif isinstance(products, (str, bytes)):
            values = [products]
        else:
            try:
                values = list(products)
            except TypeError:
                values = [products]

        ids: List[str] = []
        for value in values:
            if isinstance(value, Mapping):
                selected_column = select_id_column(value.keys(), source="mapping")
                ids.append(str(value[selected_column]))
                continue

            colnames = getattr(value, "colnames", None)
            if colnames is not None:
                selected_column = select_id_column(colnames, source="row")
                ids.append(str(value[selected_column]))
                continue

            ids.append(str(value))

        if not ids:
            raise InvalidQueryError("No download product IDs were provided.")
        return ids

    def download_products(
        self,
        products,
        *,
        catalog: Optional[str] = None,
        fmt: str = "targz",
        categories: Optional[Iterable[str]] = None,
        id_column: Optional[str] = None,
        out_path: Optional[Union[str, os.PathLike[str]]] = None,
        overwrite: bool = True,
        get_query_payload: bool = False,
        cache: bool = False,
        verbose: bool = False,
    ):
        """Batch-download files associated with query result rows or IDs."""
        file_download = None
        if id_column is None:
            try:
                id_list = self._ids_from_download_products(products, id_column=id_column)
            except InvalidQueryError:
                file_download = self._file_download_metadata(catalog=catalog, cache=cache)
                id_list = self._ids_from_download_products(
                    products,
                    id_column=id_column,
                    file_download=file_download,
                )
        else:
            id_list = self._ids_from_download_products(products, id_column=id_column)

        return self.batch_download(
            catalog=catalog,
            fmt=fmt,
            id_list=id_list,
            categories=categories,
            out_path=out_path,
            overwrite=overwrite,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def _normalize_output_format(self, output_format: str, *, allow_html: bool = False) -> str:
        allowed_formats = ["txt", "csv", "json", "votable"]
        if allow_html:
            allowed_formats.append("html")

        fmt = str(output_format).lower()
        if fmt not in allowed_formats:
            raise InvalidQueryError(
                "output_format must be one of: {0}.".format(", ".join(allowed_formats))
            )
        return fmt

    def _to_degree(self, value: Union[u.Quantity, float], *, name: str) -> float:
        try:
            if isinstance(value, u.Quantity):
                return float(value.to_value(u.deg))
            return float(value)
        except Exception as exc:
            raise InvalidQueryError(f"{name} must be a float or angular quantity.") from exc

    def _to_arcsec(self, value: Union[u.Quantity, float], *, name: str) -> float:
        try:
            if isinstance(value, u.Quantity):
                return float(value.to_value(u.arcsec))
            return float(value)
        except Exception as exc:
            raise InvalidQueryError(f"{name} must be a float or angular quantity.") from exc

    def _build_cone_pos(
        self,
        coordinates,
        radius: Union[u.Quantity, float],
        *,
        nearest_only: bool = False,
    ) -> Dict[str, Any]:
        c = self._parse_coordinates(coordinates)
        return {
            "type": "cone",
            "cone": {
                "racenter": float(c.icrs.ra.to_value(u.deg)),
                "deccenter": float(c.icrs.dec.to_value(u.deg)),
                "radius": self._to_arcsec(radius, name="radius"),
                "cone_nearestonly": bool(nearest_only),
            },
        }

    def _build_rectangle_pos(
        self,
        ra_min: Union[u.Quantity, float],
        ra_max: Union[u.Quantity, float],
        dec_min: Union[u.Quantity, float],
        dec_max: Union[u.Quantity, float],
    ) -> Dict[str, Any]:
        return {
            "type": "rect",
            "rect": {
                "ramin": self._to_degree(ra_min, name="ra_min"),
                "ramax": self._to_degree(ra_max, name="ra_max"),
                "decmin": self._to_degree(dec_min, name="dec_min"),
                "decmax": self._to_degree(dec_max, name="dec_max"),
            },
        }

    def _format_proximity_line(self, position: Any) -> str:
        if isinstance(position, str):
            line = position.strip()
            if not line:
                raise InvalidQueryError("Proximity position strings must not be empty.")
            return line

        try:
            values = list(position)
        except TypeError:
            c = self._parse_coordinates(position)
            return "{0},{1}".format(
                float(c.icrs.ra.to_value(u.deg)),
                float(c.icrs.dec.to_value(u.deg)),
            )

        if len(values) == 2:
            ra, dec = values
            return "{0},{1}".format(
                self._to_degree(ra, name="ra"),
                self._to_degree(dec, name="dec"),
            )

        if len(values) == 3:
            ra, dec, radius = values
            return "{0},{1},{2}".format(
                self._to_degree(ra, name="ra"),
                self._to_degree(dec, name="dec"),
                self._to_arcsec(radius, name="radius"),
            )

        raise InvalidQueryError(
            "Each proximity position must be a string, a coordinate object, or a 2/3-item iterable."
        )

    def _build_proximity_pos(
        self,
        positions: Union[str, Iterable[Any]],
        *,
        default_radius: Optional[Union[u.Quantity, float]] = None,
        nearest_only: bool = False,
    ) -> Dict[str, Any]:
        if isinstance(positions, str):
            textarea = positions.strip()
        else:
            lines = [self._format_proximity_line(position) for position in positions]
            textarea = "\n".join(lines)

        if not textarea:
            raise InvalidQueryError("At least one proximity position is required.")

        proximity = _drop_none(
            {
                "radecTextarea": textarea,
                "defaultRadius": (
                    self._to_arcsec(default_radius, name="default_radius")
                    if default_radius is not None
                    else None
                ),
                "proximity_nearestonly": bool(nearest_only),
            }
        )
        return {"type": "proximity", "proximity": proximity}

    def _build_catalog_query_payload(
        self,
        *,
        pos: Optional[Mapping[str, Any]] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Union[ColumnConstraint, Mapping[str, Any]]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Dict[str, Any]:
        if pos is not None and pos_group is None:
            pos_group = self._default_pos_group()

        serialized_constraints = None
        if column_constraints:
            serialized_constraints = [
                cc.to_dict() if isinstance(cc, ColumnConstraint) else dict(cc)
                for cc in column_constraints
            ]

        return _drop_none(
            {
                "output.fmt": "html",
                "pos": dict(pos) if pos is not None else None,
                "pos_group": pos_group,
                "showcol": list(showcol) if showcol is not None else None,
                "column_constraints": serialized_constraints,
                "sort": sort,
                "order": order,
            }
        )

    def _submit_catalog_job(
        self,
        payload: Mapping[str, Any],
        *,
        catalog: Optional[str] = None,
        table: Optional[str] = None,
        cache: bool = True,
    ) -> int:
        submit_resp = self._submit_query_response(
            payload,
            catalog=catalog,
            table=table,
            cache=cache,
        )
        return self._extract_sqlid(submit_resp)

    def _execute_catalog_query_response(
        self,
        payload: Mapping[str, Any],
        *,
        catalog: Optional[str] = None,
        table: Optional[str] = None,
        output_format: str = "votable",
        page: Optional[int] = 1,
        rows: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        fmt = self._normalize_output_format(output_format)
        result_rows = rows if rows is not None else self._default_row_limit()

        if get_query_payload:
            submit_payload = self._submit_query_response(
                payload,
                catalog=catalog,
                table=table,
                get_query_payload=True,
                cache=cache,
            )
            results_payload = self._get_results_response(
                "<sqlid>",
                fmt=fmt,
                page=page,
                rows=result_rows,
                sort=sort,
                order=order,
                get_query_payload=True,
                cache=cache,
            )
            return {"submit": submit_payload, "results": results_payload}

        sqlid = self._submit_catalog_job(payload, catalog=catalog, table=table, cache=cache)
        return self._get_results_response(
            sqlid,
            fmt=fmt,
            page=page,
            rows=result_rows,
            sort=sort,
            order=order,
            cache=cache,
        )

    def _execute_catalog_query_table(
        self,
        payload: Mapping[str, Any],
        *,
        catalog: Optional[str] = None,
        table: Optional[str] = None,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        if max_rows is None:
            max_rows = self._default_row_limit()

        if not isinstance(max_rows, int) or max_rows < -1:
            raise InvalidQueryError("max_rows must be -1, 0, or a positive integer.")

        if max_rows == 0:
            empty = Table()
            self.table = empty
            return empty

        if page_size is None:
            page_size = self._default_row_limit()
        if not isinstance(page_size, int) or page_size < 1:
            raise InvalidQueryError("page_size must be a positive integer.")
        if max_rows != -1:
            page_size = min(page_size, max_rows)

        fmt = self._normalize_output_format(output_format)

        if get_query_payload:
            submit_payload = self._submit_query_response(
                payload,
                catalog=catalog,
                table=table,
                get_query_payload=True,
                cache=cache,
            )
            results_payload = self._get_results_response(
                "<sqlid>",
                fmt=fmt,
                page=1,
                rows=page_size,
                sort=sort,
                order=order,
                get_query_payload=True,
                cache=cache,
            )
            return {
                "submit": submit_payload,
                "results": results_payload,
                "max_rows": max_rows,
                "page_size": page_size,
            }

        sqlid = self._submit_catalog_job(payload, catalog=catalog, table=table, cache=cache)

        tables: List[Table] = []
        returned = 0
        page = 1

        while True:
            response = self._get_results_response(
                sqlid,
                fmt=fmt,
                page=page,
                rows=page_size,
                sort=sort,
                order=order,
                cache=cache,
            )
            table = self._parse_result(response, verbose=verbose)
            if len(table) == 0:
                break

            if max_rows != -1 and returned + len(table) > max_rows:
                table = table[: max_rows - returned]
                tables.append(table)
                returned += len(table)
                break

            tables.append(table)
            returned += len(table)

            if max_rows != -1 and returned >= max_rows:
                break
            if len(table) < page_size:
                break
            page += 1

        if not tables:
            empty = Table()
            self.table = empty
            return empty
        if len(tables) == 1:
            self.table = tables[0]
            return tables[0]
        combined = vstack(tables, metadata_conflicts="silent")
        self.table = combined
        return combined

    # -----------------------------
    # High-level query helpers
    # -----------------------------

    def _request_query_region(
        self,
        coordinates,
        radius: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        output_format: str = "votable",
        verb: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
    ):
        c = self._parse_coordinates(coordinates)
        ra_deg = float(c.icrs.ra.to_value(u.deg))
        dec_deg = float(c.icrs.dec.to_value(u.deg))

        return self._request_conesearch(
            ra_deg,
            dec_deg,
            radius,
            catalog=catalog,
            verb=verb,
            output_format=output_format,
            get_query_payload=get_query_payload,
            cache=cache,
        )

    def query_region(
        self,
        coordinates,
        radius: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        output_format: str = "votable",
        verb: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        response = self._request_query_region(
            coordinates,
            radius,
            catalog=catalog,
            output_format=output_format,
            verb=verb,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return self._parse_table_response(response, verbose=verbose)

    def describe_catalog(
        self,
        *,
        catalog: Optional[str] = None,
        table: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        """Return column metadata for a catalog table.

        Parameters
        ----------
        catalog : str, optional
            Catalog name. Defaults to the client's configured catalog.
        table : str, optional
            Table name. If omitted, single-table catalogs are resolved
            automatically.
        get_query_payload : bool, optional
            Return the request payload instead of executing the request.
        cache : bool, optional
            Whether to use astroquery's request cache.
        verbose : bool, optional
            Emit parser diagnostics for table responses.

        Returns
        -------
        astropy.table.Table or dict
            Column metadata table, or the request payload when
            ``get_query_payload=True``.
        """
        return self.list_columns(
            table,
            catalog=catalog,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_catalog(
        self,
        *,
        catalog: Optional[str] = None,
        coordinates=None,
        radius: Optional[Union[u.Quantity, float]] = None,
        pos: Optional[Mapping[str, Any]] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        if pos is not None and (coordinates is not None or radius is not None):
            raise InvalidQueryError("Provide either `pos` or (`coordinates` and `radius`), not both.")

        if pos is None and (coordinates is not None or radius is not None):
            if coordinates is None or radius is None:
                raise InvalidQueryError(
                    "If providing a cone constraint, both `coordinates` and `radius` are required."
                )
            pos = self._build_cone_pos(coordinates, radius, nearest_only=nearest_only)

        payload = self._build_catalog_query_payload(
            pos=pos,
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
        )
        return self._execute_catalog_query_table(
            payload,
            catalog=catalog,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_table(
        self,
        *,
        table: Optional[str] = None,
        catalog: Optional[str] = None,
        coordinates=None,
        radius: Optional[Union[u.Quantity, float]] = None,
        pos: Optional[Mapping[str, Any]] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        table = self._resolve_table_for_request(
            table,
            catalog=catalog,
            cache=cache,
            get_query_payload=get_query_payload,
        )

        if pos is not None and (coordinates is not None or radius is not None):
            raise InvalidQueryError("Provide either `pos` or (`coordinates` and `radius`), not both.")

        if pos is None and (coordinates is not None or radius is not None):
            if coordinates is None or radius is None:
                raise InvalidQueryError(
                    "If providing a cone constraint, both `coordinates` and `radius` are required."
                )
            pos = self._build_cone_pos(coordinates, radius, nearest_only=nearest_only)

        payload = self._build_catalog_query_payload(
            pos=pos,
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
        )
        return self._execute_catalog_query_table(
            payload,
            catalog=catalog,
            table=table,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_catalog_cone(
        self,
        coordinates,
        radius: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        payload = self._build_catalog_query_payload(
            pos=self._build_cone_pos(coordinates, radius, nearest_only=nearest_only),
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
        )
        return self._execute_catalog_query_table(
            payload,
            catalog=catalog,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_catalog_rectangle(
        self,
        ra_min: Union[u.Quantity, float],
        ra_max: Union[u.Quantity, float],
        dec_min: Union[u.Quantity, float],
        dec_max: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        payload = self._build_catalog_query_payload(
            pos=self._build_rectangle_pos(ra_min, ra_max, dec_min, dec_max),
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
        )
        return self._execute_catalog_query_table(
            payload,
            catalog=catalog,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_catalog_proximity(
        self,
        positions: Union[str, Iterable[Any]],
        *,
        catalog: Optional[str] = None,
        default_radius: Optional[Union[u.Quantity, float]] = None,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[List[Mapping[str, Any]]] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        payload = self._build_catalog_query_payload(
            pos=self._build_proximity_pos(
                positions,
                default_radius=default_radius,
                nearest_only=nearest_only,
            ),
            pos_group=pos_group,
            showcol=showcol,
            column_constraints=column_constraints,
            sort=sort,
            order=order,
        )
        return self._execute_catalog_query_table(
            payload,
            catalog=catalog,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_object(
        self,
        object_name: str,
        radius: Union[u.Quantity, float],
        *,
        catalog: Optional[str] = None,
        output_format: str = "votable",
        verb: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ):
        return self.query_region(
            object_name,
            radius,
            catalog=catalog,
            output_format=output_format,
            verb=verb,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    # -----------------------------
    # Parsing
    # -----------------------------

    def _extract_sqlid(self, response) -> int:
        try:
            data = response.json()
        except Exception as exc:
            message = "Query submission did not return JSON; cannot extract sqlid."
            if self.debug:
                message += " " + _response_debug_summary(response)
            raise TableParseError(message) from exc

        if isinstance(data, int):
            return int(data)
        if isinstance(data, str) and data.strip().isdigit():
            return int(data.strip())
        if isinstance(data, Mapping):
            for key in ("sqlid", "sql_id", "id", "jobid", "job_id"):
                if key in data and data[key] is not None:
                    try:
                        return int(data[key])
                    except Exception as exc:
                        raise TableParseError(f"Could not parse sqlid from key {key!r}.") from exc

        raise TableParseError(f"Could not extract sqlid from response JSON: {data!r}")

    def _parse_submit_response(self, response, *, verbose: bool = False) -> Dict[str, Any]:
        del verbose
        try:
            data = response.json()
        except Exception as exc:
            message = "Query submission did not return JSON."
            if self.debug:
                message += " " + _response_debug_summary(response)
            raise TableParseError(message) from exc

        if isinstance(data, Mapping):
            submit = dict(data)
            submit["sqlid"] = self._extract_sqlid(response)
            return submit

        if isinstance(data, int):
            return {"sqlid": int(data)}

        if isinstance(data, str) and data.strip().isdigit():
            return {"sqlid": int(data.strip())}

        raise TableParseError(f"Unrecognized query submission response JSON: {data!r}")

    def _parse_result(self, response, *, verbose: bool = False):
        if not verbose:
            commons.suppress_vo_warnings()

        content_type = (response.headers.get("Content-Type") or "").lower()
        text = response.text

        if response_looks_like_html(response):
            message = (
                "Server returned HTML instead of a table response; "
                "check authentication or upstream errors."
            )
            if verbose or self.debug:
                message += " " + _response_debug_summary(response)
            raise TableParseError(message)

        if "votable" in content_type or "xml" in content_type or response.content[:20].lstrip().startswith(b"<"):
            try:
                return _votable_table_to_astropy_table(parse_single_table(BytesIO(response.content)))
            except Exception as exc:
                sanitized = sanitize_votable_content(
                    response.content,
                    fix_invalid_date=True,
                    fix_missing_field_datatype=True,
                    fix_empty_arraysize=True,
                )
                if sanitized != response.content:
                    try:
                        return _votable_table_to_astropy_table(parse_single_table(BytesIO(sanitized)))
                    except Exception:
                        pass
                for candidate in (response.content, sanitized):
                    if candidate != response.content and candidate == sanitized == response.content:
                        continue
                    try:
                        return _parse_first_votable_table(candidate)
                    except Exception:
                        pass
                raise TableParseError("Failed to parse VOTable response.") from exc

        if "text/csv" in content_type or "text/plain" in content_type:
            try:
                if "," in text.splitlines()[0]:
                    return ascii.read(text, format="csv", fast_reader=False)
                return ascii.read(text, fast_reader=False)
            except Exception as exc:
                raise TableParseError("Failed to parse ASCII table response.") from exc

        if "application/json" in content_type or response.text.strip().startswith(("{", "[")):
            try:
                data = response.json()
            except Exception as exc:
                raise TableParseError("Failed to decode JSON response.") from exc

            if isinstance(data, list):
                if all(isinstance(row, Mapping) for row in data):
                    return _table_from_list_of_dicts(data)  # type: ignore[arg-type]
                raise TableParseError("JSON response is a list but not a list of objects.")

            if isinstance(data, Mapping):
                if "rows" in data and isinstance(data["rows"], list):
                    if all(isinstance(row, Mapping) for row in data["rows"]):
                        return _table_from_list_of_dicts(data["rows"])  # type: ignore[arg-type]
                    raise TableParseError("Response 'rows' is not a list of objects.")
                if "tables" in data and isinstance(data["tables"], list):
                    if all(isinstance(row, Mapping) for row in data["tables"]):
                        return _table_from_list_of_dicts(data["tables"])  # type: ignore[arg-type]
                    raise TableParseError("Response 'tables' is not a list of objects.")
                if "columns" in data and isinstance(data["columns"], list):
                    if all(isinstance(row, Mapping) for row in data["columns"]):
                        return _table_from_list_of_dicts(data["columns"])  # type: ignore[arg-type]
                    raise TableParseError("Response 'columns' is not a list of objects.")
                if "total" in data and isinstance(data["total"], int):
                    return Table({"total": [data["total"]]})
                if all(not isinstance(v, (Mapping, list)) for v in data.values()):
                    return Table({str(k): [v] for k, v in data.items()})

            raise InvalidQueryError(f"Unrecognized JSON response structure: {data!r}")

        raise TableParseError(f"Unrecognized response content-type: {content_type!r}")
