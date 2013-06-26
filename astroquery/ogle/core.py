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
RESULT_DTYPE = ['f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'i8', 'a2',
                'f8']

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
    Using astropy coordinates:
    >>> from astropy import coordinates as coord
    >>> from astropy import units as u
    >>> co = coord.Galactic(0.0, 3.0, unit=(u.degree, u.degree))
    >>> t = ogle.query(co)
    >>> t.pprint()
    """
    # Inspect inputs
    if algorithm not in ALGORITHMS:
        raise ValueError('Algorithm {0} must be NG or NN'.format(algorithm))
    if quality not in QUALITIES:
        raise ValueError('Quality {0} must be GOOD or ALL'.format(quality))
    # Determine the coord object type and generate list of coordinates
    lon, lat = _parse_coords(coord, coord_sys)
    # Generate payload
    query_header = '# {0} {1} {2}\n'.format(coord_sys, algorithm, quality)
    sources = '\n'.join(['{0} {1}'.format(lon, lat) for lon, lat in zip(lon,
        lat)])
    file_data = query_header + sources
    files = {'file1': file_data}
    params = {'dnfile':'submit'}
    # Make request
    response = requests.post(URL, params=params, files=files)
    response.raise_for_status()
    # Parse table
    raw_data = response.text.split('\n')[:-2]
    header = raw_data[0][1:].encode('ascii').split()
    data = _parse_raw(raw_data)
    t = Table(data, names=header, dtypes=RESULT_DTYPE)
    return t

def _parse_coords(coord, coord_sys):
    """
    Parse single astropy.coordinates instance, list of astropy.coordinate
    instances, or 2xN list of coordinate values.

    Parameters
    ----------
    coord : list-like
    coord_sys : string

    Returns
    -------
    lon : list
        Longitude coordinate values
    lat : list
        Latitude coordinate values
    """
    CoordParseError = ValueError('Could not parse `coord` argument.')
    if not isinstance(coord, list):
        try:
            lon = [coord.fk5.ra.hours]
            lat = [coord.fk5.dec.degrees]
        except:
            raise CoordParseError
    elif isinstance(coord, list):
        try:
            lon = [co.fk5.ra.hours for co in np.array(coord)[:,0]]
            lat = [co.fk5.ra.degrees for co in np.array(coord)[:,1]]
        except:
            raise CoordParseError
    else:
        raise CoordParseError
    return lon, lat

def _parse_raw(raw_data):
    """
    Parse the raw strings returned from the query request and return a list of
    lists for each column in string format.

    Parameters
    ----------
    raw_data : list
        Raw data from the request formatted to as list of strings for each line

    Returns
    -------
    data : list
        List of lists for each column as strings
    """
    # Requests returns unicode encoding, return to ascii
    data = [line.encode('ascii').split() for line in raw_data[1:]]
    # Transpose while keeping as list of lists
    data = map(list, zip(*data))
    return data

if __name__ == "__main__":
    pass

