# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import json
import os
from astropy.utils.data import download_file
from astropy.io import ascii
from astropy.table import QTable
from astropy.coordinates import SkyCoord
import astropy.units as u

__all__ = ['NasaExoplanetArchive']

EXOPLANETS_CSV_URL = ('http://exoplanetarchive.ipac.caltech.edu/cgi-bin/'
                      'nstedAPI/nph-nstedAPI?table=exoplanets')
TIME_ATTRS = {'rowupdate': 'iso'}
BOOL_ATTRS = ('pl_kepflag', 'pl_ttvflag', 'pl_k2flag', 'st_massblend',
              'st_optmagblend', 'st_radblend', 'st_teffblend')


class NasaExoplanetArchiveClass(object):
    """
    Exoplanet Archive querying object. Use the ``get_confirmed_planets_table``
    or ``query_planet`` methods to get information about exoplanets via the NASA
    Exoplanet Archive.
    """
    def __init__(self):
        self._param_units = None
        self._table = None

    @property
    def param_units(self):
        if self._param_units is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            units_file = open(os.path.join(module_dir, 'data',
                                           'exoplanet_nexsci_units.json'))
            self._param_units = json.load(units_file)

        return self._param_units

    def get_confirmed_planets_table(self, cache=True, show_progress=True,
                                    table_path=None, all_columns=False):
        """
        Download (and optionally cache) the `NExScI Exoplanet Archive Confirmed
        Planets table <http://exoplanetarchive.ipac.caltech.edu/index.html>`_.

        The Exoplanet Archive table returns lots of columns of data. A full
        description of the columns can be found `here
        <https://exoplanetarchive.ipac.caltech.edu/docs/API_exoplanet_columns.html>`_

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
        all_columns : bool (optional)
            Return all available columns. The default returns only the
            columns in the default category at the link above.

        Returns
        -------
        table : `~astropy.table.QTable`
            Table of exoplanet properties.
        """
        if self._table is None or not cache:
            if table_path is None:
                exoplanets_url = EXOPLANETS_CSV_URL
                if all_columns:
                    exoplanets_url = EXOPLANETS_CSV_URL + '&select=*'

                table_path = download_file(exoplanets_url, cache=cache,
                                           show_progress=show_progress,
                                           timeout=120)
            exoplanets_table = ascii.read(table_path)

            # Store column of lowercase names for indexing:
            lowercase_names = [host_name.lower().replace(' ', '') + letter
                               for host_name, letter in
                               zip(exoplanets_table['pl_hostname'].data,
                                   exoplanets_table['pl_letter'].data)]
            exoplanets_table['NAME_LOWERCASE'] = lowercase_names
            exoplanets_table.add_index('NAME_LOWERCASE')

            # Create sky coordinate mixin column
            exoplanets_table['sky_coord'] = SkyCoord(ra=exoplanets_table['ra'] * u.deg,
                                                     dec=exoplanets_table['dec'] * u.deg)

            # Assign units to columns where possible
            for col in exoplanets_table.colnames:
                if col in self.param_units:
                    # Check that unit is implemented in this version of astropy
                    if hasattr(u, self.param_units[col]):
                        exoplanets_table[col].unit = u.Unit(self.param_units[col])

            self._table = QTable(exoplanets_table)

        return self._table

    def query_planet(self, planet_name, **kwargs):
        """
        Get table of exoplanet properties.

        Parameters
        ----------
        planet_name : str
            Name of planet
        kwargs : dict (optional)
            Extra keyword arguments passed to ``get_confirmed_planets_table``.

        Return
        ------
        table : `~astropy.table.QTable`
            Table of one exoplanet's properties.
        """

        exoplanet_table = self.get_confirmed_planets_table(**kwargs)
        return exoplanet_table.loc[planet_name.strip().lower().replace(' ', '')]


NasaExoplanetArchive = NasaExoplanetArchiveClass()
