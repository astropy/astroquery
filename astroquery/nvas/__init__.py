# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nvas`.
    """
    server = _config.ConfigItem(
        ['https://www.vla.nrao.edu/cgi-bin/nvas-pos.pl'],
        'Name of the NVAS mirror to use.')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to NVAS server.')


conf = Conf()

from .core import Nvas, NvasClass

__all__ = ['Nvas', 'NvasClass',
           'Conf', 'conf',
           ]
