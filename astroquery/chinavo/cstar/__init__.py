# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CSTAR Catalog Query Tool (Alias)
--------------------------------

This module provides the import path ``astroquery.chinavo.cstar`` as an alias for
``astroquery.nadc.cstar``.
"""

from ...nadc.cstar import Conf, conf
from ...nadc.cstar import Cstar, CstarClass

__all__ = [
    "Cstar",
    "CstarClass",
    "Conf",
    "conf",
]
