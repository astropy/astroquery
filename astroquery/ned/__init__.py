# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This is the old namespace for querying the NASA Extragalactic Database (NED).
Please update your imports and use it from astroquery.ipac.ned

.. deprecated:: 0.4.4
"""
import warnings

warnings.warn("the ``ned`` module has been moved to astroquery.ipac.ned, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.ned import Ned, NedClass, Conf, conf

__all__ = ['Ned', 'NedClass', 'Conf', 'conf']
