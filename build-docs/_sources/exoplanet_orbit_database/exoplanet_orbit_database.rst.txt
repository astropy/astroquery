.. _astroquery.exoplanet_orbit_database:

****************************************************************
Exoplanet Orbit Database (`astroquery.exoplanet_orbit_database`)
****************************************************************

Accessing the planet table
==========================

You can access the complete tables from each table source, with units assigned
to columns wherever possible.

.. doctest-remote-data::

        >>> from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
        >>> eod_table = ExoplanetOrbitDatabase.get_table()
        >>> eod_table[:2]
        <QTable length=2>
            A        AUPPER   ... NAME_LOWERCASE              sky_coord
            AU         AU     ...                              deg,deg
         float64    float64   ...     str19                    SkyCoord
        --------- ----------- ... -------------- -----------------------------------
        0.0780099  0.00130017 ...    kepler-107d 297.0282083332539,48.20861111111111
        0.0344721 0.000675924 ...   kepler-1049b  287.3467499971389,47.7729444445504

You can query for the row from each table corresponding to one exoplanet:

.. doctest-remote-data::

        >>> from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
        >>> hatp11b = ExoplanetOrbitDatabase.query_planet('HAT-P-11 b')


Properties of a particular planet
=================================

The properties of each planet are stored in a table, with `columns defined by
the Exoplanet Orbit Database <http://exoplanets.org/help/common/data>`_. There
is also a special column of sky coordinates for each target, named ``sky_coord``.

.. doctest-remote-data::

        >>> from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
        >>> hatp11b = ExoplanetOrbitDatabase.query_planet('HAT-P-11 b')
        >>> hatp11b['PER']  # Planet period
        <MaskedQuantity 4.8878162 d>
        >>> hatp11b['R']  # Planet radius
        <MaskedQuantity 0.422 jupiterRad>
        >>> hatp11b['sky_coord'] # Position of host star
        <SkyCoord (ICRS): (ra, dec) in deg
            (297.70890417, 48.08029444)>

Reference/API
=============

.. automodapi:: astroquery.exoplanet_orbit_database
    :no-inheritance-diagram:
