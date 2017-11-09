# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Query Tool
===============

This module contains various methods for querying the MAST Portal.
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


from .core import Observations, ObservationsClass, Catalogs, CatalogsClass, Mast, MastClass

__all__ = ['Observations', 'ObservationsClass',
           'Catalogs', 'CatalogsClass',
           'Mast', 'MastClass',
           'Conf', 'conf',
           ]
