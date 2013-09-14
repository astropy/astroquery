# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SDSS Spectra/Image/SpectralTemplate Archive Query Tool
-----------------------------------

:Author: Jordan Mirocha (mirochaj@gmail.com)
"""

from astropy.config import ConfigurationItem

SDSS_SERVER = ConfigurationItem('sdss_server', 'http://das.sdss.org',
                               'Link to SDSS website.')

SDSS_MAXQUERY = ConfigurationItem('maxqueries', 1, 'Max number of queries allowed per second')

from .core import SDSS

import warnings
warnings.warn("Experimental: SDSS has not yet been refactored to have its API match the rest of astroquery (but it's nearly there).")
