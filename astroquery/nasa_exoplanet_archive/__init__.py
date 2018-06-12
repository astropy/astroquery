# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NASA Exoplanet Archive Query Tool
---------------------------------

:Author: Brett M. Morris (brettmorris21@gmail.com)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from astropy import config as _config
from .nasa_exoplanet_archive import (NasaExoplanetArchive,
                                     NasaExoplanetArchiveClass)


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nasa_exoplanet_archive`.
    """
    pass


__all__ = ['NasaExoplanetArchive', 'NasaExoplanetArchiveClass', 'Conf']
