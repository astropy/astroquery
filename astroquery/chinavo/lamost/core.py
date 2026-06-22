# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LAMOST Spectroscopic Survey Query Tool (Alias)
==============================================

This module provides the import path ``astroquery.chinavo.lamost.core`` as an
alias for ``astroquery.nadc.lamost.core``.
"""

from ...nadc.lamost.core import Lamost, LamostClass
from ...nadc.lamost.core import parse_lrs_spectrum, parse_mrs_spectrum, plot_spectrum

__all__ = [
    'Lamost',
    'LamostClass',
    'parse_lrs_spectrum',
    'parse_mrs_spectrum',
    'plot_spectrum',
]
