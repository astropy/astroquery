# Licensed under a 3-clause BSD style license - see LICENSE.rst
import struct
import requests
import numpy as np
from astropy.table import Table
from astropy.io import fits
import ipdb as pdb


__all__ = ['query']


uri = 'http://sha.ipac.caltech.edu/applications/Spitzer/SHA/servlet/DataService?'

def query(ra=None, dec=None, size=None, naifid=None, pid=None,
    reqkey=None, dataset=2, verbosity=3):
    """
    Query the Spitzer Heritage Archive (SHA).

    Four query types are valid to search by position, NAIFID, PID, and ReqKey.
        position -> search a region
        naifid   -> NAIF ID, which is a unique number allocated to solar
                    system objects (e.g. planets, asteroids, comets,
                    spacecraft) by the NAIF at JPL.
        pid      -> program ID
        reqkey   -> AOR ID: Astronomical Observation Request ID
    For a valid query, enter only parameters related to a single query type:
        position -> ra, dec, size
        naifid   -> naifid
        pid      -> pid
        reqkey   -> reqkey

    Parameters
    ----------
    ra : number
        Right ascension in degrees
    dec : number
        Declination in degrees
    size : number
        Region size in degrees
    naifid : number
        NAIF ID
    pid : number
        Program ID
    reqkey : number
        Astronomical Observation Request ID
    dataset : number, default 2
        Data set. Valid options:
            1 -> BCD data
            2 -> PBCD data
    verbosity : number, default 3
        Verbosity level, controls the number of columns to output.

    Returns
    -------
    table : astropy.table.Table

    Notes
    -----
    For column descriptions, metadata, and other information visit the SHA
    query API_ help page:
    .. _API: http://sha.ipac.caltech.edu/applications/Spitzer/SHA/help/doc/api.html
    """
    # Query parameters
    payload = {'RA': ra,
               'DEC': dec,
               'SIZE': size,
               'NAIFID': naifid,
               'PID': pid,
               'REQKEY': reqkey,
               'VERB': verbosity,
               'DATASET': 'ivo://irsa.ipac.spitzer.level{}'.format(dataset)}
    # Make request
    response = requests.get(uri, params=payload)
    response.raise_for_status()
    # Parse output
    raw_data = [line.encode('ascii') for line in response.text.split('\n')]
    field_widths = [len(s) + 1 for s in raw_data[0].split('|')][1:-1]
    col_names = [s.strip() for s in raw_data[0].split('|')][1:-1]
    type_names = [s.strip() for s in raw_data[1].split('|')][1:-1]
    # Line parser for fixed width
    fmtstring = ''.join('%ds' % width for width in field_widths)
    line_parse = struct.Struct(fmtstring).unpack_from
    data = [[el.strip() for el in line_parse(row)] for row in raw_data[4:-1]]
    # Parse type names
    dtypes = _map_dtypes(type_names, field_widths)
    # To table
    t = Table(zip(*data), names=col_names, dtypes=dtypes)
    return t


def _map_dtypes(type_names, field_widths):
    """
    Create dtype string based on column lengths and field type names.

    Parameters
    ----------
    type_names : list
        List of type names from file header
    field_widths : list
        List of field width values

    Returns
    -------
    dtypes : list
        List of dtype for each column in data
    """
    dtypes = []
    for i, name in enumerate(type_names):
        if name == 'int':
            dtypes.append('i8')
        elif name == 'double':
            dtypes.append('f8')
        elif name == 'char':
            dtypes.append('a{}'.format(field_widths[i]))
        else:
            raise ValueError('Unexpected type name: {}.'.format(name))
    return dtypes


if __name__ == "__main__":
    pass


