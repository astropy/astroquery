# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This is the old namespace for querying the NASA Exolpanet Archive.
Please update your imports and use it from astroquery.ipac.nexsci.nasa_exoplanet_archive.

.. deprecated:: 0.4.4
"""
import warnings

warnings.warn("the ``nasa_exoplanet_archive`` module has been moved to "
              "astroquery.ipac.nexsci.nasa_exoplanet_archive, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive, NasaExoplanetArchiveClass, Conf


__all__ = ["NasaExoplanetArchive", "NasaExoplanetArchiveClass", "Conf"]
