.. doctest-skip-all

.. _astroquery.hitran:

************************************
HITRAN Queries (`astroquery.hitran`)
************************************

Getting started
===============

This module provides an interface to the high-resolution transmission molecular
absorption database API (`HITRAN`_).  The current version of the database
contains a compilation of spectroscopic parameters for 49 molecular species
along with their most significant isotopologues.  Using the ``hitran`` module you
can search transitions for a particular molecule in a given wavenumber range.

Examples
========

This will download all transitions of the main isotopologue of water between
the wavenumbers of 3400 and 4100 cm\ :sup:`-1`\ .  The expected type for the
parameters ``min_frequency`` and ``max_frequency`` is an AstroPy quantity.
The data are returned as an `~astropy.table.Table` instance.


.. code-block:: python

    >>> from astropy import units as u
    >>> from astroquery.hitran import Hitran
    >>> tbl = Hitran.query_lines(molecule_number=1,
                                 isotopologue_number=1,
                                 min_frequency=0. / u.cm,
                                 max_frequency=10. / u.cm)

Reference/API
=============

.. automodapi:: astroquery.hitran
    :no-inheritance-diagram:

.. _HITRAN: http://hitran.org
