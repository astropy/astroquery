# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SAGE Catalog Query Tool (Alias)
===============================

This module provides the import path ``astroquery.chinavo.sage.core`` as an alias
for ``astroquery.nadc.sage.core``.
"""

from ...nadc.sage.core import Sage, SageClass

__all__ = [
    "Sage",
    "SageClass",
]
