# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CSTAR Catalog Query Tool (Alias)
================================

This module provides the import path ``astroquery.chinavo.cstar.core`` as an
alias for ``astroquery.nadc.cstar.core``.
"""

from ...nadc.cstar.core import Cstar, CstarClass

__all__ = [
    "Cstar",
    "CstarClass",
]
