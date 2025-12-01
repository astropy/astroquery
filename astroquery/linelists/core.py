# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Base classes and common utilities for linelist queries (JPLSpec, CDMS, etc.)
"""
import numpy as np
import string

__all__ = ['parse_letternumber']


def parse_letternumber(st):
    """
    Parse CDMS's two-letter QNs into integers.

    Masked values are converted to -999999.

    From the CDMS docs:
    "Exactly two characters are available for each quantum number. Therefore, half
    integer quanta are rounded up ! In addition, capital letters are used to
    indicate quantum numbers larger than 99. E. g. A0 is 100, Z9 is 359. Lower case characters
    are used similarly to signal negative quantum numbers smaller than –9. e. g., a0 is –10, b0 is –20, etc."
    """
    if isinstance(st, (np.int32, np.int64, int)):
        return st
    if np.ma.is_masked(st):
        return -999999

    asc = string.ascii_lowercase
    ASC = string.ascii_uppercase
    newst = ''.join(['-' + str((asc.index(x)+1)) if x in asc else
                     str((ASC.index(x)+10)) if x in ASC else
                     x for x in st])
    return int(newst)
