# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
OGLE Query Tool
---------------

:Author: Brian Svoboda (svobodb@email.arizona.edu)

This package is for querying interstellar extinction toward the Galactic bulge
from OGLE-III data
`hosted at. <http://ogle.astrouw.edu.pl/cgi-ogle/getext.py>`_

Note:
  If you use the data from OGLE please refer to the publication by Nataf et al.
  (2012).
"""
from astropy.config import ConfigurationItem

OGLE_SERVER = ConfigurationItem('ogle_server',
                                ['http://ogle.astrouw.edu.pl/cgi-ogle/getext.py'],
                                'Name of the OGLE mirror to use.')
OGLE_TIMEOUT = ConfigurationItem('timeout', 60,
                                 'Time limit for connecting to the OGLE server.')


from .core import Ogle

__all__ = ['Ogle']

import warnings
warnings.warn("Experimental: OGLE has not yet been refactored to have its API match the rest of astroquery.")
