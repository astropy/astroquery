# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esasky`.
    """
    urlBase = _config.ConfigItem(
        'http://sky.esa.int/esasky-tap',
        'ESASky base URL')

    timeout = _config.ConfigItem(
        1000,
        'Time limit for connecting to template_module server.')

    row_limit = _config.ConfigItem(
        10000,
        'Maximum number of rows returned (set to -1 for unlimited).')


conf = Conf()

from .core import ESASky, ESASkyClass

__all__ = ['ESASky', 'ESASkyClass',
           'Conf', 'conf',
           ]
