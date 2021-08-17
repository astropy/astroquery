# Licensed under a 3-clause BSD style license - see LICENSE.rst


import warnings

warnings.warn("the ``ibe`` module has been moved to astroquery.ipac.irsa.ibe, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa.ibe import *
