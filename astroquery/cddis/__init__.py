# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
Access GNSS data in the NASA CDDIS archive.
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.cddis`.
    """
    server = _config.ConfigItem(
        'https://cddis.nasa.gov/archive/gnss/',
        'Base URL for the CDDIS GNSS archive.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to the CDDIS archive.')


conf = Conf()

from .core import CDDIS, CDDISClass

__all__ = ['CDDIS', 'CDDISClass', 'Conf', 'conf']
