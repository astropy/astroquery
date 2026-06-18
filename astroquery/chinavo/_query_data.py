# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Compatibility alias for `astroquery.nadc._query_data`.
"""

import sys

from ..nadc import _query_data as _query_data

sys.modules[__name__] = _query_data
