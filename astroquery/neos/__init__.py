"""
NEOS Query Tool
===============

:Authors:
1) Antonio Hidalgo (antoniohidalgo.inves@gmail.com)
2) Juan Luis Cano Rodríguez (juanlu001@gmail.com)

This module contains various methods for querying the
NEOWS.

All of the methods are coded as part of SOCIS 2017 for poliastro by Antonio Hidalgo[1].
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    NEOWS_URL = "https://api.nasa.gov/neo/rest/v1/neo/"
    SBDB_URL = "https://ssd.jpl.nasa.gov/sbdb.cgi"

    neows_server = _config.ConfigItem(NEOWS_URL, "Near Earth Object Web Service URL")

    sbdb_server = _config.ConfigItem(SBDB_URL, "JPL Small-Body Database Browser URL")

    timeout = _config.ConfigItem(60, "time limit for connecting to the server")


conf = Conf()

from .core import *

__all__ = [Neows, NeowsClass]
