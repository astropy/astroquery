#
# Imports
#

import io
import sys
import numpy as np
from astropy.table import Table

#
# Support for VOTABLEs as astropy tables
#


def astropy_table_from_votable_string(s):
    """
    Takes a VOTABLE string and returns an astropy table.

    Parameters
    ----------
    string or byte array : s
        a valid VOTable.

    Returns
    -------
    astropy.table.Table
        Astropy Table containing the data from the first TABLE in the VOTABLE.
    """

    # The astropy table reader would like a file-like object, so convert
    # the string to a byte stream.
    #
    # (The reader also accepts just a string, but that seems to have two
    # problems:  It looks for newlines to see if the string is itself a table,
    # and we need to support unicode content.)
    file_like_content = io.BytesIO(s)

    # The astropy table reader will auto-detect that the content is a VOTABLE
    # and parse it appropriately.
    try:
        aptable = Table.read(file_like_content, format='votable')
    except Exception as e:
        print("ERROR parsing response as astropy Table: looks like the content isn't the expected VO table XML? Returning an empty table. Look at its meta data to debug.")
        aptable = Table()

    # String values in the VOTABLE are stored in the astropy Table as bytes instead
    # of strings.  To makes accessing them more convenient, we will convert all those
    # bytes values to strings.
    #
    # This is only an issue in Python version > 2 because bytes and strings are no longer the same thing.
    if sys.version_info[0] > 2:
        stringify_table(aptable)

    return aptable


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

    # Create the astropy Table from the VOTable in the reponse content.
    aptable = astropy_table_from_votable_string(response.content)

    # Store addtional metadata from the response on the Astropy Table.
    # This can help in debugging and may have other uses. Other metadata could be added here.
    # Do not include response.text since it effectively doubles the storage needed for the table.
    aptable.meta['astroquery.vo'] = {"url": response.url}

    return aptable


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
