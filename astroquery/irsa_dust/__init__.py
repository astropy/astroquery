# Licensed under a 3-clause BSD style license - see LICENSE.rst


import warnings

warnings.warn("the ``irsa_dust`` module has been moved to "
              "astroquery.ipac.irsa.irsa_dust, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa.irsa_dust import *
