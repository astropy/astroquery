# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Query Tool
===============

This module contains various methods for querying the
IRSA Catalog Query Service(CatQuery).
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.irsa`.
    """

    server = _config.ConfigItem(
        'https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query',
        'Name of the IRSA mirror to use.')
    gator_list_catalogs = _config.ConfigItem(
        'https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-scan',
        'URL from which to list all the public catalogs in IRSA.')
    row_limit = _config.ConfigItem(
        500,
        'Maximum number of rows to retrieve in result')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the IRSA server.')


conf = Conf()


from .core import Irsa, IrsaClass

__all__ = ['Irsa', 'IrsaClass',
           'Conf', 'conf',
           ]
