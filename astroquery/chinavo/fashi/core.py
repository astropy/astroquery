# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
FASHI Catalog Query Tool (Alias)
================================

This module provides the import path ``astroquery.chinavo.fashi.core`` as an alias
for ``astroquery.nadc.fashi.core``.
"""

from ...nadc.fashi.core import Fashi, FashiClass

__all__ = [
    "Fashi",
    "FashiClass",
]
