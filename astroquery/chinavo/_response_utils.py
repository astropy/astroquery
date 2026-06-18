# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Compatibility alias for `astroquery.nadc._response_utils`.
"""

import sys

from ..nadc import _response_utils as _response_utils

sys.modules[__name__] = _response_utils
