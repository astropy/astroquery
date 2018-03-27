# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ESO service.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.eso`.
    """

    row_limit = _config.ConfigItem(
        50,
        'Maximum number of rows returned (set to -1 for unlimited).')
    username = _config.ConfigItem(
        "",
        'Optional default username for ESO archive.')
    query_instrument_url = _config.ConfigItem(
        "http://archive.eso.org/wdb/wdb/eso",
        'Root query URL for main and instrument queries.')


conf = Conf()

from .core import Eso, EsoClass

__all__ = ['Eso', 'EsoClass',
           'Conf', 'conf',
           ]
