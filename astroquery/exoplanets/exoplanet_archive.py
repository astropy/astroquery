# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
import os
from astropy.utils.data import download_file
from astropy.io import ascii
import astropy.units as u

__all__ = ['query_exoplanet_archive_catalog']

EXOPLANETS_CSV_URL = ('http://exoplanetarchive.ipac.caltech.edu/cgi-bin/'
                      'nstedAPI/nph-nstedAPI?table=exoplanets')
EXOPLANETS_TABLE = None
PARAM_UNITS = None
TIME_ATTRS = {'rowupdate': 'iso'}
BOOL_ATTRS = ('pl_kepflag', 'pl_ttvflag', 'pl_k2flag', 'st_massblend',
              'st_optmagblend', 'st_radblend', 'st_teffblend')


def exoplanet_archive_units():
    """
    Dictionary of exoplanet parameters and their associated units.
    """
    global PARAM_UNITS

    if PARAM_UNITS is None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        units_file = open(os.path.join(pkg_dir, os.path.pardir, 'data',
                                       'exoplanet_nexsci_units.json'))
        PARAM_UNITS = json.load(units_file)

    return PARAM_UNITS


def query_exoplanet_archive_catalog(cache=True, show_progress=True):
    """
    Download (and optionally cache) the NExScI Exoplanet Archive Confirmed
    Planets table [1]_.

    Parameters
    ----------
    cache : bool (optional)
        Cache exoplanet table to local astropy cache? Default is `True`.
    show_progress : bool (optional)
        Show progress of exoplanet table download (if no cached copy is
        available). Default is `True`.

    Returns
    -------
    table : `~astropy.table.Table`
        Table of exoplanet properties.

    References
    ----------
    .. [1] http://exoplanetarchive.ipac.caltech.edu/index.html
    """
    global EXOPLANETS_TABLE

    if EXOPLANETS_TABLE is None:
        table_path = download_file(EXOPLANETS_CSV_URL, cache=cache,
                                   show_progress=show_progress)
        EXOPLANETS_TABLE = ascii.read(table_path)

        # Group by the host name
        EXOPLANETS_TABLE.group_by('pl_hostname')

        # Store column of lowercase names for indexing:
        lowercase_names = [' '.join([host_name.lower(), letter])
                           for host_name, letter in
                           zip(EXOPLANETS_TABLE['pl_hostname'].data,
                               EXOPLANETS_TABLE['pl_letter'].data)]
        EXOPLANETS_TABLE['NAME_LOWERCASE'] = lowercase_names
        EXOPLANETS_TABLE.add_index('NAME_LOWERCASE')

        # Assign units to columns where possible
        units = exoplanet_archive_units()
        for col in EXOPLANETS_TABLE.colnames:
            if col in units:
                EXOPLANETS_TABLE[col].unit = u.Unit(units[col])

    return EXOPLANETS_TABLE
