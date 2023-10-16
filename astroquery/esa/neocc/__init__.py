# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NEOCC Query Tool
================

Module to query the Near Earth Objects Coordination Centre (NEOCC).

"""

import os
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for 'ESANEOCC'
    """

    BASE_URL = 'https://' + os.getenv('NEOCC_PORTAL_IP', default='neo.ssa.esa.int')

    API_URL = _config.ConfigItem(BASE_URL + '/PSDB-portlet/download?file=',
                                 "Main API URL")

    EPHEM_URL = _config.ConfigItem(BASE_URL + '/PSDB-portlet/ephemerides?des=',
                                   "Ephermerides URL")

    SUMMARY_URL = _config.ConfigItem(BASE_URL + '/search-for-asteroids?sum=1&des=',
                                     "Object summary URL")

    TIMEOUT = 60

    SSL_CERT_VERIFICATION = bool(int(os.getenv('SSL_CERT_VERIFICATION', default="1")))


conf = Conf()

from .core import neocc, NEOCCClass

__all__ = ['neocc', 'NEOCCClass', 'Conf', 'conf']
