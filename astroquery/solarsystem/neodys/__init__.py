"""
NEODyS Query Tool
-----------------

:Author: B612 Foundation

This package is for querying NEODys website

"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.solarsystem.neodys`.
    """
    server = _config.ConfigItem(
        ['https://newton.spacedys.com/~neodys2/epoch/'],
        'Base name of the NEODyS server to use.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to NEODyS server.')


conf = Conf()

from .core import NEODyS, NEODySClass

__all__ = ['NEODyS', 'NEODySClass',
           'Conf', 'conf',
           ]
