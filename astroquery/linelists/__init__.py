# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Linelists module
----------------
This module contains sub-modules for various molecular and atomic line list databases,
as well as common utilities for parsing catalog files.
"""

from .core import LineListClass, parse_letternumber

__all__ = ['LineListClass', 'parse_letternumber']
