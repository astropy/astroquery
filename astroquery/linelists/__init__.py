# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Linelists module
----------------
This module contains sub-modules for various molecular and atomic line list databases,
as well as common utilities for parsing catalog files.
"""

from astroquery.linelists.core import parse_letternumber

__all__ = ['parse_letternumber']
