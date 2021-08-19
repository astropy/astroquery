# Licensed under a 3-clause BSD style license - see LICENSE.rst


import warnings

warnings.warn("the ``nasa_exoplanet_archive`` module has been moved to "
              "astroquery.ipac.nexsci.nasa_exoplanet_archive, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.nexsci.nasa_exoplanet_archive import *
