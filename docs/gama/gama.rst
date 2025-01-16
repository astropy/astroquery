.. _astroquery.gama:

********************************
GAMA Queries (`astroquery.gama`)
********************************

Getting started
===============

This module can be used to query the GAMA (Galaxy And Mass Assembly) survey,
second data release (DR2). Currently queries must be formulated in SQL. If
successful, the results are returned as a `~astropy.table.Table`.

SQL Queries
-----------


This sends an SQL query, passed as a string, to the GAMA server and returns
a `~astropy.table.Table`. For example, to return basic information on the
first 100 spectroscopic objects in the database:

.. doctest-remote-data::

    >>> from astroquery.gama import GAMA
    >>> result = GAMA.query_sql('SELECT * FROM SpecAll LIMIT 100')
    >>> print(result)
           SPECID       SURVEY SURVEY_CODE     RA    ... DIST IS_SBEST IS_BEST
    ------------------- ------ ----------- --------- ... ---- -------- -------
    1030358159811700736   SDSS           1 211.73487 ... 0.05        1       1
    1030358434689607680   SDSS           1 211.51452 ... 0.14        1       1
    1030358984445421568   SDSS           1 211.78462 ... 0.02        1       1
    1030359809079142400   SDSS           1 211.63878 ... 0.05        1       1
    1030360358834956288   SDSS           1 211.79006 ... 0.04        1       1
    1030360633712863232   SDSS           1 211.71473 ... 0.05        0       0
    1030361183468677120   SDSS           1 211.74528 ... 0.04        1       0
    1030361733224491008   SDSS           1 211.50587 ... 0.02        1       1
    1030363382491932672   SDSS           1 211.63321 ... 0.02        1       1
    1030363657369839616   SDSS           1 211.54913 ... 0.06        0       0
                    ...    ...         ...       ... ...  ...      ...     ...
    1031441727430354944   SDSS           1 212.46214 ... 0.06        1       1
    1031442002308261888   SDSS           1 212.37016 ... 0.11        1       1
    1031442552064075776   SDSS           1 212.43301 ... 0.08        1       1
    1031444751087331328   SDSS           1 212.37388 ...  0.1        1       1
    1031445300843145216   SDSS           1 212.34656 ... 0.02        1       1
    1031445575721052160   SDSS           1 212.89604 ... 0.03        1       1
    1031446125476866048   SDSS           1 212.75493 ... 0.03        1       1
    1031446400354772992   SDSS           1 212.90264 ... 0.04        1       1
    1031446950110586880   SDSS           1 212.96246 ... 0.05        1       1
    1031447774744307712   SDSS           1  213.0112 ... 0.09        1       1
    1031448324500121600   SDSS           1 212.70039 ... 0.05        0       0
    Length = 100 rows


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.gama import GAMA
    >>> GAMA.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.

    
Reference/API
=============

.. automodapi:: astroquery.gama
    :no-inheritance-diagram:

.. _astropy.table.Table: https://docs.astropy.org/en/latest/table/index.html
