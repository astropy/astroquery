# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SHA Query Tool
--------------

:Author: Brian Svoboda (svobodb@email.arizona.edu)

This package is for querying the Spitzer Heritage Archive (SHA)
found at: http://sha.ipac.caltech.edu/applications/Spitzer/SHA.
"""
from .core import *

import warnings
warnings.warn("Experimental: SHA has not yet been refactored to have its "
              "API match the rest of astroquery.")
