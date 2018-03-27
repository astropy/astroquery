# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Exoplanet Orbit Database Query Tool
-----------------------------------

:Author: Brett M. Morris (brettmorris21@gmail.com)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from .exoplanet_orbit_database import (ExoplanetOrbitDatabase,
                                       ExoplanetOrbitDatabaseClass)
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.exoplanet_orbit_database`.
    """
    pass


__all__ = ['ExoplanetOrbitDatabase', 'ExoplanetOrbitDatabaseClass', 'Conf']
