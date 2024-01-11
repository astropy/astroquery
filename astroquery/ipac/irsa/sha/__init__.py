# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SHA Query Tool
--------------

:Author: Brian Svoboda (svobodb@email.arizona.edu)

This package is for querying the Spitzer Heritage Archive (SHA)
found at: https://sha.ipac.caltech.edu/applications/Spitzer/SHA.
"""
from .core import query, save_file, get_file

import warnings
warnings.warn("The upstream SHA API has been changed resulting this module to be broken. "
              "Please use the main IRSA module to access Spitzer data.")


__all__ = ['query', 'save_file', 'get_file']
