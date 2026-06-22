# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy import config as _config


QUERY_DATA_SHARED_TOKEN_ENV_VARS = (
    "ASTROQUERY_NADC_TOKEN",
    "NADC_QUERYDATA_TOKEN",
    "ASTROQUERY_NADC_ACCESS_TOKEN",
    "NADC_QUERYDATA_ACCESS_TOKEN",
    "ASTROQUERY_CHINAVO_TOKEN",
    "CHINAVO_QUERYDATA_TOKEN",
    "ASTROQUERY_CHINAVO_ACCESS_TOKEN",
    "CHINAVO_QUERYDATA_ACCESS_TOKEN",
)


class Conf(_config.ConfigNamespace):
    """
    Shared configuration for NADC Query Data Access OpenAPI modules.

    Notes
    -----
    This shared namespace is currently used by Query Data based clients such
    as `astroquery.nadc.cstar`, `astroquery.nadc.legacyplate`,
    `astroquery.nadc.sage`, and `astroquery.nadc.scuss`.
    Module-local ``conf.token`` values still override this shared fallback.
    """

    token = _config.ConfigItem(
        "",
        "Shared authentication token for NADC Query Data Access OpenAPI modules "
        "such as cstar, legacyplate, sage, and scuss.",
    )


conf = Conf()

# Import after conf is defined to avoid circular import
# (_query_data imports ``from . import conf``)
from ._query_data import ColumnConstraint  # noqa: E402


__all__ = [
    "ColumnConstraint",
    "Conf",
    "conf",
    "QUERY_DATA_SHARED_TOKEN_ENV_VARS",
]
