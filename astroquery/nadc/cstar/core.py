# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CSTAR Catalog Query Tool
========================

Core implementation for querying the CSTAR catalog via the NADC Query Data
Access OpenAPI service.
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
    _append_max_constraint,
    _append_range_constraint,
    _configured_token_from_env as _configured_token_from_env_base,
)
from . import conf

__all__ = [
    "Cstar",
    "CstarClass",
]


_TOKEN_ENV_VARS = (
    "ASTROQUERY_CSTAR_TOKEN",
    "ASTROQUERY_NADC_CSTAR_TOKEN",
    "NADC_CSTAR_TOKEN",
    "CHINAVO_CSTAR_TOKEN",
    "ASTROQUERY_CSTAR_ACCESS_TOKEN",
    "ASTROQUERY_NADC_CSTAR_ACCESS_TOKEN",
    "NADC_CSTAR_ACCESS_TOKEN",
    "CHINAVO_CSTAR_ACCESS_TOKEN",
    *QUERY_DATA_SHARED_TOKEN_ENV_VARS,
)


def _configured_token_from_env() -> Optional[str]:
    return _configured_token_from_env_base(_TOKEN_ENV_VARS)


class CstarClass(QueryDataBaseQuery):
    """
    Query the CSTAR catalog via the NADC Query Data Access OpenAPI service.

    Notes
    -----
    The underlying service supports multiple catalogs.  This class can be
    instantiated with a different ``catalog`` name to reuse the client code
    for other catalogs exposed by the same API:

    >>> from astroquery.nadc.cstar import CstarClass
    >>> other = CstarClass(catalog="some-other-catalog")  # doctest: +SKIP

    Internally this client is already parameterized by ``catalog``. If future
    NADC catalog modules expose the same query/auth/result behavior, prefer
    thin wrappers with different defaults before introducing a shared base
    class.
    """

    CONF = conf
    TOKEN_ENV_VARS = _TOKEN_ENV_VARS
    ERROR_LABEL = "CSTAR API error"
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
        """Query CSTAR source catalog rows with common photometric filters.

        Parameters
        ----------
        coordinates : str or astropy.coordinates object, optional
            Center position for a cone search.
        radius : str, float, or astropy.units.Quantity, optional
            Cone-search radius. Required when ``coordinates`` is provided.
        mag_range : sequence of float, optional
            Inclusive ``mag`` range.
        magerr_max : float, optional
            Maximum accepted ``magerr`` value.
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
        _append_range_constraint(constraints, "mag", mag_range)
        _append_max_constraint(constraints, "magerr", magerr_max)

        return super().query_catalog(
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


# Singleton instance for module-level access
Cstar: CstarClass = CstarClass()
