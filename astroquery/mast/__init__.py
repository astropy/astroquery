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

from .cutouts import TesscutClass, Tesscut, ZcutClass, Zcut, HapcutClass, Hapcut
from .observations import Observations, ObservationsClass, MastClass, Mast
from .collections import Catalogs, CatalogsClass
from .missions import MastMissions, MastMissionsClass
from . import utils

__all__ = ['Observations', 'ObservationsClass',
           'Catalogs', 'CatalogsClass',
           'MastMissions', 'MastMissionsClass',
           'Mast', 'MastClass',
           'Tesscut', 'TesscutClass',
           'Zcut', 'ZcutClass',
           'Hapcut', 'HapcutClass',
           'Conf', 'conf', 'utils',
           ]
