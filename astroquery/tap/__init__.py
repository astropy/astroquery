# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

from astroquery.tap.core import Tap
from astroquery.tap.core import TapPlus
from astroquery.tap.model.tapcolumn import TapColumn

__all__ = ['Tap', 'TapPlus', 'Job', 'TapColumn']