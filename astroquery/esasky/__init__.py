# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esasky`.
    """
    urlBase = _config.ConfigItem(
        'http://ammidev.n1data.lan:8080/esasky-tap',
        'ESASky base URL')

    timeout = _config.ConfigItem(
        1000,
        'Time limit for connecting to template_module server.')


conf = Conf()

from .core import ESASky, ESASkyClass 

__all__ = ['ESASky', 'ESASkyClass',
           'Conf', 'conf',
           ]

