.. _astroquery.dace:

************************
DACE (`astroquery.dace`)
************************

This module let you query DACE (Data Analysis Center for Exoplanets) data. This project is developed
at Observatory of Geneva and can be accessed online at https://dace.unige.ch

Getting started
===============


Query radial velocities
-----------------------
If you need to get radial velocities data for an object you can do the following and get a `~astropy.table.Table` :


.. doctest-remote-data::

    >>> from astroquery.dace import Dace
    >>> radial_velocities_table = Dace.query_radial_velocities('HD40307')
    >>> radial_velocities_table.pprint(max_lines=5, max_width=120)
       berv       berv_err ... date_night                                  raw_file
    ----------------- -------- ... ---------- -------------------------------------------------------------------------
    1.73905237267071      NaN ... 1998-11-13 coralie98/DRS-3.3/reduced/1998-11-13/CORALIE.1998-11-14T07:42:28.001.fits
    1.30280483191029      NaN ... 1998-11-21 coralie98/DRS-3.3/reduced/1998-11-21/CORALIE.1998-11-22T07:21:45.001.fits
                 ...      ... ...        ...                                                                       ...
    -3.37421721287255      NaN ... 2014-03-31       harps/DRS-3.5/reduced/2014-03-31/HARPS.2014-03-31T23:53:00.821.fits
    -3.32906204496065      NaN ... 2014-04-05       harps/DRS-3.5/reduced/2014-04-05/HARPS.2014-04-06T01:00:15.375.fits
    Length = 600 rows


Reference/API
=============

.. automodapi:: astroquery.dace
    :no-inheritance-diagram:
