# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SDSS Spectra/Image/SpectralTemplate Archive Query Tool
------------------------------------------------------

:Author: Jordan Mirocha (mirochaj@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.sdss`.
    """
    server = _config.ConfigItem(
        ['http://data.sdss3.org/sas/dr10'],
        'Link to SDSS website.'
        )
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to SDSS server.'
        )
    maxqueries = _config.ConfigItem(
        1,
        'Max number of queries allowed per second.'
        )

conf = Conf()

from .core import SDSS, SDSSClass

import warnings
warnings.warn("Experimental: SDSS has not yet been refactored to have its API "
              "match the rest of astroquery (but it's nearly there).")
