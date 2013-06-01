# Licensed under a 3-clause BSD style license - see LICENSE.rst
import requests
import numpy as np
from astropy.table import Table

__all__ = ['query']


url = 'http://sha.ipac.caltech.edu/applications/Spitzer/SHA/servlet/DataService?{query}&VERB={verb}&DATASET=ivo%3A%2F%2Firsa.ipac%2Fspitzer.level{dataset}'
query_forms = {'position': 'RA={}&DEC={}&SIZE={}',
               'naifid': 'NAIFID={}',
               'pid': 'PID={}',
               'reqkey': 'REQKEY={}'}

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
    """
    if query_type not in query_forms.keys():
        raise ValueError('Invalid query type : {}.'.format(query_type))
    # Create the query strings from arguments
    # query_type <- position
    if query_type == 'position':
        if not all([isinstance(x, (float, int) for x in [ra, dec, size])]):
            raise ValueError('Ra, Dec, and Size must be in decimal degrees.')
        query_string = query_forms[query_type].format(ra, dec, size)
    # query_type <- naifid
    elif query_type == 'naifid':
        if not isinstance(naifid, (int, float)):
            raise ValueError('NAIFID must be a number.')
        query_string = query_forms[query_type].format(naifid)
    # query_type <- pid
    elif query_type == 'pid':
        if not isinstance(pid, (int, float)):
            raise ValueError('PID must be a number.')
        query_string = query_forms[query_type].format(pid)
    # query_type <- reqkey
    elif query_type == 'reqkey':
        if not isinstance(reqkey, (int, float)):
            raise ValueError('REQKEY must be a number.')
        query_string = query_forms[query_type].format(reqkey)
    else:
        raise Exception('Unexpected error')
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


