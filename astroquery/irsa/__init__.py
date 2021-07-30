# Licensed under a 3-clause BSD style license - see LICENSE.rst


import warnings

warnings.warn("the ``irsa`` module has been moved to astroquery.ipac.irsa, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa import *
