.. doctest-skip-all

.. _astroquery.esasky:

************************************
ESASky Queries (`astroquery.esasky`)
************************************

Getting started
===============

This is a python interface for querying the ESASky web service. This supports
querying an object as well as querying a region around the target. For region
queries, the region dimensions may be specified as a
radius. The queries may be further constrained by specifying 
a choice of catalogs or missions.

Get the available catalog names
-------------------

If you know the names of all the available catalogs you can use
:meth:`~astroquery.esasky.ESASkyClass.list_catalogs`:

.. code-block:: python

    >>> catalog_list = ESASky.list_catalogs()
    >>> print(catalog_list)
		['INTEGRAL', 'XMM-EPIC', 'XMM-OM', 'XMM-SLEW', 'Tycho-2', 'Gaia DR1 TGAS', 'Hipparcos-2', 'HSC', 'Planck-PGCC2', 'Planck-PCCS2E', 'Planck-PCCS2-HFI', 'Planck-PCCS2-LFI', 'Planck-PSZ']

Get the available maps mission names
-------------------

If you know the names of all the available maps missions you can use
:meth:`~astroquery.esasky.ESASkyClass.list_maps`:

.. code-block:: python

    >>> maps_list = ESASky.list_maps()
    >>> print(maps_list)
    	['INTEGRAL', 'XMM-EPIC', 'SUZAKU', 'XMM-OM-OPTICAL', 'XMM-OM-UV', 'HST', 'Herschel', 'ISO']

Reference/API
=============

.. automodapi:: astroquery.esasky
    :no-inheritance-diagram:
