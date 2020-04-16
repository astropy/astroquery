# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os

# Import DEVNULL for py3 or py3
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

# Check availability of some system tools
# Exceptions are raised if not found


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
    import shutil
    import gzip

    # system-wide 'gzip' was removed, Python gzip used instead.
    # See #1538 : https://github.com/astropy/astroquery/issues/1538

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
    try:
        cfg = get_ipython().config
        app = cfg['IPKernelApp']
        # ipython 1.0 console has no 'parent_appname',
        # but ipynb does
        if ('parent_appname' in app and
                app['parent_appname'] == 'ipython-notebook'):
            return True
        else:
            return False
    except NameError:
        # NameError will occur if this is called from python (not ipython)
        return False
