# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LCOGT public archive Query Tool
===============

This module contains various methods for querying
LCOGT data archive as hosted by IPAC.
"""
from astropy import config as _config
import warnings

warnings.warn("The LCOGT archive API has been changed. While we aim to "
              "accommodate the changes into astroqeury, pleased be advised "
              "that this module is not working at the moment.")


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.irsa`.
    """

    server = _config.ConfigItem(
        'http://lcogtarchive.ipac.caltech.edu/cgi-bin/Gator/nph-query',
        'Name of the LCOGT archive as hosted by IPAC to use.')
    row_limit = _config.ConfigItem(
        500,
        'Maximum number of rows to retrieve in result')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the LCOGT IPAC server.')

conf = Conf()


from .core import Lcogt, LcogtClass

__all__ = ['Lcogt', 'LcogtClass',
           'Conf', 'conf',
           ]
