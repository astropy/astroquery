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


.. doctest-remote-data::

    >>> from astropy import units as u
    >>> from astroquery.hitran import Hitran
    >>> tbl = Hitran.query_lines(molecule_number=1,
    ...                            isotopologue_number=1,
    ...                            min_frequency=0. / u.cm,
    ...                            max_frequency=10. / u.cm)
    >>> tbl
    <Table length=27>
    molec_id local_iso_id    nu        sw    ... line_mixing_flag    gp     gpp
     int32      int32     float32   float32  ...      bytes1      float32 float32
    -------- ------------ -------- --------- ... ---------------- ------- -------
           1            1 0.072052 1.875e-30 ...                      9.0    11.0
           1            1 0.400571 2.528e-28 ...                     27.0    21.0
           1            1 0.741682 4.451e-25 ...                     39.0    33.0
         ...          ...      ...       ... ...              ...     ...     ...
           1            1 8.944491 3.361e-30 ...                     39.0    45.0
           1            1 9.795592 1.794e-27 ...                     39.0    45.0
           1            1   9.9215 6.136e-28 ...                     13.0    15.0


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.hitran import Hitran
    >>> Hitran.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.hitran
    :no-inheritance-diagram:

.. _HITRAN: https://hitran.org
