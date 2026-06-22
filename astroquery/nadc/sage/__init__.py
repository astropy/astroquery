# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SAGE Catalog Query Tool
=======================

This module provides access to the SAGE-related catalogs currently exposed by
the NADC Query Data Access OpenAPI service.

The repository's verified service snapshot currently surfaces exactly two
SAGE catalog names: ``SAGES-DR1`` and ``SAGES-StellarParameters``.
"""

from astropy import config as _config

from .. import _QUERY_DATA_BASE_URL


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nadc.sage`.
    """

    server = _config.ConfigItem(
        _QUERY_DATA_BASE_URL,
        "Base URL for the NADC Query Data Access OpenAPI service.",
    )

    timeout = _config.ConfigItem(
        60,
        "Timeout for SAGE queries in seconds.",
    )

    catalog = _config.ConfigItem(
        "SAGES-DR1",
        "Default catalog name used in API paths.",
    )

    supported_catalogs = _config.ConfigItem(
        "SAGES-DR1,SAGES-StellarParameters",
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
        "When True, include extra HTTP response diagnostics in SAGE exceptions.",
    )

    row_limit = _config.ConfigItem(
        10000,
        "Default maximum number of rows to request per page.",
    )

    pos_group = _config.ConfigItem(
        "",
        "Optional default coordinate group used by structured spatial catalog "
        "queries. Leave empty to omit pos_group by default.",
    )


conf = Conf()


from .core import Sage, SageClass  # noqa: E402


__all__ = [
    "Conf",
    "Sage",
    "SageClass",
    "conf",
]
