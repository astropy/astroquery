# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access to Fermi Gamma-ray Space Telescope data.

http://fermi.gsfc.nasa.gov
http://fermi.gsfc.nasa.gov/ssc/data/
"""
from astropy.config import ConfigurationItem

FERMI_URL = ConfigurationItem('fermi_url',
                              ['http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi'],
                              "Fermi query URL")
FERMI_TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to FERMI server')
FERMI_RETRIEVAL_TIMEOUT = ConfigurationItem('retrieval_timeout', 120, 'time limit for retrieving a data file once it has been located')

from .core import FermiLAT, GetFermilatDatafile, get_fermilat_datafile

import warnings
warnings.warn("Experimental: Fermi-LAT has not yet been refactored to have its API match the rest of astroquery.")
