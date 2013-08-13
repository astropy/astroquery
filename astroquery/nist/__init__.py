# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Fetches line spectra from the NIST Atomic Spectra Database.
"""
from astropy.config import ConfigurationItem
NIST_SERVER = ConfigurationItem('nist_server', ["http://physics.nist.gov/cgi-bin/ASD/lines1.pl"],
                               'Name of the NIST URL to query.')

NIST_TIMEOUT = ConfigurationItem('timeout', 30, 'time limit for connecting to NIST server')

from .core import Nist

__all__ = ['Nist']
