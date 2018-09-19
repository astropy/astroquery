# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Virtual Observatory
===================

This module contains various methods for querying the Virtual Observatory
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vo`.
    """
    registry_tap_url = _config.ConfigItem(
        'https://vao.stsci.edu/RegTAP/TapService.aspx',
        'Base URL of Registry TAP server')
    timeout = _config.ConfigItem(
        60,
        'Time limit (seconds) for connecting to VO services.',
        'float'
    )


conf = Conf()

from .core import Registry, RegistryClass

__all__ = ['Registry', 'RegistryClass']
