.. doctest-skip-all
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

.. code-block:: python

    >>> from astroquery.gama import GAMA
    >>> result = GAMA.query_sql('SELECT * FROM SpecAll LIMIT 100')
    Downloading http://www.gama-survey.org/dr2/query/../tmp/GAMA_VHI6pj.fits
    |===========================================|  37k/ 37k (100.00%)        00s
    >>> print result
          SPECID       SURVEY SURVEY_CODE     RA    ... DIST IS_SBEST IS_BEST
    ------------------ ------ ----------- --------- ... ---- -------- -------
    131671727225700352   SDSS           1 132.16668 ...  0.1        1       1
    131671727229894656   SDSS           1 132.17204 ... 0.13        1       1
    131671727246671872   SDSS           1 132.24395 ... 0.13        1       1
    131671727255060480   SDSS           1  132.1767 ... 0.06        1       1
    131671727267643392   SDSS           1 132.63599 ... 0.05        1       1
    131671727271837696   SDSS           1 132.85366 ... 0.02        1       1
    131671727276032000   SDSS           1 132.70244 ... 0.03        1       1
    131671727292809216   SDSS           1 132.19579 ... 0.12        1       1
    131671727301197824   SDSS           1 132.57563 ...  0.0        1       1
    131671727309586432   SDSS           1 133.01007 ... 0.06        1       1
    131671727313780736   SDSS           1 132.76907 ... 0.04        1       1
    131671727322169344   SDSS           1 132.81014 ... 0.03        1       1
    131671727334752256   SDSS           1 132.85607 ... 0.02        1       1
    131671727338946560   SDSS           1 132.90222 ... 0.04        1       1
    131671727351529472   SDSS           1 133.00397 ... 0.05        1       1
    131671727355723776   SDSS           1 132.96032 ... 0.05        1       1
    131671727359918080   SDSS           1 132.92164 ... 0.03        1       1
                   ...    ...         ...       ... ...  ...      ...     ...
    131671727791931392   SDSS           1 131.59537 ... 0.03        1       1
    131671727796125696   SDSS           1 131.58167 ... 0.11        1       1
    131671727800320000   SDSS           1 131.47693 ... 0.05        1       1
    131671727804514304   SDSS           1 131.47471 ... 0.03        1       1
    131671727808708608   SDSS           1 131.60197 ... 0.03        1       1
    131671727825485824   SDSS           1 132.18426 ... 0.05        1       1
    131671727833874432   SDSS           1  132.2593 ... 0.05        1       1
    131671727838068736   SDSS           1  132.1901 ... 0.09        1       1
    131671727854845952   SDSS           1 132.30575 ... 0.04        1       1
    131671727859040256   SDSS           1   132.419 ... 0.04        1       1
    131671727867428864   SDSS           1 132.29052 ... 0.15        1       1
    131671727871623168   SDSS           1 132.37213 ... 0.01        1       1
    131671727880011776   SDSS           1 132.36358 ...  0.1        1       1
    131671727892594688   SDSS           1  132.3956 ... 0.05        1       1
    131671727896788992   SDSS           1 131.89562 ... 0.15        1       1
    131671727900983296   SDSS           1 131.85848 ... 0.05        1       1
    131671727905177600   SDSS           1 132.12958 ... 0.09        0       0

Reference/API
=============

.. automodapi:: astroquery.gama
    :no-inheritance-diagram:

.. _astropy.table.Table: http://docs.astropy.org/en/latest/table/index.html
