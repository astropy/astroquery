# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Legacy Plate Catalog Query Tool (Alias)
---------------------------------------

This module provides the import path ``astroquery.chinavo.legacyplate`` as an
alias for ``astroquery.nadc.legacyplate``.
"""

from ...nadc.legacyplate import Conf, conf
from ...nadc.legacyplate import Legacyplate, LegacyplateClass

__all__ = [
    "Conf",
    "Legacyplate",
    "LegacyplateClass",
    "conf",
]
