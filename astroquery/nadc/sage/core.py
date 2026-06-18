# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SAGE Catalog Query Tool
=======================

Core implementation for querying the SAGE-related catalogs exposed by the
NADC Query Data Access OpenAPI service.
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Union,
)

from astropy.table import Table

from .. import QUERY_DATA_SHARED_TOKEN_ENV_VARS
from .._query_data import (
    QueryDataBaseQuery,
    _append_equal_constraint,
    _append_max_constraint,
    _append_range_constraint,
    _configured_token_from_env as _configured_token_from_env_base,
)
from . import conf

__all__ = [
    "Sage",
    "SageClass",
]


_TOKEN_ENV_VARS = (
    "ASTROQUERY_SAGE_TOKEN",
    "ASTROQUERY_NADC_SAGE_TOKEN",
    "NADC_SAGE_TOKEN",
    "CHINAVO_SAGE_TOKEN",
    "ASTROQUERY_SAGE_ACCESS_TOKEN",
    "ASTROQUERY_NADC_SAGE_ACCESS_TOKEN",
    "NADC_SAGE_ACCESS_TOKEN",
    "CHINAVO_SAGE_ACCESS_TOKEN",
    *QUERY_DATA_SHARED_TOKEN_ENV_VARS,
)


def _configured_token_from_env() -> Optional[str]:
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


class SageClass(QueryDataBaseQuery):
    """
    Query SAGE-related catalogs via the NADC Query Data Access OpenAPI service.

    Notes
    -----
    The verified service snapshot bundled with this repository currently
    exposes two SAGE-related catalog names: ``SAGES-DR1`` and
    ``SAGES-StellarParameters``. Both are classified as plain ``catalog``
    products in the discovery snapshot, so this module intentionally reuses the
    shared Query Data catalog workflow without image- or spectrum-specific
    wrappers.

    The public NADC resource page for DOI ``10.12149/100876`` describes the
    underlying data release as DR1 plus DR1s data products, but only the two
    catalog names above appear in the verified service catalog snapshot.
    """

    CONF = conf
    TOKEN_ENV_VARS = _TOKEN_ENV_VARS
    ERROR_LABEL = "SAGE API error"
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_uv_sources(
        self,
        coordinates=None,
        radius=None,
        *,
        mag_u_range: Optional[Sequence[float]] = None,
        err_u_max: Optional[float] = None,
        mag_v_range: Optional[Sequence[float]] = None,
        err_v_max: Optional[float] = None,
        flag_u: Optional[int] = None,
        flag_v: Optional[int] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SAGE DR1 UV-source photometry from the ``dr1_uv`` table.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        mag_u_range, mag_v_range : sequence of float, optional
            Inclusive magnitude ranges.
        err_u_max, err_v_max : float, optional
            Maximum accepted photometric errors.
        flag_u, flag_v : int, optional
            Exact flag values to match.
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
        _append_range_constraint(constraints, "mag_u", mag_u_range)
        _append_max_constraint(constraints, "err_u", err_u_max)
        _append_range_constraint(constraints, "mag_v", mag_v_range)
        _append_max_constraint(constraints, "err_v", err_v_max)
        _append_equal_constraint(constraints, "flag_u", flag_u)
        _append_equal_constraint(constraints, "flag_v", flag_v)

        return super().query_table(
            table="dr1_uv",
            catalog="SAGES-DR1",
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

    def query_gri_sources(
        self,
        coordinates=None,
        radius=None,
        *,
        mag_g_range: Optional[Sequence[float]] = None,
        err_g_max: Optional[float] = None,
        mag_r_range: Optional[Sequence[float]] = None,
        err_r_max: Optional[float] = None,
        mag_i_range: Optional[Sequence[float]] = None,
        err_i_max: Optional[float] = None,
        flag_g: Optional[int] = None,
        flag_r: Optional[int] = None,
        flag_i: Optional[int] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SAGE DR1s gri-source photometry from the ``dr1s_gri`` table.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        mag_g_range, mag_r_range, mag_i_range : sequence of float, optional
            Inclusive magnitude ranges.
        err_g_max, err_r_max, err_i_max : float, optional
            Maximum accepted photometric errors.
        flag_g, flag_r, flag_i : int, optional
            Exact flag values to match.
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
        _append_range_constraint(constraints, "mag_g", mag_g_range)
        _append_max_constraint(constraints, "err_g", err_g_max)
        _append_range_constraint(constraints, "mag_r", mag_r_range)
        _append_max_constraint(constraints, "err_r", err_r_max)
        _append_range_constraint(constraints, "mag_i", mag_i_range)
        _append_max_constraint(constraints, "err_i", err_i_max)
        _append_equal_constraint(constraints, "flag_g", flag_g)
        _append_equal_constraint(constraints, "flag_r", flag_r)
        _append_equal_constraint(constraints, "flag_i", flag_i)

        return super().query_table(
            table="dr1s_gri",
            catalog="SAGES-DR1",
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

    def query_stellar_parameters(
        self,
        coordinates=None,
        radius=None,
        *,
        teff_range: Optional[Sequence[float]] = None,
        feh_range: Optional[Sequence[float]] = None,
        err_teff_max: Optional[float] = None,
        err_feh_max: Optional[float] = None,
        ruwe_max: Optional[float] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SAGE stellar-parameter catalog rows with common quality filters.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        teff_range, feh_range : sequence of float, optional
            Inclusive stellar-parameter ranges.
        err_teff_max, err_feh_max, ruwe_max : float, optional
            Maximum accepted quality metrics.
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
        _append_range_constraint(constraints, "teff", teff_range)
        _append_range_constraint(constraints, "feh", feh_range)
        _append_max_constraint(constraints, "err_teff", err_teff_max)
        _append_max_constraint(constraints, "err_feh", err_feh_max)
        _append_max_constraint(constraints, "ruwe", ruwe_max)

        return super().query_table(
            table="sages_param",
            catalog="SAGES-StellarParameters",
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


Sage: SageClass = SageClass()
