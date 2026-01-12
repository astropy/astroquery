# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Base classes and common utilities for linelist queries (JPLSpec, CDMS, etc.)
"""
import numpy as np
import string


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


def parse_molid(mol_id):
    """
    Parse molecule ID to ensure it is a zero-padded 6-character string.

    Parameters
    ----------
    mol_id : int or str
        The molecule identifier. Can be an integer (e.g., 18003 for H2O)
        or a zero-padded 6-character string (e.g., '018003').

    Returns
    -------
    str
        Zero-padded 6-character string representation of the molecule ID.

    Raises
    ------
    ValueError
        If mol_id is not an integer or string, or if it cannot be converted
        to a valid 6-digit identifier.
    """
    # Convert to string and zero-pad to 6 digits
    if isinstance(mol_id, (int, np.int32, np.int64)):
        molecule_str = f'{mol_id:06d}'
        if len(molecule_str) > 6:
            raise ValueError("molecule_id should be an integer with"
                             " fewer than 6 digits or a length-6 "
                             "string of numbers")
    elif isinstance(mol_id, str):
        # this is for the common case where the molecule is specified e.g. as 028001 CO
        try:
            molecule_id = f"{int(mol_id[:6]):06d}"
        except ValueError:
            raise ValueError("molecule_id should be an integer or a length-6 string of numbers")
        molecule_str = molecule_id
    else:
        raise ValueError("molecule_id should be an integer or a length-6 string of numbers")

    return molecule_str
