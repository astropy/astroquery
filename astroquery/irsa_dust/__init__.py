# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This is the old namespace for querying the NASA/IPAC Infrared Science Archive Dust Reddening Tool.
Please update your imports and use it from astroquery.ipac.irsa.irsa_dust

.. deprecated:: 0.4.4
"""

import warnings

warnings.warn("the ``irsa_dust`` module has been moved to "
              "astroquery.ipac.irsa.irsa_dust, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa.irsa_dust import IrsaDust, IrsaDustClass, Conf, conf


__all__ = ['IrsaDust', 'IrsaDustClass', 'Conf', 'conf']
