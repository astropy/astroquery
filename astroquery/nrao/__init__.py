# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NRAO Archive service.
"""
from astropy import config as _config


# list the URLs here separately so they can be used in tests.
_url_list = ['https://data.nrao.edu'
             ]

tap_urls = ['https://data-query.nrao.edu/']

auth_urls = ['data.nrao.edu']


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nrao`.
    """

    timeout = _config.ConfigItem(60, "Timeout in seconds.")

    archive_url = _config.ConfigItem(
        _url_list,
        'The NRAO Archive mirror to use.')

    auth_url = _config.ConfigItem(
        auth_urls,
        'NRAO Central Authentication Service URLs'
    )

    username = _config.ConfigItem(
        "",
        'Optional default username for NRAO archive.')


conf = Conf()

from .core import Nrao, NraoClass, NRAO_BANDS

__all__ = ['Nrao', 'NraoClass',
           'Conf', 'conf',
           ]
