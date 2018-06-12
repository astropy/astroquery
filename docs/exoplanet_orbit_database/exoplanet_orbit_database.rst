.. doctest-skip-all

.. _astroquery.exoplanet_orbit_database:

****************************************************************
Exoplanet Orbit Database (`astroquery.exoplanet_orbit_database`)
****************************************************************

Accessing the planet table
==========================

You can access the complete tables from each table source, with units assigned
to columns wherever possible.

.. code-block:: python

        >>> from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
        >>> eod_table = ExoplanetOrbitDatabase.get_confirmed_planets_table()

        >>> eod_table[:2]
        <Table masked=True length=2>
        pl_hostname pl_letter pl_discmethod ... pl_nnotes rowupdate  NAME_LOWERCASE
                                            ...
           str27       str1       str29     ...   int64     str10        str29
        ----------- --------- ------------- ... --------- ---------- --------------
         Kepler-151         b       Transit ...         1 2014-05-14   kepler-151 b
         Kepler-152         b       Transit ...         1 2014-05-14   kepler-152 b

You can query for the row from each table corresponding to one exoplanet:

.. code-block:: python

        >>> from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
        >>> hatp11b = ExoplanetOrbitDatabase.query_planet('HAT-P-11 b')


Properties of a particular planet
=================================

The properties of each planet are stored in a table, with `columns defined by
the Exoplanet Orbit Database <http://exoplanets.org/help/common/data>`_. There
is also a special column of sky coordinates for each target, named ``sky_coord``.

.. code-block:: python

        >>> from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
        >>> hatp11b = ExoplanetOrbitDatabase.query_planet('HAT-P-11 b')

        >>> hatp11b['PER']  # Planet period
        <Quantity 4.8878162 d>

        >>> hatp11b['R']  # Planet radius
        <Quantity 0.422 jupiterRad>

        >>> hatp11b['sky_coord'] # Position of host star
        <SkyCoord (ICRS): (ra, dec) in deg
            ( 297.70891666,  48.08029444)>

Reference/API
=============

.. automodapi:: astroquery.exoplanet_orbit_database
    :no-inheritance-diagram:
