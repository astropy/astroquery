# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAGPIS Image and Catalog Query Tool
-----------------------------------
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Adam Ginsburg (adam.g.ginsburg@gmail.com)

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.magpis`.
    """
    server = _config.ConfigItem(
        ['https://third.ucllnl.org/cgi-bin/gpscutout'],
        'Name of the MAGPIS server.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to MAGPIS server.')


conf = Conf()

from .core import Magpis, MagpisClass

__all__ = ['Magpis', 'MagpisClass',
           'Conf', 'conf',
           ]
