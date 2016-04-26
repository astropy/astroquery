# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ESO service.
"""
import warnings

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

conf = Conf()

from .core import Eso, EsoClass

__all__ = ['Eso', 'EsoClass',
           'Conf', 'conf',
           ]

warnings.warn("ESO is deploying new query forms in the first half of April "
              "2016. While we aim to accommodate the changes as soon as "
              "possible into astroquery, please be advised that things "
              "might break temporarily.")
