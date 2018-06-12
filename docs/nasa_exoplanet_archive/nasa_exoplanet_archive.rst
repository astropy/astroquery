.. doctest-skip-all

.. _astroquery.nasa_exoplanet_archive:

************************************************************
NASA Exoplanet Archive (`astroquery.nasa_exoplanet_archive`)
************************************************************

Accessing the planet table
==========================

You can access the complete tables from each table source, with units assigned
to columns wherever possible.

.. code-block:: python

        >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
        >>> exoplanet_archive_table = NasaExoplanetArchive.get_confirmed_planets_table()

        >>> exoplanet_archive_table[:2]
        <Table masked=True length=2>
        pl_hostname pl_letter pl_discmethod ... pl_nnotes rowupdate  NAME_LOWERCASE
                                            ...
           str27       str1       str29     ...   int64     str10        str29
        ----------- --------- ------------- ... --------- ---------- --------------
         Kepler-151         b       Transit ...         1 2014-05-14   kepler-151 b
         Kepler-152         b       Transit ...         1 2014-05-14   kepler-152 b

You can query for the row from each table corresponding to one exoplanet:

.. code-block:: python

        >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
        >>> hatp11b = NasaExoplanetArchive.query_planet('HAT-P-11 b')


Properties of a particular planet
=================================

The properties of each planet are stored in a table, with `columns defined by
the NASA Explanet Archive <https://exoplanetarchive.ipac.caltech.edu/docs/API_exoplanet_columns.html>`_.
There is also a special column of sky coordinates for each target, named
``sky_coord``.

.. code-block:: python

        >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
        >>> hatp11b = NasaExoplanetArchive.query_planet('HAT-P-11 b')

        >>> hatp11b['pl_orbper']  # Planet period
        <Quantity 4.8878162 d>

        >>> hatp11b['pl_radj']  # Planet radius
        <Quantity 0.422 jupiterRad>

        >>> hatp11b['sky_coord'] # Position of host star
        <SkyCoord (ICRS): (ra, dec) in deg
            ( 297.709351,  48.080856)>

Reference/API
=============

.. automodapi:: astroquery.nasa_exoplanet_archive
    :no-inheritance-diagram:
