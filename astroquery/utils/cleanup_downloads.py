# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Utility to cleanup files created during doctesting.
"""
import glob
import os
import shutil

__all__ = ['cleanup_saved_downloads']


def cleanup_saved_downloads(names):
    """ Function to clean up save files.

    Parameters
    ----------
    names : str or list of str
        Files or directories to clean up. Wildcards are accepted.
    """

    if isinstance(names, str):
        names = [names]

    for path in names:
        files = glob.glob(path)
        for saved_download in files:
            try:
                shutil.rmtree(saved_download)
            except NotADirectoryError:
                os.remove(saved_download)
