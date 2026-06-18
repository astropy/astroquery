# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SCUSS Catalog Query Tool
========================

Core implementation for querying SCUSS-related catalogs via the NADC Query
Data Access OpenAPI service.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Sequence, Union

from astropy.table import Table

from .. import QUERY_DATA_SHARED_TOKEN_ENV_VARS
from .._query_data import (
    QueryDataBaseQuery,
    _append_max_constraint,
    _append_min_constraint,
    _append_range_constraint,
    _configured_token_from_env as _configured_token_from_env_base,
)
from . import conf

__all__ = [
    "Scuss",
    "ScussClass",
]


_TOKEN_ENV_VARS = (
    "ASTROQUERY_SCUSS_TOKEN",
    "ASTROQUERY_NADC_SCUSS_TOKEN",
    "NADC_SCUSS_TOKEN",
    "CHINAVO_SCUSS_TOKEN",
    "ASTROQUERY_SCUSS_ACCESS_TOKEN",
    "ASTROQUERY_NADC_SCUSS_ACCESS_TOKEN",
    "NADC_SCUSS_ACCESS_TOKEN",
    "CHINAVO_SCUSS_ACCESS_TOKEN",
    *QUERY_DATA_SHARED_TOKEN_ENV_VARS,
)


def _configured_token_from_env() -> Optional[str]:
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


class ScussClass(QueryDataBaseQuery):
    """
    Query SCUSS-related catalogs via the NADC Query Data Access OpenAPI service.

    Notes
    -----
    The verified SCUSS catalog family currently consists of four catalog names:
    ``scuss`` (multi-table), ``scuss-cat`` (catalog-level query only in current
    discovery responses), ``scuss-image`` (single-table), and
    ``scuss-proper-motion`` (single-table).

    When working with the multi-table ``scuss`` catalog, pass the target table
    explicitly to ``query_table``, for example
    ``Scuss.query_table(catalog="scuss", table="catalogue")``.
    The ``scuss-cat`` catalog remains available for catalog-level query methods,
    but does not currently expose table metadata through discovery methods.
    """

    CONF = conf
    TOKEN_ENV_VARS = _TOKEN_ENV_VARS
    ERROR_LABEL = "SCUSS API error"
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_sources(
        self,
        coordinates=None,
        radius=None,
        *,
        mag_range: Optional[Sequence[float]] = None,
        magerr_max: Optional[float] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query sources from the main SCUSS catalogue table.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        mag_range : sequence of float, optional
            Inclusive ``psfmag`` range.
        magerr_max : float, optional
            Maximum accepted ``psferr`` value.
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
        constraints = []
        _append_range_constraint(constraints, "psfmag", mag_range)
        _append_max_constraint(constraints, "psferr", magerr_max)

        return super().query_table(
            table="catalogue",
            catalog="scuss",
            coordinates=coordinates,
            radius=radius,
            showcol=columns,
            column_constraints=constraints or None,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_sdss_matches(
        self,
        coordinates=None,
        radius=None,
        *,
        match_error_max: Optional[float] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SDSS DR10 matches associated with SCUSS sources.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        match_error_max : float, optional
            Maximum accepted match error.
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
        constraints = []
        _append_max_constraint(constraints, "match_err", match_error_max)

        return super().query_table(
            table="sdss10",
            catalog="scuss",
            coordinates=coordinates,
            radius=radius,
            showcol=columns,
            column_constraints=constraints or None,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_images(
        self,
        coordinates=None,
        radius=None,
        *,
        seeing_max: Optional[float] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "json",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SCUSS image metadata.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        seeing_max : float, optional
            Maximum accepted seeing value.
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
        constraints = []
        _append_max_constraint(constraints, "seeing", seeing_max)

        return super().query_table(
            table="image",
            catalog="scuss-image",
            coordinates=coordinates,
            radius=radius,
            showcol=columns,
            column_constraints=constraints or None,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_proper_motions(
        self,
        coordinates=None,
        radius=None,
        *,
        pmra_range: Optional[Sequence[float]] = None,
        pmdec_range: Optional[Sequence[float]] = None,
        mag_range: Optional[Sequence[float]] = None,
        obsused_min: Optional[int] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SCUSS proper-motion measurements.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        pmra_range, pmdec_range, mag_range : sequence of float, optional
            Inclusive proper-motion or magnitude ranges.
        obsused_min : int, optional
            Minimum number of observations used.
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
        constraints = []
        _append_range_constraint(constraints, "pmra", pmra_range)
        _append_range_constraint(constraints, "pmdec", pmdec_range)
        _append_range_constraint(constraints, "mag", mag_range)
        _append_min_constraint(constraints, "obsused", obsused_min)

        return super().query_table(
            table="proper_motion",
            catalog="scuss-proper-motion",
            coordinates=coordinates,
            radius=radius,
            showcol=columns,
            column_constraints=constraints or None,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )


Scuss: ScussClass = ScussClass()
