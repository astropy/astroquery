# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
HyperLEDA Query Tool
-------------------

A tool to query HyperLEDA http://leda.univ-lyon1.fr/

:author: Iskren Y. Georgiev (iskren.y.g@gmail.com)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.hyperleda`.
    """
    server = _config.ConfigItem(
        ['http://leda.univ-lyon1.fr/'],
        'Base URL for HyperLeda http requests'
        )

    timeout = _config.ConfigItem(
        30,
        'Time timeout for the HyperLeda query.'
        )


conf = Conf()

from .core import hyperleda, HyperLEDAClass

__all__ = ['hyperleda', 'HyperLEDAClass',
           'Conf', 'conf',
           ]
