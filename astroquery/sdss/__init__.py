# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SDSS Spectra/Image/SpectralTemplate Archive Query Tool
-----------------------------------

:Author: Jordan Mirocha (mirochaj@gmail.com)
"""

from astropy.config import ConfigurationItem

SDSS_SERVER = ConfigurationItem('sdss_server', 'http://das.sdss.org',
                               'Link to SDSS website.')

SDSS_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to SDSS server')

from .core import *
