# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SCUSS Catalog Query Tool
========================

This module provides access to SCUSS-related catalogs served by the NADC
Query Data Access OpenAPI service.

The currently verified service catalogs are ``scuss``, ``scuss-cat``,
``scuss-image``, and ``scuss-proper-motion``. The root ``scuss`` catalog is a
multi-table catalog, while ``scuss-cat`` currently exposes no table metadata
through the discovery API.
"""

from astropy import config as _config

from .. import _QUERY_DATA_BASE_URL


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nadc.scuss`.
    """

    server = _config.ConfigItem(
        _QUERY_DATA_BASE_URL,
        "Base URL for the NADC Query Data Access OpenAPI service.",
    )

    timeout = _config.ConfigItem(
        60,
        "Timeout for SCUSS queries in seconds.",
    )

    catalog = _config.ConfigItem(
        "scuss",
        "Default catalog name used in API paths.",
    )

    supported_catalogs = _config.ConfigItem(
        "scuss,scuss-cat,scuss-image,scuss-proper-motion",
        "Comma-separated catalogs surfaced by list_catalogs().",
    )

    token = _config.ConfigItem(
        "",
        "Module-local authentication token override (optional). Falls back to astroquery.nadc.conf.token when unset.",
    )

    auth_method = _config.ConfigItem(
        "bearer",
        'Authentication method: "query" adds a token query parameter; '
        '"bearer" sets an Authorization bearer-token header.',
    )

    debug = _config.ConfigItem(
        False,
        "When True, include extra HTTP response diagnostics in SCUSS exceptions.",
    )

    row_limit = _config.ConfigItem(
        10000,
        "Default maximum number of rows to request per page.",
    )

    pos_group = _config.ConfigItem(
        "",
        "Optional default coordinate group used by structured spatial queries. "
        "Leave empty because SCUSS catalogs do not share one safe default group.",
    )


conf = Conf()


from .core import Scuss, ScussClass  # noqa: E402


__all__ = [
    "Conf",
    "Scuss",
    "ScussClass",
    "conf",
]
