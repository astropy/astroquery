# Licensed under a 3-clause BSD style license - see LICENSE.rst
import StringIO
import requests
import numpy as np
from astropy.table import Table
import ipdb as pdb

__all__ = ['query']


URL = "http://ogle.astrouw.edu.pl/cgi-ogle/getext.py?"
ALGORITHMS = ['NG', 'NN']
QUALITIES = ['GOOD', 'ALL']
CoordParseError = ValueError('Could not parse `coord` argument.')

def query(coord, algorithm='NG', quality='GOOD', coord_sys='RD'):
    """
    Query the OGLE-III extinction calculator.

    Parameters
    ----------
    coord : array-like
    algorith : string
    quality : string
    coord_sys : string

    Returns
    -------
    astropy.table.Table

    Examples
    --------
    >>> 
    """
    if algorithm not in ALGORITHMS:
        raise ValueError('Algorithm {0} must be NG or NN'.format(algorithm))
    if quality not in QUALITIES:
        raise ValueError('Quality {0} must be GOOD or ALL'.format(quality))
    # Determine the coord object type and generate list of coordinates
    if not isinstance(coord, list):
        try:
            ra = [coord.fk5.ra.degrees]
            dec = [coord.fk5.dec.degrees]
        except:
            raise CoordParseError
    elif isinstance(coord, list):
        try:
            ra = [co.fk5.ra.degrees for co in np.array(coord)[:,0]]
            dec = [co.fk5.ra.degrees for co in np.array(coord)[:,1]]
        except:
            raise CoordParseError
    else:
        raise CoordParseError
    # Generate payload
    query_header = '# {0} {1} {2}\n'.format(coord_sys, algorithm, quality)
    sources = '\n'.join(['{0} {1}'.format(ra, dec) for ra, dec in zip(ra, dec)])
    file_data = query_header + sources
    files = {'file1': file_data}
    params = {'dnfile':'submit'}
    pdb.set_trace()
    # Make request
    response = requests.post(URL, params=params, files=files)
    response.raise_for_status()
    # Parse table
    raw_data = response.text.split('\n')[:-2]
    header = raw_data[0][1:].split()
    data = np.array([np.fromstring(line, sep=' ') for line in raw_data[1:]])
    t = Table(data, names=header)
    return t

if __name__ == "__main__":
    pass

