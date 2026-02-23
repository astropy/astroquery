# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ExoMol database query module for astroquery.
Wraps RADIS ExoMol reader (radis.io.exomol) into astroquery BaseQuery pattern.

References
----------
Tennyson et al. 2020, J. Quant. Spectrosc. Radiat. Transf.
https://www.exomol.com
RADIS: https://github.com/radis/radis (issue #925)
"""

from astropy.table import Table
from astroquery.query import BaseQuery
from astroquery import log

__all__ = ["ExoMol", "ExoMolClass"]

EXOMOL_URL = "https://www.exomol.com"


class ExoMolClass(BaseQuery):
    """
    Queries the `ExoMol <https://www.exomol.com>`_ database for molecular
    line lists used in exoplanet atmosphere modelling.

    This module wraps the RADIS ExoMol reader (``radis.io.exomol``) and
    exposes it via the standard astroquery ``BaseQuery`` interface, returning
    ``astropy.table.Table`` objects.

    Examples
    --------
    Query CO lines between 2000-2100 cm^-1::

        from astroquery.linelists.exomol import ExoMol
        result = ExoMol.query_lines('CO',
                                    load_wavenum_min=2000,
                                    load_wavenum_max=2100)
        print(result)
    """

    URL = EXOMOL_URL
    TIMEOUT = 60

    def get_molecule_list(self, *, cache=True):
        """
        Retrieve list of all molecules available in ExoMol.

        Parameters
        ----------
        cache : bool, optional
            Cache HTTP response. Default ``True``.

        Returns
        -------
        list of str
            Sorted list of molecule names available in ExoMol.
        """
        url = f"{self.URL}/db/exomol.all"
        response = self._request("GET", url, cache=cache, timeout=self.TIMEOUT)
        response.raise_for_status()
        molecules = []
        for line in response.text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split()
                if parts:
                    molecules.append(parts[0])
        return sorted(list(set(molecules)))

    def get_databases(self, molecule, isotopologue=None, *, cache=True):
        """
        Get available line list databases for a given molecule.

        Parameters
        ----------
        molecule : str
            Molecule formula e.g. ``'H2O'``, ``'CO'``, ``'CH4'``.
        isotopologue : str, optional
            Isotopologue slug e.g. ``'1H2-16O'``. If ``None``, uses default.
        cache : bool, optional
            Cache results. Default ``True``.

        Returns
        -------
        list of str
            Available database names for this molecule.
        """
        from radis.api.exomolapi import get_exomol_database_list
        from radis.api.exomolapi import get_exomol_full_isotope_name

        iso_name = get_exomol_full_isotope_name(molecule, 1)
        dbs, _ = get_exomol_database_list(molecule, iso_name)
        return dbs

    def query_lines(
        self,
        molecule,
        database=None,
        isotopologue="1",
        load_wavenum_min=None,
        load_wavenum_max=None,
        broadening_species=None,
        *,
        cache=True,
    ):
        """
        Fetch ExoMol line list for a given molecule.

        Parameters
        ----------
        molecule : str
            Molecule formula e.g. ``'H2O'``, ``'CO'``, ``'SiO'``.
        database : str, optional
            ExoMol database name e.g. ``'POKAZATEL'`` for H2O.
            If ``None``, uses the ExoMol-recommended database.
        isotopologue : str, optional
            Isotopologue number. Default ``'1'`` (most abundant).
        load_wavenum_min : float, optional
            Minimum wavenumber in cm^-1.
        load_wavenum_max : float, optional
            Maximum wavenumber in cm^-1.
        broadening_species : str or list of str, optional
            Pressure-broadening partner(s).
            Examples: ``'H2'``, ``['H2', 'He']``, ``'air'``.
            If ``None``, downloads all available broadening files.
            See RADIS issue #917 for broadening parameter details.
        cache : bool, optional
            Cache downloaded line list files. Default ``True``.

        Returns
        -------
        `~astropy.table.Table`
            Line list table with columns for wavenumber (wav),
            line intensity (int), Einstein A coefficient (A),
            and lower/upper state energies (El, Eu).

        Examples
        --------
        Query CO lines::

            from astroquery.linelists.exomol import ExoMol
            result = ExoMol.query_lines('CO',
                                        load_wavenum_min=2000,
                                        load_wavenum_max=2100)

        Query H2O with H2+He broadening::

            result = ExoMol.query_lines('H2O',
                                        database='POKAZATEL',
                                        broadening_species=['H2', 'He'],
                                        load_wavenum_min=1000,
                                        load_wavenum_max=1100)
        """
        from radis.io.exomol import fetch_exomol

        log.info(
            f"Querying ExoMol for {molecule} "
            f"[{load_wavenum_min}-{load_wavenum_max} cm-1]"
        )

        df = fetch_exomol(
            molecule=molecule,
            database=database,
            isotope=isotopologue,
            load_wavenum_min=load_wavenum_min,
            load_wavenum_max=load_wavenum_max,
            broadening_species=broadening_species
            if broadening_species is not None
            else "air",
            cache=cache,
            verbose=False,
        )
        return df if isinstance(df, Table) else Table.from_pandas(df)

    def get_partition_function(
        self, molecule, database=None, isotopologue="1", *, cache=True
    ):
        """
        Get partition function Q(T) for a molecule from ExoMol.

        Parameters
        ----------
        molecule : str
            Molecule formula e.g. ``'CO'``, ``'H2O'``.
        database : str, optional
            ExoMol database name. If ``None``, uses recommended database.
        isotopologue : str, optional
            Isotopologue number. Default ``'1'``.
        cache : bool, optional
            Cache downloaded files. Default ``True``.

        Returns
        -------
        `~astropy.table.Table`
            Table with columns for temperature T (K) and partition
            function Q(T).
        """
        from radis.io.exomol import fetch_exomol

        df = fetch_exomol(
            molecule=molecule,
            database=database,
            isotope=isotopologue,
            return_partition_function=True,
            cache=cache,
            verbose=False,
        )
        return df if isinstance(df, Table) else Table.from_pandas(df)


ExoMol = ExoMolClass()
