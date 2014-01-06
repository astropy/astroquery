# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Splatalogue Catalog Query Tool
-----------------------------------

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)

:Originally contributed by:

     Magnus Vilehlm Persson (magnusp@vilhelm.nu)
"""
from astropy.config import ConfigurationItem
SLAP_URL = ConfigurationItem("Splatalogue SLAP interface URL (not used).",'http://find.nrao.edu/splata-slap/slap')
QUERY_URL = ConfigurationItem("Splatalogue web interface URL.",'http://www.cv.nrao.edu/php/splat/c_export.php')
SPLATALOGUE_TIMEOUT = ConfigurationItem('timeout', 60, 'default timeout for connecting to server')
LINES_LIMIT = ConfigurationItem('Limit to number of lines exported', 10000)

import load_species_table

from .core import Splatalogue,SplatalogueClass

__all__ = ['Splatalogue','SplatalogueClass']
