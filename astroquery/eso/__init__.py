# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ESO service.
"""
from astropy import config as _config
import os


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
    tap_url = _config.ConfigItem(
        "https://archive.eso.org/tap_obs",
        'URL for TAP queries.')
    tap_url_dev = _config.ConfigItem(
        os.environ['TAP_URL_DEV'],
        'URL for TAP development server.')

conf = Conf()

from .core import Eso, EsoClass

__all__ = ['Eso', 'EsoClass',
           'Conf', 'conf',
           ]
