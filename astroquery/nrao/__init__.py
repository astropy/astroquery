# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to query the NRAO Data Archive for observation summaries.
"""
from astropy import config as _config

import warnings

# Remove module altogether if API update is not done in 6 months (2022-11-02).
warnings.warn("The legacy NRAO archive this module uses has been retired causing astroquery.nrao to be "
              "broken. We will remove this exception once sufficient updates are done to use the new "
              "NRAO archive API.")


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nrao`.
    """
    server = _config.ConfigItem(
        ['https://archive.nrao.edu/archive/ArchiveQuery'],
        'Name of the NRAO mirror to use.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to NRAO server.')
    username = _config.ConfigItem(
        "",
        'Optional default username for ALMA archive.')


conf = Conf()

from .core import Nrao, NraoClass

__all__ = ['Nrao', 'NraoClass',
           'Conf', 'conf',
           ]
