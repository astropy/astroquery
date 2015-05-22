# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SDSS Spectra/Image/SpectralTemplate Archive Query Tool
------------------------------------------------------
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.sdss`.
    """
    server = _config.ConfigItem(
        'notused',
        'Base URL for the '
        )
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to SDSS server.'
        )

conf = Conf()

from .core import SDSS, SDSSClass

import warnings
warnings.warn("Experimental: SDSS has not yet been refactored to have its API "
              "match the rest of astroquery (but it's nearly there).")
