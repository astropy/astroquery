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

.. doctest-remote-data::

    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> from astroquery.ogle import Ogle
    >>> co = SkyCoord(0*u.deg, 3*u.deg, frame='galactic')
    >>> t = Ogle.query_region(coord=co)

Arguments can be passed to choose the interpolation algorithm, quality factor,
and coordinate system. Multiple coordinates may be queried simultaneously by
passing a vector SkyCoord object. All of coordinates will be internally converted
to FK5.

.. doctest-remote-data::

    >>> # list of coordinate instances
    >>> co_list = [co, co, co]
    >>> t1 = Ogle.query_region(coord=co_list)
    >>> # (2 x N) list of values
    >>> co_list_values = SkyCoord([0, 1, 2], [3, 3, 3], unit=u.deg, frame='galactic')
    >>> t2 = Ogle.query_region(coord=co_list_values, coord_sys='LB')

Note that non-Astropy coordinates may not be supported in a future version.


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.ogle import Ogle
    >>> Ogle.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.ogle
    :no-inheritance-diagram:

.. _calculator: https://ogle.astrouw.edu.pl/
