.. _astroquery.linelists.exomol:

ExoMol Line List Queries (`astroquery.linelists.exomol`)
*********************************************************

.. automodapi:: astroquery.linelists.exomol
    :no-inheritance-diagram:

Overview
========

The `~astroquery.linelists.exomol` module provides access to the
`ExoMol database <https://www.exomol.com>`_, the primary source of
high-temperature molecular line lists for exoplanet atmosphere modelling.

.. note::

    This module requires `radis <https://radis.readthedocs.io>`_ as a
    dependency (``pip install radis``). Results are returned as
    `~astropy.table.Table` objects; ``radis`` internally uses ``pandas``
    for data processing.

Getting Started
===============

List available molecules::

    from astroquery.linelists.exomol import ExoMol

    molecules = ExoMol.get_molecule_list()  # doctest: +SKIP
    print(molecules[:10])  # doctest: +SKIP

Get available databases for a molecule::

    databases = ExoMol.get_databases('H2O')  # doctest: +SKIP
    print(databases)  # doctest: +SKIP

Query CO line list in a wavenumber range::

    result = ExoMol.query_lines(
        molecule='CO',
        load_wavenum_min=2000,
        load_wavenum_max=2100,
    )
    print(result)  # doctest: +SKIP

Get partition function Q(T)::

    pf = ExoMol.get_partition_function('CO')
    print(pf)  # doctest: +SKIP
