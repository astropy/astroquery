"""
MPC Query Tool
=================

The International Astronomical Union Minor Planet Center is "the single worldwide location for
receipt and distribution of positional measurements of minor planets, comets, and outer irregular
natural satellites of the major planets".
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.mpc`.
    """
    server = _config.ConfigItem(
        ['minorplanetcenter.net'],
        'Base URL for the MPC web service')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to MPC web service.')

    row_limit = _config.ConfigItem(
        # O defaults to the maximum limit
        0,
        'Maximum number of rows that will be fetched from the result.')


conf = Conf()

from .core import MPC, MPCClass

__all__ = ['MPCClass', 'conf']
