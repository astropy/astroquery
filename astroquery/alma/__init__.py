# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALMA Archive service.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.alma`.
    """

    timeout = _config.ConfigItem(60, "Timeout in seconds")

    archive_url = _config.ConfigItem(['http://almascience.eso.org',
                                      'http://almascience.nrao.edu'],
                                     'The ALMA Archive mirror to use')

conf = Conf()

from .core import Alma, AlmaClass

__all__ = ['Alma', 'AlmaClass',
           'Conf', 'conf',
           ]


