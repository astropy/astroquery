# Licensed under a 3-clause BSD style license - see LICENSE.rst
import struct
import requests
import numpy as np
from astropy.table import Table
from astropy.io import fits


__all__ = ['query']


uri = 'http://sha.ipac.caltech.edu/applications/Spitzer/SHA/servlet/DataService?'

def query(query_type, ra=None, dec=None, size=None, naifid=None, pid=None,
    reqkey=None, dataset=2, verbosity=3):
    """
    Query the Spitzer Heritage Archive (SHA).

    Parameters
    ----------
    query_type : string
        Query type. Valid options:
            position -> search a region
            naifid   -> NAIF ID, which is a unique number allocated to solar
                        system objects (e.g. planets, asteroids, comets,
                        spacecraft) by the NAIF at JPL.
            pid      -> program ID
            reqkey   -> AOR ID: Astronomical Observation Request ID
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
    raw_data = response.text.split('\n')
    field_widths = [len(s) for s in raw_data[0].split('|')]
    col_names = [s.strip() for s in raw_data[0].split('|')]
    type_names = [s.strip() for s in raw_data[1].split('|')]
    # Line parser for fixed width
    fmtstring = ''.join('%ds' % width for width in field_widths)
    line_parse = struct.Struct(fmtstring).unpack_from
    data = [line_parse(row) for row in raw_data[4:]]
    # To table
    return


def get_image(path):
    """
    Download a FITS image from the SHA
    """
    return


def _check_dtypes(data):
    """
    Check the data types of each column. If a column cannot be converted to a
    float, fall-back to a string.

    Parameters
    ----------
    data : np.narray

    Returns
    -------
    dtypes : list
        List of dtype for each column in data
    """
    dtypes = []
    for i in xrange(data.shape[1]):
        try:
            data[:,i].astype('float')
            dtypes.append('<f8')
        except ValueError:
            # TODO some columns may be more than 14 char long, change
            # dynamically
            dtypes.append('|S14')
    return dtypes


