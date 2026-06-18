# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Legacy Plate Catalog Query Tool
===============================

This module provides access to legacy plate catalogs served by the NADC
Query Data Access OpenAPI service.

The implementation shares the same protocol as `astroquery.nadc.cstar`, but
defaults to the ``legacyplate`` catalog family and filters catalog discovery to
the catalogs surfaced by this module.
"""

from astropy import config as _config

from .. import _QUERY_DATA_BASE_URL


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nadc.legacyplate`.
    """

    server = _config.ConfigItem(
        _QUERY_DATA_BASE_URL,
        "Base URL for the NADC Query Data Access OpenAPI service.",
    )

    timeout = _config.ConfigItem(
        60,
        "Timeout for legacy plate queries in seconds.",
    )

    catalog = _config.ConfigItem(
        "legacyplate",
        "Default catalog name used in API paths.",
    )

    supported_catalogs = _config.ConfigItem(
        "legacyplate,legacyplateedr,legacyplate-cat,legacyplate-image",
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
        "When True, include extra HTTP response diagnostics in Legacyplate exceptions.",
    )

    row_limit = _config.ConfigItem(
        10000,
        "Default maximum number of rows to request per page.",
    )

    pos_group = _config.ConfigItem(
        "ra,dec",
        "Default coordinate group used by structured spatial catalog queries.",
    )


conf = Conf()


from .core import Legacyplate, LegacyplateClass  # noqa: E402

__all__ = [
    "Conf",
    "Legacyplate",
    "LegacyplateClass",
    "conf",
]
