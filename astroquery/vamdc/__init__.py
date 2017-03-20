# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VAMDC molecular line database
"""
from astropy import config as _config
from astropy.config import paths
import os


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vamdc`.
    """

    timeout = _config.ConfigItem(60, "Timeout in seconds")

    cache_location = os.path.join(paths.get_cache_dir(), 'astroquery/vamdc',)


conf = Conf()

from .core import VamdcClass
from .core import Vamdc

__all__ = ['Vamdc', 'VamdcClass',
           'Conf', 'conf',
           ]
