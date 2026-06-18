# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Legacy Plate Catalog Query Tool (Alias)
=======================================

This module provides the import path ``astroquery.chinavo.legacyplate.core`` as an
alias for ``astroquery.nadc.legacyplate.core``.
"""

from ...nadc.legacyplate.core import Legacyplate, LegacyplateClass

__all__ = [
    "Legacyplate",
    "LegacyplateClass",
]
