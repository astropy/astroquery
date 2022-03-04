# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NASA Exoplanet Archive Query Tool
---------------------------------

Module to query the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu>`_ via `the
API <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_.
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ipac.nexsci.nasa_exoplanet_archive`.
    """

    url_api = _config.ConfigItem(
        "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI",
        "URL for the NASA Exoplanet Archive API")
    url_tap = _config.ConfigItem(
        "https://exoplanetarchive.ipac.caltech.edu/TAP/",
        "URL for the NASA Exoplanet Archive TAP")
    url_aliaslookup = _config.ConfigItem(
        "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Lookup/nph-aliaslookup.py?objname=",
        "URL for the NASA Exoplanet Archive aliaslookup")
    timeout = _config.ConfigItem(
        600, "Time limit for requests from the NASA Exoplanet Archive servers")
    cache = _config.ConfigItem(False, "Should the requests be cached?")


conf = Conf()

from .core import NasaExoplanetArchive, NasaExoplanetArchiveClass  # noqa isort:skip

__all__ = ["NasaExoplanetArchive", "NasaExoplanetArchiveClass", "Conf"]
