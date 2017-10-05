# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
WFAU Image and Catalog Query Tool
---------------------------------
.. topic:: Revision History

    The UKIDSS query tool was refactored using common API as a part of Google
    Summer of Code 2013.  It was then refactored again to generically apply
    to any WFAU archives in late 2017.

    :Originally contributed by:

        Thomas Robitalle (thomas.robitaille@gmail.com)

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from .core import BaseWFAUClass, clean_catalog

__all__ = ['BaseWFAUClass', 'clean_catalog', ]
