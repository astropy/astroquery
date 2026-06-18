# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SCUSS Catalog Query Tool (Alias)
================================

This module provides the import path ``astroquery.chinavo.scuss.core`` as an alias
for ``astroquery.nadc.scuss.core``.
"""

from ...nadc.scuss.core import Scuss, ScussClass

__all__ = [
    "Scuss",
    "ScussClass",
]
