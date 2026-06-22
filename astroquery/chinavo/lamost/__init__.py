# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LAMOST Spectroscopic Survey Query Tool (Alias)
----------------------------------------------

This module provides the import path ``astroquery.chinavo.lamost`` as an alias for
``astroquery.nadc.lamost``.
"""

from ...nadc.lamost import Conf, conf
from ...nadc.lamost import Lamost, LamostClass
from ...nadc.lamost import parse_lrs_spectrum, parse_mrs_spectrum, plot_spectrum

__all__ = [
    'Lamost',
    'LamostClass',
    'Conf',
    'conf',
    'parse_lrs_spectrum',
    'parse_mrs_spectrum',
    'plot_spectrum',
]
