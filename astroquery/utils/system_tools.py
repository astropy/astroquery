# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import subprocess


# Import DEVNULL for py3 or py3
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

# Check availability of some system tools
# Exceptions are raised if not found
__is_gzip_found = False
try:
    subprocess.call(["gzip", "-V"], stdout=DEVNULL, stderr=DEVNULL)
except OSError:
    print("gzip was not found on your system! You should solve this issue for "
          "astroquery.eso to be at its best!\n"
          "On POSIX system: make sure gzip is installed and in your path!"
          "On Windows: 7-zip (http://www.7-zip.org) should do the job, but "
          "unfortunately is not yet supported!")
else:
    __is_gzip_found = True


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
    if __is_gzip_found and not filename.endswith('.fz'):
        subprocess.call(["gzip", "-d", "{0}".format(filename)],
                        stdout=DEVNULL, stderr=DEVNULL)
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
