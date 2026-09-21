# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LAMOST Spectroscopic Survey Query Tool
---------------------------------------

This module provides access to the LAMOST (Large Sky Area Multi-Object Fiber
Spectroscopic Telescope) spectroscopic survey data through the LAMOST OpenAPI.
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nadc.lamost`.
    """

    server = _config.ConfigItem(
        'https://www.lamost.org/openapi',
        'LAMOST OpenAPI base URL, including /openapi. Read when a '
        'LamostClass instance is created.')

    timeout = _config.ConfigItem(
        60,
        'Timeout for LAMOST queries in seconds')

    data_release = _config.ConfigItem(
        'dr10',
        'Default LAMOST data release version (e.g., dr10, dr11, dr12)')

    sub_version = _config.ConfigItem(
        'v2.0',
        'Default API sub-version')

    token = _config.ConfigItem(
        '',
        'Authentication token read when a LamostClass instance is created. '
        'An empty value allows environment/config-file fallback; pass token="" '
        'to the constructor for anonymous access. Authenticated requests '
        'disable caching.')


conf = Conf()

from .core import Lamost, LamostClass  # noqa: E402

__all__ = ['Lamost', 'LamostClass',
           'Conf', 'conf']
