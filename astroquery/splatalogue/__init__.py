# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Splatalogue Catalog Query Tool
-----------------------------------

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)

:Originally contributed by:

     Magnus Vilehlm Persson (magnusp@vilhelm.nu)
"""
from astropy.config import ConfigurationItem
SLAP_URL = ConfigurationItem('http://find.nrao.edu/splata-slap/slap',"Splatalogue SLAP interface URL (not used).")
QUERY_URL = ConfigurationItem('http://www.cv.nrao.edu/php/splat/c_export.php',"Splatalogue web interface URL.")
SPLATALOGUE_TIMEOUT = ConfigurationItem('timeout', 60, 'default timeout for connecting to server')

import load_species_table

from .core import Splatalogue

__all__ = ['Splatalogue']
