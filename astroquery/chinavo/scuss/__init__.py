# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SCUSS Catalog Query Tool (Alias)
--------------------------------

This module provides the import path ``astroquery.chinavo.scuss`` as an alias for
``astroquery.nadc.scuss``.
"""

from ...nadc.scuss import Conf, conf
from ...nadc.scuss import Scuss, ScussClass

__all__ = [
    "Conf",
    "Scuss",
    "ScussClass",
    "conf",
]
