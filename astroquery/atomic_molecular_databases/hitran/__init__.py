# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
HITRAN Catalog Query Tool
-------------------------

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
import os
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.hitran`.
    """
    query_url = _config.ConfigItem('http://hitran.org/lbl/api',
                                   'HITRAN web interface URL.')
    timeout = _config.ConfigItem(60,
                                 'Time limit for connecting to HITRAN server.')
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    formatfile = _config.ConfigItem(os.path.join(data_dir, 'readme.txt'),
                                    'Format file.')


conf = Conf()

from .core import Hitran, HitranClass

__all__ = ['Hitran', 'HitranClass', 'conf']
