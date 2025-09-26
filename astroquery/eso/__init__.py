# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ESO service.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.eso`.
    """

    ROW_LIMIT = _config.ConfigItem(
        1000,
        'Maximum number of rows returned (set to -1 for unlimited).')
    username = _config.ConfigItem(
        "",
        'Optional default username for ESO archive.')
    tap_url = _config.ConfigItem(
        "https://archive.eso.org/tap_obs",
        'URL for TAP queries.')


conf = Conf()

from .core import Eso, EsoClass

__all__ = ['Eso', 'EsoClass',
           'Conf', 'conf',
           ]
