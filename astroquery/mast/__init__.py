# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Query Tool
===============

Module to query the Barbara A. Mikulski Archive for Space Telescopes (MAST).
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.mast`.
    """

    server = _config.ConfigItem(
        'https://mast.stsci.edu',
        'Name of the MAST server.')
    ssoserver = _config.ConfigItem(
        'https://ssoportal.stsci.edu',
        'MAST SSO Portal server.')
    timeout = _config.ConfigItem(
        600,
        'Time limit for requests from the STScI server.')
    pagesize = _config.ConfigItem(
        50000,
        'Number of results to request at once from the STScI server.')


conf = Conf()

from .cutouts import TesscutClass, Tesscut, ZcutClass, Zcut
from .observations import MastObservations, MastObservationsClass, MastClass, Mast
from .collections import Catalogs, CatalogsClass
from .missions import MastMissions, MastMissionsClass
from .core import MastQueryWithLogin
from . import utils

__all__ = ['MastObservations', 'MastObservationsClass',
           'Catalogs', 'CatalogsClass',
           'MastMissions', 'MastMissionsClass',
           'Mast', 'MastClass',
           'Tesscut', 'TesscutClass',
           'Zcut', 'ZcutClass',
           'Conf', 'conf', 'utils',
           ]
