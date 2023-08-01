# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This is the old namespace for querying the NASA/IPAC Infrared Science Archive (IRSA).
Please update your imports and use it from astroquery.ipac.irsa

.. deprecated:: 0.4.4
"""
import warnings

warnings.warn("the ``irsa`` module has been moved to astroquery.ipac.irsa, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa import Irsa, IrsaClass, Conf, conf


__all__ = ['Irsa', 'IrsaClass', 'Conf', 'conf', ]
