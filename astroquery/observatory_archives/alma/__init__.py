# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALMA Archive service.
"""
from astropy import config as _config


# list the URLs here separately so they can be used in tests.
_url_list = ['http://almascience.org',
             'https://almascience.eso.org',
             'https://almascience.nrao.edu',
             'https://almascience.nao.ac.jp']

_test_url_list = ['https://beta.cadc-ccda.hia-ha.nrc-cnrc.gc.ca']

auth_urls = ['asa.alma.cl', 'rh-cas.alma.cl']


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.alma`.
    """

    timeout = _config.ConfigItem(60, "Timeout in seconds.")

    archive_url = _config.ConfigItem(
        _url_list,
        'The ALMA Archive mirror to use.')

    test_archive_url = _config.ConfigItem(
        _test_url_list,
        'ALMA Archive Test Mirrors (temporary)'
    )

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
