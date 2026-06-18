# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Legacy Plate Catalog Query Tool
===============================

Core implementation for querying legacy plate catalogs via the NADC Query
Data Access OpenAPI service.
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Union,
)

import astropy.units as u
from astropy.table import Table

from .. import QUERY_DATA_SHARED_TOKEN_ENV_VARS
from .._query_data import (
    QueryDataBaseQuery,
    _append_contains_constraint,
    _append_equal_constraint,
    _append_range_constraint,
    _configured_token_from_env as _configured_token_from_env_base,
)
from . import conf

if TYPE_CHECKING:
    from .._query_data import ColumnConstraint

__all__ = [
    "Legacyplate",
    "LegacyplateClass",
]


_TOKEN_ENV_VARS = (
    "ASTROQUERY_LEGACYPLATE_TOKEN",
    "ASTROQUERY_NADC_LEGACYPLATE_TOKEN",
    "NADC_LEGACYPLATE_TOKEN",
    "CHINAVO_LEGACYPLATE_TOKEN",
    "ASTROQUERY_LEGACYPLATE_ACCESS_TOKEN",
    "ASTROQUERY_NADC_LEGACYPLATE_ACCESS_TOKEN",
    "NADC_LEGACYPLATE_ACCESS_TOKEN",
    "CHINAVO_LEGACYPLATE_ACCESS_TOKEN",
    *QUERY_DATA_SHARED_TOKEN_ENV_VARS,
)


def _configured_token_from_env() -> Optional[str]:
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


# ---------------------------------------------------------------------------
# Column-constraint format — prefer ColumnConstraint factories over raw dicts
# ---------------------------------------------------------------------------
# >>> from astroquery.nadc import ColumnConstraint
# >>> ColumnConstraint.equal("observat", "Naoc")
# >>> ColumnConstraint.greaterequal("year", "1950")
# >>> ColumnConstraint.between("year", 1950, 1970)
# >>> ColumnConstraint.in_("observat", ["Naoc", "Shao"])
# Raw dicts are still accepted for backward compatibility.
# ---------------------------------------------------------------------------


class LegacyplateClass(QueryDataBaseQuery):
    """
    Query legacy plate catalogs via the NADC Query Data Access OpenAPI service.

    In addition to position-based searches (cone, rectangle, proximity), the
    legacy plate catalogs support filtering by **observatory** and
    **observation year** through the ``column_constraints`` parameter available
    on ``query_catalog``, ``query_catalog_cone``, ``query_catalog_rectangle``,
    and ``query_catalog_proximity``.

    Known observatory codes (``observat`` column): ``Naoc`` (国家天文台),
    ``Pmo`` (紫金山天文台), ``Qdo`` (青岛观象台), ``Shao`` (上海天文台),
    ``Ynao`` (云南天文台).

    Commonly used filterable columns include ``year`` (observation year),
    ``observat`` (observatory), ``telescop`` (telescope aperture in cm),
    ``object`` (target name), and ``date_o`` (observation date).

    Examples
    --------
    Filter plates observed at NAOC from 1950 onwards, sorted by year:

    >>> from astroquery.nadc import ColumnConstraint
    >>> from astroquery.nadc.legacyplate import Legacyplate
    >>> results = Legacyplate.query_catalog(  # doctest: +SKIP
    ...     catalog="legacyplateedr",
    ...     column_constraints=[
    ...         ColumnConstraint.greaterequal("year", "1950"),
    ...         ColumnConstraint.equal("observat", "Naoc"),
    ...     ],
    ...     sort="year",
    ...     order="desc",
    ...     max_rows=20,
    ... )

    Notes
    -----
    The underlying service can expose multiple legacy plate related catalogs.
    This class defaults to the module's configured catalog, while
    ``list_catalogs`` returns only queryable catalogs surfaced by this module.
    Pass ``queryable_only=False`` to include non-queryable module-supported
    catalogs in the discovery table.

    The ``column_constraints`` format follows the OpenAPI ``ColumnConstraint``
    schema.  Use the ``ColumnConstraint`` factory class for
    validation and clearer examples, or pass raw dicts with required keys
    ``column_name`` and ``operation``.
    """

    CONF = conf
    TOKEN_ENV_VARS = _TOKEN_ENV_VARS
    ERROR_LABEL = "Legacyplate API error"
    URL = conf.server
    TIMEOUT = conf.timeout

    def _plate_constraints(
        self,
        *,
        year_range: Optional[Sequence[int]] = None,
        observatory: Optional[str] = None,
        telescope: Optional[str] = None,
        object_name: Optional[str] = None,
    ) -> List[ColumnConstraint]:
        constraints: List[ColumnConstraint] = []
        _append_range_constraint(constraints, "year", year_range)
        _append_equal_constraint(constraints, "observat", observatory)
        _append_equal_constraint(constraints, "telescop", telescope)
        _append_contains_constraint(constraints, "object", object_name)
        return constraints

    def query_plates(
        self,
        coordinates=None,
        radius: Optional[Union[u.Quantity, float]] = None,
        *,
        year_range: Optional[Sequence[int]] = None,
        observatory: Optional[str] = None,
        telescope: Optional[str] = None,
        object_name: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
        catalog: str = "legacyplateedr",
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query legacy plate metadata with common archive filters.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        year_range : sequence of int, optional
            Inclusive observation-year range.
        observatory : str, optional
            Observatory code to match in the ``observat`` column.
        telescope : str, optional
            Telescope aperture value to match in the ``telescop`` column.
        object_name : str, optional
            Substring to match in the ``object`` column.
        columns : iterable of str, optional
            Columns to include in the result.
        catalog : str, optional
            Legacy plate catalog to query.
        nearest_only : bool, optional
            Return only the nearest match for spatial queries.
        output_format : str, optional
            Output format requested from the service.
        max_rows : int, optional
            Maximum number of rows to retrieve.
        page_size : int, optional
            Number of rows requested per service page.
        sort : str, optional
            Column used for sorting.
        order : {"asc", "desc"}, optional
            Sort order.
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
        constraints = self._plate_constraints(
            year_range=year_range,
            observatory=observatory,
            telescope=telescope,
            object_name=object_name,
        )

        return self.query_catalog(
            catalog=catalog,
            coordinates=coordinates,
            radius=radius,
            showcol=columns,
            column_constraints=constraints or None,
            sort=sort,
            order=order,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_plate_images(
        self,
        coordinates=None,
        radius: Optional[Union[u.Quantity, float]] = None,
        *,
        year_range: Optional[Sequence[int]] = None,
        observatory: Optional[str] = None,
        telescope: Optional[str] = None,
        object_name: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query legacy plate image metadata with common archive filters.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        year_range : sequence of int, optional
            Inclusive observation-year range.
        observatory : str, optional
            Observatory code to match in the ``observat`` column.
        telescope : str, optional
            Telescope aperture value to match in the ``telescop`` column.
        object_name : str, optional
            Substring to match in the ``object`` column.
        columns : iterable of str, optional
            Columns to include in the result.
        nearest_only : bool, optional
            Return only the nearest match for spatial queries.
        output_format : str, optional
            Output format requested from the service.
        max_rows : int, optional
            Maximum number of rows to retrieve.
        page_size : int, optional
            Number of rows requested per service page.
        sort : str, optional
            Column used for sorting.
        order : {"asc", "desc"}, optional
            Sort order.
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
        return self.query_plates(
            coordinates=coordinates,
            radius=radius,
            year_range=year_range,
            observatory=observatory,
            telescope=telescope,
            object_name=object_name,
            columns=columns,
            catalog="legacyplate-image",
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            sort=sort,
            order=order,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )


Legacyplate: LegacyplateClass = LegacyplateClass()
