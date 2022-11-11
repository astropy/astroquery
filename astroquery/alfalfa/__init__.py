# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ALFALFA Spectra Archive Query Tool
-----------------------------------

:Author: Jordan Mirocha (mirochaj@gmail.com)

"""
import warnings

from .core import Alfalfa, AlfalfaClass


__all__ = ["Alfalfa", "AlfalfaClass"]


warnings.warn("Experimental: ALFALFA has not yet been refactored to have "
              "its API match the rest of astroquery.")
