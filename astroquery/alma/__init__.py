# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALMA Archive service.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.alma`.
    """

    timeout = _config.ConfigItem(60, "Timeout in seconds.")

    archive_url = _config.ConfigItem(
        ['http://almascience.org',
         'https://almascience.eso.org',
         'https://almascience.nrao.edu',
         'https://almascience.nao.ac.jp',
         'https://beta.cadc-ccda.hia-iha.nrc-cnrc.gc.ca'],
        'The ALMA Archive mirror to use.')

    username = _config.ConfigItem(
        "",
        'Optional default username for ALMA archive.')


conf = Conf()

from .core import Alma, AlmaClass
from .utils import make_finder_chart

__all__ = ['Alma', 'AlmaClass',
           'Conf', 'conf',
           ]
