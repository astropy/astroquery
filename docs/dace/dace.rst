.. doctest-skip-all

.. _astroquery.dace:

************************
DACE (`astroquery.dace`)
************************

This module let you query DACE (Data Analysis Center for Exoplanets) data. This project is developed
at Observatory of Geneva and can be accessed online at https://dace.unige.ch


API
===

Query radial velocities
-----------------------
If you need to get radial velocities data for an object you can do the following and get a `~astropy.table.Table` :

.. code-block:: python

    >>> from astroquery.dace import Dace
    >>> radial_velocities_table = Dace.query_radial_velocities('HD40307')
    >>> print(radial_velocities_table)

          rjd                 rv               rv_err        ins_name
    ------------------ ------------------ ------------------ --------- ...
    51131.82401522994   31300.4226771379  5.420218247708816 CORALIE98
    51139.809670339804   31295.5671320506 4.0697289792344185 CORALIE98
    51188.67579095997   31294.3391634734 3.4386352834851026 CORALIE98
    51259.531961040106   31298.3278930888 7.0721030870398245 CORALIE98

               ...                ...                ...       ...
    56403.48691046983   31333.3379143329 0.5476157667089154   HARPS03
    56596.82446234021   31334.9563430348  0.508056405864858   HARPS03
    56602.871036310215   31337.4095684621 0.4167374664543639   HARPS03

Reference/API
=============

.. automodapi:: astroquery.dace
    :no-inheritance-diagram: