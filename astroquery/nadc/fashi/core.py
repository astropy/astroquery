# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
FASHI Catalog Query Tool
========================

Core implementation for querying FASHI catalogs via the NADC Query Data
Access OpenAPI service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Sequence, Union

from astropy.table import Table

from .. import QUERY_DATA_SHARED_TOKEN_ENV_VARS
from .._query_data import (
    QueryDataBaseQuery,
    _append_equal_constraint,
    _append_min_constraint,
    _append_range_constraint,
    _configured_token_from_env as _configured_token_from_env_base,
)
from . import conf

if TYPE_CHECKING:
    from .._query_data import ColumnConstraint

__all__ = [
    "Fashi",
    "FashiClass",
]


_TOKEN_ENV_VARS = (
    "ASTROQUERY_FASHI_TOKEN",
    "ASTROQUERY_NADC_FASHI_TOKEN",
    "NADC_FASHI_TOKEN",
    "CHINAVO_FASHI_TOKEN",
    "ASTROQUERY_FASHI_ACCESS_TOKEN",
    "ASTROQUERY_NADC_FASHI_ACCESS_TOKEN",
    "NADC_FASHI_ACCESS_TOKEN",
    "CHINAVO_FASHI_ACCESS_TOKEN",
    *QUERY_DATA_SHARED_TOKEN_ENV_VARS,
)

_CATALOG = "FASHI"
_CATALOG_ALFALFA = "alfalfa_crossmatch"
_CATALOG_SDSS_PHOT = "optical_counterparts_sdss_phot"
_CATALOG_SDSS_SPEC = "optical_counterparts_sdss_spec"
_CATALOG_SGA = "optical_counterparts_sga"
_TABLE_HI_SOURCES = "extragalactic_hi_source_catalog"
_TABLE_ALFALFA = "alfalfa_crossmatch"
_TABLE_SDSS_PHOT = "optical_counterparts_sdss_phot"
_TABLE_SDSS_SPEC = "optical_counterparts_sdss_spec"
_TABLE_SGA = "optical_counterparts_sga"
_POS_GROUP_HI = "ra,dec"
_POS_GROUP_FASHI = "ra_fashi,dec_fashi"


def _configured_token_from_env() -> Optional[str]:
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


class FashiClass(QueryDataBaseQuery):
    """
    Query FASHI catalogs via the NADC Query Data Access OpenAPI service.

    Notes
    -----
    The FASHI catalog currently exposes one main HI-source table plus four
    precomputed match/counterpart tables.  Match tables contain both FASHI and
    external-catalog coordinates, so spatial queries should select the intended
    coordinate group explicitly when using low-level methods.
    """

    CONF = conf
    TOKEN_ENV_VARS = _TOKEN_ENV_VARS
    ERROR_LABEL = "FASHI API error"
    URL = conf.server
    TIMEOUT = conf.timeout

    def _query_fashi_table(
        self,
        *,
        catalog: str,
        table: str,
        coordinates=None,
        radius=None,
        default_pos_group: str,
        pos_group: Optional[str] = None,
        showcol: Optional[Iterable[str]] = None,
        column_constraints: Optional[list[ColumnConstraint]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        query_pos_group = pos_group
        if query_pos_group is None and (coordinates is not None or radius is not None):
            query_pos_group = default_pos_group

        return super().query_table(
            table=table,
            catalog=catalog,
            coordinates=coordinates,
            radius=radius,
            pos_group=query_pos_group,
            showcol=showcol,
            column_constraints=column_constraints or None,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_hi_sources(
        self,
        coordinates=None,
        radius=None,
        *,
        cz_range: Optional[Sequence[float]] = None,
        z_range: Optional[Sequence[float]] = None,
        snr_min: Optional[float] = None,
        distance_range: Optional[Sequence[float]] = None,
        log10mass_range: Optional[Sequence[float]] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query the main FASHI extragalactic HI source catalog."""
        constraints: list[ColumnConstraint] = []
        _append_range_constraint(constraints, "cz", cz_range)
        _append_range_constraint(constraints, "z", z_range)
        _append_min_constraint(constraints, "snr", snr_min)
        _append_range_constraint(constraints, "distance", distance_range)
        _append_range_constraint(constraints, "log10mass", log10mass_range)

        return self._query_fashi_table(
            catalog=_CATALOG,
            table=_TABLE_HI_SOURCES,
            coordinates=coordinates,
            radius=radius,
            default_pos_group=_POS_GROUP_HI,
            showcol=columns,
            column_constraints=constraints,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_alfalfa_matches(
        self,
        coordinates=None,
        radius=None,
        *,
        agcnr_alfalfa: Optional[int] = None,
        cz_fashi_range: Optional[Sequence[float]] = None,
        cz_alfalfa_range: Optional[Sequence[float]] = None,
        pos_group: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query the precomputed FASHI/ALFALFA cross-match table."""
        constraints: list[ColumnConstraint] = []
        _append_equal_constraint(constraints, "agcnr_alfalfa", agcnr_alfalfa)
        _append_range_constraint(constraints, "cz_fashi", cz_fashi_range)
        _append_range_constraint(constraints, "cz_alfalfa", cz_alfalfa_range)

        return self._query_fashi_table(
            catalog=_CATALOG_ALFALFA,
            table=_TABLE_ALFALFA,
            coordinates=coordinates,
            radius=radius,
            default_pos_group=_POS_GROUP_FASHI,
            pos_group=pos_group,
            showcol=columns,
            column_constraints=constraints,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_sdss_phot_counterparts(
        self,
        coordinates=None,
        radius=None,
        *,
        objid_sdss: Optional[int] = None,
        probability_min: Optional[float] = None,
        z_fashi_range: Optional[Sequence[float]] = None,
        pos_group: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SDSS photometric optical counterparts for FASHI sources."""
        constraints: list[ColumnConstraint] = []
        _append_equal_constraint(constraints, "objid_sdss", objid_sdss)
        _append_min_constraint(constraints, "probability_sdss", probability_min)
        _append_range_constraint(constraints, "z_fashi", z_fashi_range)

        return self._query_fashi_table(
            catalog=_CATALOG_SDSS_PHOT,
            table=_TABLE_SDSS_PHOT,
            coordinates=coordinates,
            radius=radius,
            default_pos_group=_POS_GROUP_FASHI,
            pos_group=pos_group,
            showcol=columns,
            column_constraints=constraints,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_sdss_spec_counterparts(
        self,
        coordinates=None,
        radius=None,
        *,
        objid_sdss: Optional[int] = None,
        z_fashi_range: Optional[Sequence[float]] = None,
        z_sdss_range: Optional[Sequence[float]] = None,
        pos_group: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SDSS spectroscopic optical counterparts for FASHI sources."""
        constraints: list[ColumnConstraint] = []
        _append_equal_constraint(constraints, "objid_sdss", objid_sdss)
        _append_range_constraint(constraints, "z_fashi", z_fashi_range)
        _append_range_constraint(constraints, "z_sdss", z_sdss_range)

        return self._query_fashi_table(
            catalog=_CATALOG_SDSS_SPEC,
            table=_TABLE_SDSS_SPEC,
            coordinates=coordinates,
            radius=radius,
            default_pos_group=_POS_GROUP_FASHI,
            pos_group=pos_group,
            showcol=columns,
            column_constraints=constraints,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )

    def query_sga_counterparts(
        self,
        coordinates=None,
        radius=None,
        *,
        name_sga: Optional[str] = None,
        z_fashi_range: Optional[Sequence[float]] = None,
        z_sga_range: Optional[Sequence[float]] = None,
        pos_group: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
        nearest_only: bool = False,
        output_format: str = "votable",
        max_rows: Optional[int] = None,
        page_size: Optional[int] = None,
        get_query_payload: bool = False,
        cache: bool = True,
        verbose: bool = False,
    ) -> Union[Table, Dict[str, Any]]:
        """Query SGA optical counterparts for FASHI sources."""
        constraints: list[ColumnConstraint] = []
        _append_equal_constraint(constraints, "name_sga", name_sga)
        _append_range_constraint(constraints, "z_fashi", z_fashi_range)
        _append_range_constraint(constraints, "z_sga", z_sga_range)

        return self._query_fashi_table(
            catalog=_CATALOG_SGA,
            table=_TABLE_SGA,
            coordinates=coordinates,
            radius=radius,
            default_pos_group=_POS_GROUP_FASHI,
            pos_group=pos_group,
            showcol=columns,
            column_constraints=constraints,
            nearest_only=nearest_only,
            output_format=output_format,
            max_rows=max_rows,
            page_size=page_size,
            get_query_payload=get_query_payload,
            cache=cache,
            verbose=verbose,
        )


Fashi: FashiClass = FashiClass()
