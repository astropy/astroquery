#
# Imports
#

import html # to unescape, which shouldn't be neccessary but currently is
import io
import numpy as np
from astropy.table import Table

#
# Support for VOTABLEs as astropy tables
#

def astropy_table_from_votable_response(response):
    """
    Takes a VOTABLE response from a web service and returns an astropy table.

    Parameters
    ----------
    response : requests.Response
        Response whose contents are assumed to be a VOTABLE.

    Returns
    -------
    astropy.table.Table
        Astropy Table containing the data from the first TABLE in the VOTABLE.
    """

    # The astropy table reader would like a file-like object, so convert
    # the response content a byte stream.  This assumes Python 3.x.
    #
    # (The reader also accepts just a string, but that seems to have two
    # problems:  It looks for newlines to see if the string is itself a table,
    # and we need to support unicode content.)
    #Tracer()()
    try:
        file_like_content = io.BytesIO(response.content)
    except IOError:
        print("ERROR parsing response content? Got:\n    {}...".format(response.content[0:400]))
        #  Should this return or raise?
        raise
    except Exception as e:
        raise e

    # The astropy table reader will auto-detect that the content is a VOTABLE
    # and parse it appropriately.
    try:
        aptable = Table.read(file_like_content, format='votable')
    except Exception as e:
        print("ERROR parsing response as astropy Table: looks like the content isn't the expected VO table XML? Returning an empty table. Look at its meta data to debug.")
        aptable = Table()
        #raise e

    aptable.meta['url'] = response.url
    aptable.meta['text'] = response.text
    # String values in the VOTABLE are stored in the astropy Table as bytes instead
    # of strings.  To makes accessing them more convenient, we will convert all those
    # bytes values to strings.
    stringify_table(aptable)

    return aptable

def find_column_by_ucd(table, ucd):
    """
    Given an astropy table derived from a VOTABLE, this function returns
    the first Column object that has the given Universal Content Descriptor (UCD).
    The name field of the returned value contains the column name and can be used
    for accessing the values in the column.

    Parameters
    ----------
    table : astropy.table.Table
        Astropy Table which was created from a VOTABLE (as if by astropy_table_from_votable_response).
    ucd : str
        The UCD identifying the column to be found.

    Returns
    -------
    astropy.table.Column
        The first column found which had the given ucd.  None is no such column found.

    Example
    -------
    col = find_column_by_ucd(my_table, 'VOX:Image_Title')
    print ('1st row title value is:', my_table[col.name][0])
    """

    # Loop through all the columns looking for the UCD
    for key in table.columns:
        col = table.columns[key]
        ucdval = col.meta.get('ucd')
        if ucdval is not None:
            if ucd == ucdval:
                return col

    return None

def find_column_by_utype(table, utype):
    """
    Given an astropy table derived from a VOTABLE, this function returns
    the first Column object that has the given utype.
    The name field of the returned value contains the column name and can be used
    for accessing the values in the column.

    Parameters
    ----------
    table : astropy.table.Table
        Astropy Table which was created from a VOTABLE (as if by astropy_table_from_votable_response).
    utype : str
        The utype identifying the column to be found.

    Returns
    -------
    astropy.table.Column
        The first column found which had the given utype.  None is no such column found.

    Example
    -------
    col = find_column_by_utype(my_table, 'Access.Reference')
    print ('1st row access_url value is:', my_table[col.name][0])
    """

    # Loop through all the columns looking for the utype
    for key in table.columns:
        col = table.columns[key]
        utypeval = col.meta.get('utype')
        if utypeval is not None:
            if utype == utypeval:
                return col

    return None

#
# Functions to help replace bytes with strings in astropy tables that came from VOTABLEs
#

def sval(val):
    """
    Returns a string value for the given object.  When the object is an instanceof bytes,
    utf-8 decoding is used.

    Parameters
    ----------
    val : object
        The object to convert

    Returns
    -------
    string
        The input value converted (if needed) to a string
    """
    if isinstance(val, bytes):
        return str(val, 'utf-8')
    else:
        return str(val)

# Create a version of sval() that operates on a whole column.
svalv = np.vectorize(sval)

def sval_whole_column(single_column):
    """
    Returns a new column whose values are the string versions of the values
    in the input column.  The new column also keeps the metadata from the input column.

    Parameters
    ----------
    single_column : astropy.table.Column
        The input column to stringify

    Returns
    -------
    astropy.table.Column
        Stringified version of input column
    """
    new_col = svalv(single_column)
    new_col.meta = single_column.meta
    return new_col

def stringify_table(t):
    """
    Substitutes strings for bytes values in the given table.

    Parameters
    ----------
    t : astropy.table.Table
        An astropy table assumed to have been created from a VOTABLE.

    Returns
    -------
    astropy.table.Table
        The same table as input, but with bytes-valued cells replaced by strings.
    """
    # This mess will look for columns that should be strings and convert them.
    if len(t) is 0:
        return   # Nothing to convert

    scols = []
    for col in t.columns:
        colobj = t.columns[col]
        if (colobj.dtype == 'object' and isinstance(t[colobj.name][0], bytes)):
            scols.append(colobj.name)

    for colname in scols:
        t[colname] = sval_whole_column(t[colname])

def query_loop(query_function, service, params, verbose=False):
    # Only one service, which is expected to be a row of a Registry query result that has  service['access_url']
    if verbose: print("    Querying service {}".format(html.unescape(service['access_url'])))
    # Initialize a table to add results to:
    service_results = []
    for j, param in enumerate(params):

        result = query_function(service=html.unescape(service['access_url']), **param)
        # Need a test that we got something back. Shouldn't error if not, just be empty
        if verbose:
            if len(result) > 0:
                print("    Got {} results for parameters[{}]".format(len(result), j))
                #Tracer()()
            else:
                print("    (Got no results for parameters[{}])".format(j))

        service_results.append(result)
    return service_results


def try_query(url, retries=3, timeout=60, get_params=None, post_data=None, files=None):
    """ A wrapper to the astroquery _request() function allowing for retries
    """
    from requests.exceptions import (Timeout, ReadTimeout)
    from urllib3.exceptions import ReadTimeoutError
    from astroquery.query import BaseQuery
    from IPython.core.debugger import Tracer

    bq = BaseQuery()
    retry = retries
    assert get_params is not None or post_data is not None, "Give either get_params or post_data"

    #Tracer()()
    while retry:
        try:
            if post_data is not None:
                response = bq._request('POST', url, data=post_data, cache=False, timeout=timeout,files=files)
            else:
                response = bq._request('GET', url, params=get_params, cache=False, timeout=timeout)
            retry = retries-1
        except (Timeout, ReadTimeout, ReadTimeoutError, ConnectionError) as e:
            retry = retry-1
            if retry == 0:
                print("ERROR: Got another timeout; quitting.")
                #Tracer()()
                #raise e
                return response
            else:
                print("WARNING: Got a timeout; trying again.")
        except:
            raise
        else:
            return response
