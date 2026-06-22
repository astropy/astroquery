# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CSTAR Catalog Query Tool
========================

This module provides access to the CSTAR catalog served by the NADC
Query Data Access OpenAPI service.

The underlying service supports multiple catalogs.  The implementation here
defaults to the ``cstar`` catalog, but `~astroquery.nadc.cstar.CstarClass`
can be instantiated with a different catalog name to reuse the same client
code for other catalogs exposed by the same API.
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nadc.cstar`.
    """

    server = _config.ConfigItem(
        "http://10.3.10.180:5506/",
        "Base URL for the NADC Query Data Access OpenAPI service.",
    )

    timeout = _config.ConfigItem(
        60,
        "Timeout for CSTAR queries in seconds.",
    )

    catalog = _config.ConfigItem(
        "cstar",
        "Default catalog name used in API paths.",
    )

    supported_catalogs = _config.ConfigItem(
        "cstar",
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
        "When True, include extra HTTP response diagnostics in CSTAR exceptions.",
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


from .core import Cstar, CstarClass  # noqa: E402

__all__ = [
    "Cstar",
    "CstarClass",
    "Conf",
    "conf",
]
