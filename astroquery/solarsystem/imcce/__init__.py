# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
astroquery.solarsystem.imcce
----------------------------

a collection of data services provided by IMCCE
"""

from .miriade import Miriade, MiriadeClass
from .skybot import Skybot, SkybotClass


__all__ = ["Miriade", "MiriadeClass", "Skybot", "SkybotClass"]
