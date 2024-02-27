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

from .core import Alma, AlmaClass, ALMA_BANDS, get_enhanced_table

__all__ = ['Alma', 'AlmaClass',
           'Conf', 'conf', 'ALMA_BANDS', 'get_enhanced_table'
           ]
