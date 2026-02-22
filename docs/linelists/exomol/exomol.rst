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

Getting Started
===============

List available molecules::

    from astroquery.linelists.exomol import ExoMol

    molecules = ExoMol.get_molecule_list()
    print(molecules[:10])

Get available databases for a molecule::

    databases = ExoMol.get_databases('H2O')
    print(databases)

Query CO line list in a wavenumber range::

    result = ExoMol.query_lines(
        molecule='CO',
        load_wavenum_min=2000,
        load_wavenum_max=2100,
    )
    print(result)

Get partition function Q(T)::

    pf = ExoMol.get_partition_function('CO')
    print(pf)
