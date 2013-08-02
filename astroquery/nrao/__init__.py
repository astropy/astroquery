# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""

from astropy.config import ConfigurationItem

NRAO_SERVER = ConfigurationItem('nrao_server', ["https://webtest.aoc.nrao.edu/cgi-bin/lsjouwer/archive-pos.pl"],
                               'Name of the NRAO mirror to use.')
NRAO_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to NRAO server')



from .core import Nrao
