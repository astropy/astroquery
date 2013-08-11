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

from .core import *
