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

    timeout = _config.ConfigItem(
        120,
        "Timeout in seconds. Applied to every request sent to the archive; "
        "the NRAO TAP backend can be slow, but a server that goes silent "
        "for longer than this is assumed to have stalled.")

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

from .core import Nrao, NraoClass

__all__ = ['Nrao', 'NraoClass',
           'Conf', 'conf',
           ]
