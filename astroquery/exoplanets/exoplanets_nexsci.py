# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function, absolute_import

from astropy.utils.data import download_file
from astropy.io import ascii

EXOPLANETS_CSV_URL = ('http://exoplanetarchive.ipac.caltech.edu/cgi-bin/'
                      'nstedAPI/nph-nstedAPI?table=exoplanets')
EXOPLANETS_TABLE = None
PARAM_UNITS = None
TIME_ATTRS = {'TT': 'jd', 'T0': 'jd'}
BOOL_ATTRS = ('pl_kepflag', 'pl_ttvflag', 'pl_k2flag')


def exoplanets_table(cache=True, show_progress=True):
    global EXOPLANETS_TABLE

    if EXOPLANETS_TABLE is None:
        table_path = download_file(EXOPLANETS_CSV_URL, cache=cache,
                                   show_progress=show_progress)
        EXOPLANETS_TABLE = ascii.read(table_path)

        # Store column of lowercase names for indexing:
        lowercase_names = [i.lower() for i in EXOPLANETS_TABLE['NAME'].data]
        EXOPLANETS_TABLE['NAME_LOWERCASE'] = lowercase_names
        EXOPLANETS_TABLE.add_index('NAME_LOWERCASE')

    return EXOPLANETS_TABLE
