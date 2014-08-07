.. doctest-skip-all

.. _astroquery.ogle:

********************************
OGLE Queries (`astroquery.ogle`)
********************************

Getting started
===============

The Optical Gravitational Lensing Experiment III (OGLE-III) stores information
on the interstellar extinction towards the Galactic Bulge. The
`astroquery.ogle` module queries the online extinction calculator_ and returns
an `~astropy.table.Table` instance with the same data. To run a single query
using an `astropy.coordinates` instance use:

.. code-block:: python

    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> from astroquery.ogle import Ogle
    >>> co = coordinates.SkyCoord(0*u.deg, 3*u.deg, frame='galactic')
    >>> t = Ogle.query_region(coord=co)

Arguments can be passed to choose the interpolation algorithm, quality factor,
and coordinate system. Multiple coordinates may be queried simultaneously by
passing a list-like object of string/float values or a list-like object of
`astropy.coordinates` instances. All of coordinates will be internally converted
to FK5.

.. code-block:: python

    >>> # list of coordinate instances
    >>> co_list = [co, co, co]
    >>> t1 = Ogle.query_region(coord=co_list)
    >>> # (2 x N) list of values
    >>> co_list_values = [[0, 0, 0], [3, 3, 3]]
    >>> t2 = Ogle.query_region(coord=co_list_values, coord_sys='LB')

Note that non-Astropy coordinates may not be supported in a future version.


Reference/API
=============

.. automodapi:: astroquery.ogle
    :no-inheritance-diagram:

.. _calculator: http://ogle.astrouw.edu.pl/
