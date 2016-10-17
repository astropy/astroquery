# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function, absolute_import

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
import os

from astropy.utils.data import download_file
from astropy.io import ascii
import astropy.units as u
from astropy.time import Time

__all__ = ['PlanetParams']

# Set global variables
EXOPLANETS_CSV_URL = 'http://exoplanets.org/csv-files/exoplanets.csv'
EXOPLANETS_TABLE = None
PARAM_UNITS = None
TIME_ATTRS = {'TT': 'jd', 'T0': 'jd'}
BOOL_ATTRS = ('ASTROMETRY', 'BINARY', 'EOD', 'KDE', 'MICROLENSING', 'MULT',
              'SE', 'TIMING', 'TRANSIT', 'TREND')


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


def parameter_units():
    """
    Dictionary of exoplanet parameters and their associated units.
    """
    global PARAM_UNITS

    if PARAM_UNITS is None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        units_file = open(os.path.join(pkg_dir, os.path.pardir, 'data',
                                       'exoplanet_org_units.json'))
        PARAM_UNITS = json.load(units_file)

    return PARAM_UNITS


class PlanetParams(object):
    """
    Exoplanet system parameters.

    Caches a local copy of the http://exoplanets.org table, and queries
    for a planet's properties. Unitful quantities are returned whenever
    possible.
    """
    def __init__(self, exoplanet_name, cache=True, show_progress=True):
        """
        Parameters
        ----------
        exoplanet_name : str
            Name of exoplanet (case insensitive)
        cache : bool (optional)
            Cache exoplanet table to local astropy cache? Default is `True`.
        show_progress : bool (optional)
            Show progress of exoplanet table download (if no cached copy is
            available). Default is `True`.
        """
        # Load exoplanets table, corresponding units
        table = exoplanets_table(cache=cache, show_progress=show_progress)
        param_units = parameter_units()

        if not exoplanet_name.lower().strip() in table['NAME_LOWERCASE'].data:
            raise ValueError('Planet "{0}" not found in exoplanets.org catalog')

        row = table.loc[exoplanet_name.lower().strip()]
        for column in row.colnames:
            value = row[column]

            # If param is unitful quantity, make it a `astropy.units.Quantity`
            if column in param_units:
                parameter = u.Quantity(value, unit=param_units[column])

            # If param describes a time, make it a `astropy.time.Time`
            elif column in TIME_ATTRS:
                parameter = Time(value, format=TIME_ATTRS[column])

            elif column in BOOL_ATTRS:
                parameter = bool(value)

            # Otherwise, simply set the parameter to its raw value
            else:
                parameter = value

            # Attributes should be all lowercase:
            setattr(self, column.lower(), parameter)

    def __repr__(self):
        return ('<{0}: name="{1}" from exoplanets.org>'
                .format(self.__class__.__name__, self.name))
