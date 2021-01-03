# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
FIRST Image Query Tool
----------------------
.. topic:: Revision History

    :Originally contributed by:

        Rick White (rlw@stsci.edu)

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.image_cutouts.first`.
    """
    server = _config.ConfigItem(
        ['https://third.ucllnl.org/cgi-bin/firstcutout'],
        'Name of the FIRST server.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to FIRST server.')


conf = Conf()

from .core import First, FirstClass

__all__ = ['First', 'FirstClass',
           'Conf', 'conf',
           ]
