# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
FASHI Catalog Query Tool (Alias)
--------------------------------

This module provides the import path ``astroquery.chinavo.fashi`` as an alias for
``astroquery.nadc.fashi``.
"""

from ...nadc.fashi import Conf, conf
from ...nadc.fashi import Fashi, FashiClass

__all__ = [
    "Conf",
    "Fashi",
    "FashiClass",
    "conf",
]
