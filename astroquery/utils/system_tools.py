# Licensed under a 3-clause BSD style license - see LICENSE.rst

import gzip
import os
import shutil


def gunzip(filename):
    """ Decompress a file with gzip.

    Parameters
    ----------
    filename : str
        Fully qualified path of the file to decompress.

    Returns
    -------
    filename : str
        Name of the decompressed file (or input filename if gzip is not
        available).
    """

    # ".fz" denotes RICE rather than gzip compression
    if not filename.endswith('.fz'):
        with gzip.open(filename, 'rb') as f_in:
            with open(filename.rsplit(".", 1)[0], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return filename.rsplit(".", 1)[0]
    else:
        return filename


# If there is an update issue of astropy#2793 that got merged, this should
# be replaced with it.

def in_ipynb():
    return 'JPY_PARENT_PID' in os.environ
