# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
Dace API
--------

:author: Julien Burnier (julien.burnier@unige.ch)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.dace`.
    """
    server = _config.ConfigItem(
        ['https://dace-api.unige.ch/'],
        'Dace')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to DACE server.')


conf = Conf()

from .core import Dace, DaceClass

__all__ = ['Dace', 'DaceClass',
           'Conf', 'conf',
           ]
