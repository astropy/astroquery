# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This is the old namespace for querying the NASA/IPAC Infrared Science Archive Image Server (IBE).
Please update your imports and use it from astroquery.ipac.irsa.ibe

.. deprecated:: 0.4.4
"""
import warnings

warnings.warn("the ``ibe`` module has been moved to astroquery.ipac.irsa.ibe, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa.ibe import Ibe, IbeClass, Conf, conf


__all__ = ["Ibe", "IbeClass", "Conf", "conf"]
