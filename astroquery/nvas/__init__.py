# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""

from astropy.config import ConfigurationItem

NVAS_SERVER = ConfigurationItem('nvas_server', ["https://webtest.aoc.nrao.edu/cgi-bin/lsjouwer/archive-pos.pl"],
                               'Name of the NVAS mirror to use.')
NVAS_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to NVAS server')

from .core import Nvas

__all__ = ['Nvas']
