# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Astro ODA
-------

TODO

https://www.astro.unige.ch/cdci/astrooda_/
https://github.com/oda-hub/oda_api
https://marketplace.eosc-portal.eu/services/astronomical-online-data-analysis-astrooda
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.oda`.
    """

    server = _config.ConfigItem(
        ['https://www.astro.unige.ch/cdci/astrooda_'],
        'frontend base URL')

    timeout = _config.ConfigItem(
        30,
        'Time limit')


conf = Conf()

from .core import ODA, ODAClass

__all__ = ['ODA', 'ODAClass',
           'Conf', 'conf',
           ]
