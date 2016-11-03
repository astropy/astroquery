.. doctest-skip-all

************************************
HITRAN Queries (`astroquery.hitran`)
************************************

Getting started
===============

This module provides an interface to the `HITRAN`_ database API.  It can
download a data file including transitions for a particular molecule in a given
wavenumber range.  The file is downloaded in the `~hitran.cache_location`
directory and can be opened with a reader function that returns a table of
spectral lines including all accessible parameters.

Examples
========

This will download all transitions of the main isotopologue of water between
the wavenumbers of 3400 and 4100 cm\ :sup:`-1`\ .

.. code-block:: python

    >>> import os
    >>> from astroquery.hitran import read_hitran_file, cache_location, download_hitran
    >>> download_hitran(1, 1, 3400, 4100)
    >>> tbl = read_hitran_file(os.path.join(cache_location, 'H2O.data'))

Transitions are returned as an `~astropy.table.Table` instance.

Reference/API
=============

.. automodapi:: astroquery.hitran
    :no-inheritance-diagram:

.. _HITRAN: http://hitran.org
