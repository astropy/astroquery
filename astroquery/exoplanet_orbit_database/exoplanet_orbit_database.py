# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
import os

from astropy.utils.data import download_file
from astropy.io import ascii
from astropy.table import QTable
import astropy.units as u
from astropy.coordinates import SkyCoord

__all__ = ['ExoplanetOrbitDatabase']

EXOPLANETS_CSV_URL = 'http://exoplanets.org/csv-files/exoplanets.csv'
TIME_ATTRS = {'TT': 'jd', 'T0': 'jd'}
BOOL_ATTRS = ('ASTROMETRY', 'BINARY', 'EOD', 'KDE', 'MICROLENSING', 'MULT',
              'SE', 'TIMING', 'TRANSIT', 'TREND')


class ExoplanetOrbitDatabaseClass(object):
    """
    Exoplanet Orbit Database querying object. Use the ``get_table`` or
    ``query_planet`` methods to get information about exoplanets via the
    Exoplanet Orbit Database.
    """
    def __init__(self):
        self._param_units = None
        self._table = None

    @property
    def param_units(self):
        if self._param_units is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            units_file = open(os.path.join(module_dir, 'data',
                                           'exoplanet_orbit_database_units.json'))
            self._param_units = json.load(units_file)

        return self._param_units

    def get_table(self, cache=True, show_progress=True, table_path=None):
        """
        Download (and optionally cache) the `Exoplanet Orbit Database planets
        table <http://www.exoplanets.org>`_.

        Parameters
        ----------
        cache : bool (optional)
            Cache exoplanet table to local astropy cache? Default is `True`.
        show_progress : bool (optional)
            Show progress of exoplanet table download (if no cached copy is
            available). Default is `True`.
        table_path : str (optional)
            Path to a local table file. Default `None` will trigger a
            download of the table from the internet.

        Returns
        -------
        table : `~astropy.table.QTable`
            Table of exoplanet properties.
        """
        if self._table is None:
            if table_path is None:
                table_path = download_file(EXOPLANETS_CSV_URL, cache=cache,
                                           show_progress=show_progress)
            exoplanets_table = ascii.read(table_path, fast_reader=False)

            # Store column of lowercase names for indexing:
            lowercase_names = [i.lower().replace(" ", "")
                               for i in exoplanets_table['NAME'].data]
            exoplanets_table['NAME_LOWERCASE'] = lowercase_names
            exoplanets_table.add_index('NAME_LOWERCASE')

            # Create sky coordinate mixin column
            exoplanets_table['sky_coord'] = SkyCoord(ra=exoplanets_table['RA'] * u.hourangle,
                                                     dec=exoplanets_table['DEC'] * u.deg)

            # Assign units to columns where possible
            for col in exoplanets_table.colnames:
                if col in self.param_units:
                    # Check that unit is implemented in this version of astropy
                    try:
                        exoplanets_table[col].unit = u.Unit(self.param_units[col])
                    except ValueError:
                        print(f"WARNING: Unit {self.param_units[col]} not recognised")

            self._table = QTable(exoplanets_table)

        return self._table

    def query_planet(self, planet_name, table_path=None):
        """
        Get table of exoplanet properties.

        Parameters
        ----------
        planet_name : str
            Name of planet
        table_path : str (optional)
            Path to a local table file. Default `None` will trigger a
            download of the table from the internet.

        Returns
        -------
        table : `~astropy.table.QTable`
            Table of one exoplanet's properties.
        """

        exoplanet_table = self.get_table(table_path=table_path)
        return exoplanet_table.loc[planet_name.strip().lower().replace(' ', '')]


ExoplanetOrbitDatabase = ExoplanetOrbitDatabaseClass()
