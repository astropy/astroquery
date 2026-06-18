# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
FASHI Catalog Query Tool
========================

This module provides access to the FAST All Sky HI survey catalog served by
the NADC Query Data Access OpenAPI service.
"""

from astropy import config as _config

from .. import _QUERY_DATA_BASE_URL


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nadc.fashi`.
    """

    server = _config.ConfigItem(
        _QUERY_DATA_BASE_URL,
        "Base URL for the NADC Query Data Access OpenAPI service.",
    )

    timeout = _config.ConfigItem(
        60,
        "Timeout for FASHI queries in seconds.",
    )

    catalog = _config.ConfigItem(
        "FASHI",
        "Default catalog name used in API paths.",
    )

    supported_catalogs = _config.ConfigItem(
        (
            "FASHI,alfalfa_crossmatch,optical_counterparts_sdss_phot,"
            "optical_counterparts_sdss_spec,optical_counterparts_sga"
        ),
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
        "When True, include extra HTTP response diagnostics in FASHI exceptions.",
    )

    row_limit = _config.ConfigItem(
        10000,
        "Default maximum number of rows to request per page.",
    )

    pos_group = _config.ConfigItem(
        "",
        "Optional default coordinate group used by structured spatial queries. Leave empty because FASHI tables expose multiple coordinate groups.",
    )


conf = Conf()


from .core import Fashi, FashiClass  # noqa: E402


__all__ = [
    "Conf",
    "Fashi",
    "FashiClass",
    "conf",
]
