# Licensed under a 3-clause BSD style license - see LICENSE.rst
import StringIO
import requests
import numpy as np
from astropy.table import Table

__all__ = ['query']


URL = "http://ogle.astrouw.edu.pl/cgi-ogle/getext.py?"
ALGORITHMS = ['NG', 'NN']
QUALITIES = ['GOOD', 'ALL']
COORD_SYS = ['RD', 'LB']
RESULT_DTYPE = ['f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'i8', 'a2',
                'f8']

def query(coord, algorithm='NG', quality='GOOD', coord_sys='RD'):
    """
    Query the OGLE-III interstellar extinction calculator.

    Parameters
    ----------
    coord : list-like
        Pointings to evaluate interstellar extinction. Three forms of
        coordinates may be passed:
            * single astropy coordinate instance
            * list-like object (1 x N) of astropy coordinate instances
            * list-like object (2 x N) of RA/Decs or Glon/Glat as strings or
              floats.
    algorithm : string
        Algorithm to interpolate data for desired coordinate. Valid options:
            * 'NG': nearest grid point
            * 'NN': natural neighbor interpolation
    quality : string
        Quality factor for data. Valid options:
            * 'All': all points
            * 'GOOD': QF=0 as described in Nataf et al. (2012).
    coord_sys : string
        Coordinate system. Valid options:
            * 'RD': equatorial coordinates
            * 'LB': Galactic coordinates.

    Returns
    -------
    astropy.table.Table

    Raises
    ------
    CoordParseError
        Exception raised for malformed coordinate input

    Examples
    --------
    Using astropy coordinates:
    >>> from astropy import coordinates as coord
    >>> from astropy import units as u
    >>> co = coord.Galactic(0.0, 3.0, unit=(u.degree, u.degree))
    >>> t = ogle.query(co)
    >>> t.pprint()
      RA/LON   Dec/Lat    A_I  E(V-I) S_E(V-I) R_JKVI   mu    S_mu
    --------- ---------- ----- ------ -------- ------ ------ ----- ...
    17.568157 -27.342475 3.126  2.597    0.126 0.3337 14.581 0.212
    """
    # Inspect inputs
    if algorithm not in ALGORITHMS:
        raise ValueError('Algorithm {0} must be NG or NN'.format(algorithm))
    if quality not in QUALITIES:
        raise ValueError('Quality {0} must be GOOD or ALL'.format(quality))
    if coord_sys not in COORD_SYS:
        raise ValueError('Coordinate system {0} must be RD or \
                         LB.'.format(coord_sys))
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
        # single astropy coordinate
        try:
            lon = [coord.fk5.ra.hours]
            lat = [coord.fk5.dec.degrees]
            return lon, lat
        except:
            raise CoordParseError
    elif isinstance(coord, list):
        shape = np.shape(coord)
        # list of astropy coordinates
        if len(shape) == 1:
            try:
                lon = [co.fk5.ra.hours for co in coord]
                lat = [co.fk5.dec.degrees for co in coord]
                return lon, lat
            except:
                raise CoordParseError
        # list-like of values
        elif (len(shape) == 2) & (shape[0] == 2):
            return coord
        else:
            raise CoordParseError
    else:
        raise CoordParseError

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

