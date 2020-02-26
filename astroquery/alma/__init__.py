# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALMA Archive service.
"""
from astropy import config as _config


# list the URLs here separately so they can be used in tests.
_url_list =['http://almascience.org',
            'https://almascience.eso.org',
            'https://almascience.nrao.edu',
            'https://almascience.nao.ac.jp',
            # does not respond on Feb 25, 20202 'https://beta.cadc-ccda.hia-iha.nrc-cnrc.gc.ca'
           ]

_test_url_list = ['https://asa.hq.eso.org:8443',
                  # not a valid test server as of Feb 25, 2020 'https://2020feb.asa-test.alma.cl',
                 ]

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

    username = _config.ConfigItem(
        "",
        'Optional default username for ALMA archive.')


conf = Conf()

from .core import Alma, AlmaClass
from .utils import make_finder_chart

__all__ = ['Alma', 'AlmaClass',
           'Conf', 'conf',
           ]
