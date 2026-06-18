# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SAGE Catalog Query Tool (Alias)
-------------------------------

This module provides the import path ``astroquery.chinavo.sage`` as an alias for
``astroquery.nadc.sage``.
"""

from ...nadc.sage import Conf, conf
from ...nadc.sage import Sage, SageClass

__all__ = [
    "Conf",
    "Sage",
    "SageClass",
    "conf",
]
