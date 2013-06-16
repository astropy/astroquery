# Licensed under a 3-clause BSD style license - see LICENSE.rst
import requests
import numpy as np
from astropy.table import Table

__all__ = ['query']


URL = "http://ogle.astrouw.edu.pl/cgi-ogle/getext.py?"

def print_mols():
    """
    Print molecule names available for query.
    """
    for mol_family in mols.keys():
        print '-- {0} :'.format(mol_family)
        print mols[mol_family], '\n'


def query(coord, algorithm=None, quality=None):
    """
    Query the OGLE-III extinction calculator.

    Parameters
    ----------
    coord : array-like
    algorith : string
    quality : string

    Returns
    -------
    astropy.table.Table

    Examples
    --------
    >>> 
    """
    # Convert list of coords to equatorial coordinates
    if coord is not None:
        try:
            ra = coord.fk5.ra.degrees
            dec = coord.fk5.dec.degrees
        except:
            raise Exception('Cannot parse `coord` argument.')
    # Query header
    query_header = '# {0} {1} {2}'.format()
    payload = {'',
              }
    # Make request
    response = requests.get(URL, params=payload)
    response.raise_for_status()
    pass

if __name__ == "__main__":
    pass

