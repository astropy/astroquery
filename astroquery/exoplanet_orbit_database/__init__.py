# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Exoplanet Orbit Database Query Tool
-----------------------------------

:Author: Brett M. Morris (brettmorris21@gmail.com)
"""
import warnings
from .exoplanet_orbit_database import (ExoplanetOrbitDatabase,
                                       ExoplanetOrbitDatabaseClass)
from astropy import config as _config
from astropy.utils.exceptions import AstropyDeprecationWarning


warnings.warn("due to the retirement of its upstream website, the ``exoplanet_orbit_database`` module "
              "has been deprecated as of v0.4.7 and will be removed in a future release.",
              AstropyDeprecationWarning, stacklevel=2)


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.exoplanet_orbit_database`.
    """
    pass


__all__ = ['ExoplanetOrbitDatabase', 'ExoplanetOrbitDatabaseClass', 'Conf']
