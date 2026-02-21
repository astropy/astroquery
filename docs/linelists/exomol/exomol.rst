.. _astroquery.linelists.exomol:

****************************************************************
ExoMol Line List Queries (`astroquery.linelists.exomol`)
****************************************************************

Overview
========

The `~astroquery.linelists.exomol` module provides access to the
`ExoMol database <https://www.exomol.com>`_, the primary source of
high-temperature molecular line lists for exoplanet atmosphere modelling.

ExoMol 2024 contains 91 molecules and ~10\ :sup:`12` transitions —
including species critical for JWST atmosphere retrieval such as
H\ :sub:`2`\ O, CO, CH\ :sub:`4`, NH\ :sub:`3`, and HCN.

This module wraps RADIS's mature ExoMol reader (``radis.io.exomol``,
see `radis/radis#925 <https://github.com/radis/radis/issues/925>`_)
into the standard astroquery `~astroquery.query.BaseQuery` pattern.

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

Query with broadening species (critical for JWST H/He atmosphere models)::

    result = ExoMol.query_lines(
        molecule='H2O',
        database='POKAZATEL',
        broadening_species=['H2', 'He'],
        load_wavenum_min=1000,
        load_wavenum_max=1100,
    )

Get partition function Q(T)::

    pf = ExoMol.get_partition_function('CO')
    print(pf)

Reference / API
===============

.. automodule:: astroquery.linelists.exomol.core
   :members:
