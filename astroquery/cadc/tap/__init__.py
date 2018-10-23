# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""

from astroquery.cadc.tap.core import Tap
from astroquery.cadc.tap.core import TapPlus
from astroquery.cadc.tap.model.taptable import TapTableMeta
from astroquery.cadc.tap.model.tapcolumn import TapColumn

__all__ = ['Tap', 'TapPlus', 'TapTableMeta', 'TapColumn']
