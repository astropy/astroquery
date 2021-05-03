.. doctest-skip-all

.. _astroquery.nasa_exoplanet_archive:

************************************************************
NASA Exoplanet Archive (`astroquery.nasa_exoplanet_archive`)
************************************************************

This module can be used to query the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu>`_ via
`the TAP service <https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html>`_ or
`the API <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_.
A full discussion of the available tables and query syntax through the two interfaces is available at [1]_ and [2]_. 
More information about the development of a more integrated NASA Exoplanet Archive and ongoing transition to
fully TAP supported services can be found at [3]_.

*NOTE*: the ``exoplanet`` and ``exomultpars`` tables are no longer available and have been replaced by the 
Planetary Systems table (``ps``). Likewise, the `compositepars` table has been replaced by the 
Planetary Systems Composite Parameters table (``pscomppars``). Both the ``ps`` and ``pscomppars`` tables are accessible 
through the Exoplanet Archive TAP service. Database column names have changed; 
`this document <https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html>`_ contains the current definitions 
and a mapping between the new and deprecated names. The ``ps`` table 

Query methods
=============

The `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_object` method can be used to query for a specific planet or planet host.
For example, the following query searches the ``ps`` table of confirmed exoplanets for information about the planet K2-18 b.

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_object("K2-18 b")
    <QTable masked=True length=11>
    pl_name pl_letter hostname hd_name hip_name     tic_id    ... sy_hmagerr2     sy_hmagstr     sy_kmag sy_kmagerr1 sy_kmagerr2      sky_coord      
                                                            ...                                                                      deg,deg       
    str7     str1     str5     str1    str1       str13     ...   float64         str18        float64   float64     float64          object       
    ------- --------- -------- ------- -------- ------------- ... ----------- ------------------ ------- ----------- ----------- --------------------
    K2-18 b         b    K2-18                  TIC 388804061 ...      -0.026 9.135&plusmn;0.026   8.899       0.019      -0.019 172.560141,7.5878315
        ...       ...      ...     ...      ...           ... ...         ...                ...     ...         ...         ...                  ...
    K2-18 b         b    K2-18                  TIC 388804061 ...      -0.026 9.135&plusmn;0.026   8.899       0.019      -0.019 172.560141,7.5878315


Similarly, cone searches can be executed using the `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_region` method:

.. code-block:: python

    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord
    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_region(
    ...     table="pscomppars", coordinates=SkyCoord(ra=172.56 * u.deg, dec=7.59 * u.deg),
    ...     radius=1.0 * u.deg)
    <QTable masked=True length=2>
    pl_name pl_letter hostname hd_name hip_name ...          x                  y                   z            htm20         sky_coord      
                                                ...                                                                             deg,deg       
    str7     str1     str5     str1    str1   ...       float64            float64             float64         int32           object       
    ------- --------- -------- ------- -------- ... ------------------- ------------------ ------------------- ---------- --------------------
    K2-18 c         c    K2-18                  ... -0.9828986469005482 0.1283516165386736 0.13204587253292302 -244884223 172.560141,7.5878315
    K2-18 b         b    K2-18                  ... -0.9828986469005482 0.1283516165386736 0.13204587253292302 -244884223 172.560141,7.5878315


The most general queries can be performed using the `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_criteria` method.
For example, a full table can be queried as follows:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="cumulative", select="*")
    <QTable masked=True length=9564>
    kepid   kepoi_name kepler_name      ra     ra_err    ra_str    ... koi_srho koi_srho_err1 koi_srho_err2 koi_fittype koi_score      sky_coord     
                                       deg      deg                ...                                                                  deg,deg      
     int64      str9       str15      float64  float64    str12     ... float64     float64       float64        str7     float64         object      
    -------- ---------- ------------ --------- ------- ------------ ... -------- ------------- ------------- ----------- --------- -------------------
    10797460  K00752.01 Kepler-227 b 291.93423     0.0 19h27m44.22s ...  3.20796       0.33173      -1.09986     LS+MCMC       1.0 291.93423,48.141651
    10797460  K00752.02 Kepler-227 c 291.93423     0.0 19h27m44.22s ...  3.02368       2.20489      -2.49638     LS+MCMC     0.969 291.93423,48.141651
       ...        ...       ...         ...        ...    ...       ...      ...           ...           ...         ...       ...                 ...
    10147276  K07987.01              294.16489     0.0 19h36m39.57s ...  8.97692      23.11894      -8.63287     LS+MCMC     0.021 294.16489,47.176281
    10155286  K07988.01              296.76288     0.0 19h47m03.09s ... 85.88623      17.31552     -41.55038     LS+MCMC     0.092 296.76288,47.145142
    10156110  K07989.01              297.00977     0.0 19h48m02.34s ...  1.40645       0.16166      -0.95964     LS+MCMC       0.0 297.00977,47.121021


Example queries
===============

Specific searches can be executed using the ``where``, ``select``, ``order``, and other parameters as described in the documentation [1]_, [2]_.

In this section, we demonstrate

1. The number of confirmed planets discovered by TESS:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="pscomppars", select="count(*)",
    ...                                     where="disc_facility like '%TESS%'")
    <QTable masked=True length=1>
    count(*)
    int32  
    --------
        123


2. The list of confirmed planets discovered by TESS and their host star coordinates:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="pscomppars", select="pl_name,ra,dec",
    ...                                     where="disc_facility like '%TESS%'")
    <QTable masked=True length=123>
    pl_name        ra         dec           sky_coord       
                                             deg,deg        
    str15      float64     float64            object        
    ---------- ----------- ----------- ----------------------
    TOI-763 b  194.468098 -39.7580613 194.468098,-39.7580613
    DS Tuc A b 354.9154673  -69.196043 354.9154673,-69.196043
        ...         ...         ...                    ...
    NGTS-11 b  23.5214497 -14.4191493 23.5214497,-14.4191493
    TOI-892 b   86.738228 -11.2353401  86.738228,-11.2353401
    LHS 1478 b  44.3388743  76.5514045  44.3388743,76.5514045


3. The list of confirmed planets discovered using microlensing that have data available in the archive:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="pscomppars", where="dicoverymethod like 'Microlensing'")
    <QTable masked=True length=108>
           pl_name            ra         dec           sky_coord       
                                                        deg,deg        
            str24          float64     float64           object        
    --------------------- ---------- ----------- ----------------------
    OGLE-2012-BLG-0724L b 268.968292 -29.8185278 268.968292,-29.8185278
    OGLE-2016-BLG-1190L b 269.717926 -27.6135559 269.717926,-27.6135559
                    ...        ...         ...                    ...
    OGLE-2015-BLG-0966L b  268.75425 -29.0471111  268.75425,-29.0471111
    OGLE-2012-BLG-0950L b 272.019257 -29.7315826 272.019257,-29.7315826
    OGLE-2012-BLG-0563L b   271.4905     -27.712       271.4905,-27.712


4. The list of confirmed planets where the host star name starts with "Kepler" using a *wildcard search*:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="pscomppars", where="hostname like 'Kepler%'", order="hostname")
    <QTable masked=True length=2366>
    pl_name    pl_letter  hostname  hd_name hip_name ...         x                   y                  z             htm20           sky_coord       
                                                    ...                                                                                deg,deg        
    str14          str1     str12      str9    str9   ...      float64             float64            float64          int32            object        
    ------------ --------- ---------- ------- -------- ... ------------------ ------------------- ------------------ ----------- ----------------------
    Kepler-10 c         c  Kepler-10                  ... 0.1728409270855706 -0.6157551422018002 0.7687467845631882   512815427  285.679298,50.2414842
    Kepler-10 b         b  Kepler-10                  ... 0.1728409270855706 -0.6157551422018002 0.7687467845631882   512815427  285.679298,50.2414842
            ...       ...        ...     ...      ... ...                ...                 ...                ...         ...                    ...
    Kepler-997 b         b Kepler-997                  ... 0.2120139905204571 -0.6076812103558352 0.7653584875103029   604179197 289.2333767,49.9388952
    Kepler-998 b         b Kepler-998                  ... 0.2940941907890821 -0.5833667239066758 0.7570943616105638  1883599570 296.7541629,49.2087085
    Kepler-999 b         b Kepler-999                  ... 0.3425231804882674 -0.6014704986342326 0.7217417198007118 -1948748132 299.6604865,46.1984679


5. The Kepler Objects of Interest that were vetted more recently than January 24, 2015 using a *date search*:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="koi", where="koi_vet_date>to_date('2015-01-24','yyyy-mm-dd')",
    ...     select="kepoi_name,koi_vet_date", order="koi_vet_date")
    <QTable length=34652>
    kepoi_name koi_vet_date
       str9       str10
    ---------- ------------
     K00866.01   2015-09-24
     K00867.01   2015-09-24
           ...          ...
     K06824.01   2018-08-16
     K06825.01   2018-08-16


References
==========

.. [1] `NASA Exoplanet Archive TAP Documentation <https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html>`_
.. [2] `NASA Exoplanet Archive API Documentation <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_
.. [3] `Developing a More Integrated NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu/docs/transition.html>`_


Reference/API
=============

.. automodapi:: astroquery.nasa_exoplanet_archive
    :no-inheritance-diagram:
