# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
UKIDSS Image and Catalog Query Tool
-----------------------------------

:Author: Thomas Robitalle (thomas.robitaille@gmail.com)
:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from __future__ import print_function
try:
    from .core import *
except ImportError:
    print("Failed to import UKIDSS: most likely because it is not py3-compatible")
