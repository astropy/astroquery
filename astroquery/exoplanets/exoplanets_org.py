# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
import os

from astropy.utils.data import download_file
from astropy.io import ascii
import astropy.units as u

__all__ = ['query_exoplanets_org_catalog']

# Set global variables
EXOPLANETS_CSV_URL = 'http://exoplanets.org/csv-files/exoplanets.csv'
EXOPLANETS_TABLE = None
PARAM_UNITS = None
TIME_ATTRS = {'TT': 'jd', 'T0': 'jd'}
BOOL_ATTRS = ('ASTROMETRY', 'BINARY', 'EOD', 'KDE', 'MICROLENSING', 'MULT',
              'SE', 'TIMING', 'TRANSIT', 'TREND')


def query_exoplanets_org_catalog(cache=True, show_progress=True):
    """
    Download (and optionally cache) the exoplanets.org planets table [1]_.

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
    .. [1] http://www.exoplanets.org
    """
    global EXOPLANETS_TABLE

    if EXOPLANETS_TABLE is None:
        table_path = download_file(EXOPLANETS_CSV_URL, cache=cache,
                                   show_progress=show_progress)
        EXOPLANETS_TABLE = ascii.read(table_path)

        # Store column of lowercase names for indexing:
        lowercase_names = [i.lower() for i in EXOPLANETS_TABLE['NAME'].data]
        EXOPLANETS_TABLE['NAME_LOWERCASE'] = lowercase_names
        EXOPLANETS_TABLE.add_index('NAME_LOWERCASE')

        # Assign units to columns where possible
        units = exoplanets_org_units()
        for col in EXOPLANETS_TABLE.colnames:
            if col in units:
                EXOPLANETS_TABLE[col].unit = u.Unit(units[col])

    return EXOPLANETS_TABLE


def exoplanets_org_units():
    """
    Dictionary of exoplanet parameters and their associated units.
    """
    global PARAM_UNITS

    if PARAM_UNITS is None:
        module_dir = os.path.dirname(os.path.abspath(__file__))
        units_file = open(os.path.join(module_dir, 'data',
                                       'exoplanet_org_units.json'))
        PARAM_UNITS = json.load(units_file)

    return PARAM_UNITS
