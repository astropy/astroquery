# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
JPL Spectral Catalog (Deprecated Location)
-------------------------------------------

.. deprecated:: 0.4.12
    The `astroquery.jplspec` module has been moved to `astroquery.linelists.jplspec`.
    Please update your imports to use `from astroquery.linelists.jplspec import JPLSpec` instead.
    This backward compatibility layer will be removed in a future version.

This module provides backward compatibility for the old import location.
The JPLSpec module has been reorganized under the linelists subpackage.

For new code, please use::

    from astroquery.linelists.jplspec import JPLSpec

"""
import warnings

# Issue deprecation warning
warnings.warn(
    "Importing from 'astroquery.jplspec' is deprecated. "
    "Please use 'from astroquery.linelists.jplspec import JPLSpec' instead. "
    "The old import path will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new location
from ..linelists.jplspec import JPLSpec, JPLSpecClass, Conf, conf

__all__ = ['JPLSpec', 'JPLSpecClass', 'Conf', 'conf']
