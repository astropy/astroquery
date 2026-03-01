# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
ExoMol database query module for astroquery.
Queries the ExoMol database directly via its API.

References
----------
Tennyson et al. 2020, J. Quant. Spectrosc. Radiat. Transf.
https://www.exomol.com
RADIS: https://github.com/radis/radis (issue #925)
"""

from astropy import units as u
from astropy.table import Table
from astroquery.query import BaseQuery
from astropy import log

__all__ = ["ExoMol", "ExoMolClass"]

EXOMOL_URL = "https://www.exomol.com"


class ExoMolClass(BaseQuery):
    """
    Queries the `ExoMol <https://www.exomol.com>`_ database for molecular
    line lists used in exoplanet atmosphere modelling.

    This module queries ExoMol directly and optionally uses RADIS
    (``radis``) for line list fetching via :meth:`query_lines`.

    .. note::

       The :meth:`query_lines` and :meth:`get_partition_function` methods
       require `RADIS <https://radis.readthedocs.io>`_ as an optional
       dependency. Install it with::

           pip install radis

       All other methods (``get_molecule_list``, ``get_databases``)
       work without RADIS.

    Examples
    --------
    Query CO lines between 2000-2100 cm\\ :sup:`-1`::

        from astropy import units as u
        from astroquery.linelists.exomol import ExoMol

        result = ExoMol.query_lines('CO',
                                    wavenum_min=2000*u.cm**-1,
                                    wavenum_max=2100*u.cm**-1)
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

    def get_databases(self, molecule, *, cache=True):
        """
        Get available line list databases for a given molecule.

        Scrapes the ExoMol website to find available databases.

        Parameters
        ----------
        molecule : str
            Molecule formula e.g. ``'H2O'``, ``'CO'``, ``'CH4'``.
        cache : bool, optional
            Cache results. Default ``True``.

        Returns
        -------
        list of str
            Available database names for this molecule.

        Examples
        --------
        .. code-block:: python

            from astroquery.linelists.exomol import ExoMol
            dbs = ExoMol.get_databases('H2O')
            print(dbs)  # doctest: +SKIP

        """
        try:
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(
                "The 'beautifulsoup4' package is required for get_databases(). "
                "Install it with: pip install beautifulsoup4"
            ) from e

        url = f"{self.URL}/data/molecules/{molecule}/"
        response = self._request("GET", url, cache=cache, timeout=self.TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        databases = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if (
                href.startswith(f"/data/molecules/{molecule}/")
                and href != f"/data/molecules/{molecule}/"
            ):
                db_name = href.rstrip("/").split("/")[-1]
                if db_name and db_name != molecule:
                    databases.append(db_name)

        return sorted(list(set(databases)))

    def query_lines(
        self,
        molecule,
        database=None,
        isotopologue="1",
        wavenum_min=None,
        wavenum_max=None,
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
        wavenum_min : `~astropy.units.Quantity`, optional
            Minimum wavenumber, e.g. ``2000*u.cm**-1``.
        wavenum_max : `~astropy.units.Quantity`, optional
            Maximum wavenumber, e.g. ``2100*u.cm**-1``.
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

            from astropy import units as u
            from astroquery.linelists.exomol import ExoMol

            result = ExoMol.query_lines('CO',
                                        wavenum_min=2000*u.cm**-1,
                                        wavenum_max=2100*u.cm**-1)

        Query H2O with H2+He broadening::

            result = ExoMol.query_lines('H2O',
                                        database='POKAZATEL',
                                        broadening_species=['H2', 'He'],
                                        wavenum_min=1000*u.cm**-1,
                                        wavenum_max=1100*u.cm**-1)
        """
        try:
            from radis.io.exomol import fetch_exomol
        except ImportError as e:
            raise ImportError(
                "The 'radis' package is required for query_lines(). "
                "Install it with: pip install radis"
            ) from e

        # Convert Quantity to float (cm^-1) for RADIS
        wavenum_min_value = None
        wavenum_max_value = None

        if wavenum_min is not None:
            if hasattr(wavenum_min, "unit"):
                wavenum_min_value = wavenum_min.to(u.cm**-1).value
            else:
                wavenum_min_value = float(wavenum_min)

        if wavenum_max is not None:
            if hasattr(wavenum_max, "unit"):
                wavenum_max_value = wavenum_max.to(u.cm**-1).value
            else:
                wavenum_max_value = float(wavenum_max)

        log.info(
            f"Querying ExoMol for {molecule} "
            f"[{wavenum_min_value}-{wavenum_max_value} cm-1]"
        )

        df = fetch_exomol(
            molecule=molecule,
            database=database,
            isotope=isotopologue,
            load_wavenum_min=wavenum_min_value,
            load_wavenum_max=wavenum_max_value,
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
        try:
            from radis.io.exomol import fetch_exomol
        except ImportError as e:
            raise ImportError(
                "The 'radis' package is required for get_partition_function(). "
                "Install it with: pip install radis"
            ) from e

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
