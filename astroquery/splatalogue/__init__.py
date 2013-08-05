# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Splatalogue Catalog Query Tool
-----------------------------------

REQUIRES mechanize (and astropy)

.. TODO::
    Replace mechanize with standard module

:Author: Magnus Vilehlm Persson (magnusp@vilhelm.nu)
"""
from .core import *
SLAP_URL = 'http://find.nrao.edu/splata-slap/slap'
QUERY_URL = 'http://www.cv.nrao.edu/php/splat/c_export.php'
