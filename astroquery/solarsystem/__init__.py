# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
astroquery.solarsystem
----------------------

a collection of Solar-System related data services
"""

from .jpl import SBDB, SBDBClass, Horizons, HorizonsClass
from .imcce import Miriade, MiriadeClass, Skybot, SkybotClass
from .mpc import MPC, MPCClass


__all__ = ["SBDB", "SBDBClass", "Horizons", "HorizonsClass",
           "Miriade", "MiriadeClass", "Skybot", "SkybotClass",
           "MPC", "MPCClass"]
