# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALMA Archive service.
"""
from astropy import config as _config


# list the URLs here separately so they can be used in tests.
_url_list = ['https://almascience.org',
             'https://almascience.eso.org',
             'https://almascience.nrao.edu',
             'https://almascience.nao.ac.jp'
             ]

auth_urls = ['asa.alma.cl', 'rh-cas.alma.cl']


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.alma`.
    """

    # Used if the current discovered host has no Service ID equivalent.  This
    # is used when overriding the default registry, which assumes to have
    # just almascience.org as the authority in the Service IDs.
    default_service_id_auth = 'almascience.org'

    timeout = _config.ConfigItem(60, "Timeout in seconds.")

    archive_url = _config.ConfigItem(
        _url_list,
        'The ALMA Archive mirror to use.')

    auth_url = _config.ConfigItem(
        auth_urls,
        'ALMA Central Authentication Service URLs'
    )

    username = _config.ConfigItem(
        "",
        'Optional default username for ALMA archive.')


conf = Conf()

from .core import Alma, AlmaClass, ALMA_BANDS

__all__ = ['Alma', 'AlmaClass',
           'Conf', 'conf', 'ALMA_BANDS'
           ]
