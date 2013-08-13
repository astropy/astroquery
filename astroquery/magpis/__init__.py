# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAGPIS Image and Catalog Query Tool
-----------------------------------
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Adam Ginsburg (adam.g.ginsburg@gmail.com)

"""
from astropy.config import ConfigurationItem

MAGPIS_SERVER = ConfigurationItem('magpis_server', ["http://third.ucllnl.org/cgi-bin/gpscutout"],
                               'Name of the MAGPIS server.')
MAGPIS_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to MAGPIS server')

from .core import Magpis

__all__ = ['Magpis']
