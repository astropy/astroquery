# Licensed under a 3-clause BSD style license - see LICENSE.rst


import warnings

warnings.warn("the ``ned`` module has been moved to astroquery.ipac.ned, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.ned import *
