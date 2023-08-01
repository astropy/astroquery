# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This is the old namespace for querying the Spitzer Heritage Archive (SHA).
Please update your imports and use it from astroquery.ipac.irsa.sha.

.. deprecated:: 0.4.4
"""
import warnings


warnings.warn("the ``sha`` module has been moved to astroquery.ipac.irsa.sha, "
              "please update your imports.", DeprecationWarning, stacklevel=2)

from astroquery.ipac.irsa.sha import query, save_file, get_file


__all__ = ['query', 'save_file', 'get_file']
