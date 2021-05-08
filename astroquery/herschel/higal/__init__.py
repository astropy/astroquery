# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
HiGal cutout service
--------------------

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.higal`.
    """
    server = _config.ConfigItem(
        ['https://tools.ssdc.asi.it/',
         ],
        'Name of the higal server to use.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')


conf = Conf()

from .core import HiGal, HiGalClass

__all__ = ['HiGal', 'HiGalClass',
           'Conf', 'conf',
           ]
