# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
OGLE Query Tool
---------------

:Author: Brian Svoboda (svobodb@email.arizona.edu)

This package is for querying interstellar extinction toward the Galactic bulge
from OGLE-III data
`hosted at. <https://ogle.astrouw.edu.pl/cgi-ogle/getext.py>`_

Note:
  If you use the data from OGLE please refer to the publication by Nataf et al.
  (2012).
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ogle`.
    """
    server = _config.ConfigItem(
        ['https://ogle.astrouw.edu.pl/cgi-ogle/getext.py'],
        'Name of the OGLE mirror to use.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to OGLE server.')


conf = Conf()

from .core import Ogle, OgleClass

__all__ = ['Ogle', 'OgleClass',
           'Conf', 'conf',
           ]

import warnings
warnings.warn("Experimental: OGLE has not yet been refactored to have its "
              "API match the rest of astroquery.")
