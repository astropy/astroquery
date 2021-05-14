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
and a mapping between the new and deprecated names.

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
    K2-18 b         b    K2-18                  TIC 388804061 ...      -0.026 9.135&plusmn;0.026   8.899       0.019      -0.019 172.560141,7.5878315
        ...       ...      ...     ...      ...           ... ...         ...                ...     ...         ...         ...                  ...
    K2-18 b         b    K2-18                  TIC 388804061 ...      -0.026 9.135&plusmn;0.026   8.899       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18                  TIC 388804061 ...      -0.026 9.135&plusmn;0.026   8.899       0.019      -0.019 172.560141,7.5878315
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
    pl_name pl_letter hostname hd_name hip_name     tic_id    ...          x                   y                   z            htm20         sky_coord      
                                                            ...                                                                              deg,deg       
    str7     str1     str5     str1    str1       str13     ...       float64             float64             float64         int32           object       
    ------- --------- -------- ------- -------- ------------- ... ------------------- ------------------- ------------------- ---------- --------------------
    K2-18 b         b    K2-18                  TIC 388804061 ... -0.9828986469005482 0.12835161653867366 0.13204587253292302 -244884223 172.560141,7.5878315
    K2-18 c         c    K2-18                  TIC 388804061 ... -0.9828986469005482 0.12835161653867366 0.13204587253292302 -244884223 172.560141,7.5878315


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
        ...        ...          ...       ...     ...          ... ...      ...           ...           ...         ...       ...                 ...
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
        125


2. The list of confirmed planets discovered by TESS and their host star coordinates:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="pscomppars", select="pl_name,ra,dec",
    ...                                     where="disc_facility like '%TESS%'")
    <QTable masked=True length=125>
    pl_name         ra         dec           sky_coord       
                    deg         deg            deg,deg        
        str15       float64     float64           object        
    ------------- ----------- ----------- ----------------------
    WD 1856+534 b  284.415675  53.5090244  284.415675,53.5090244
    HD 213885 b 338.9837166  -59.864829 338.9837166,-59.864829
            ...         ...         ...                    ...
        TOI-257 b  47.5172608 -50.8322632 47.5172608,-50.8322632
        HD 5278 b  12.5467785 -83.7437671 12.5467785,-83.7437671
    LHS 1478 b  44.3388743  76.5514045  44.3388743,76.5514045


3. The list of confirmed planets discovered using microlensing that have data available in the archive:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="pscomppars", where="discoverymethod like 'Microlensing'")
    <QTable masked=True length=108>
           pl_name        pl_letter       hostname      hd_name hip_name ...          y                   z                  htm20          sky_coord       
                                                                         ..    .                                                                 deg,deg        
            str24            str1          str22          str1    str1   ...       float64             float64               int32            object        
    --------------------- --------- ------------------- ------- -------- ... ------------------- -------------------- -----------     ----------------------
    OGLE-2016-BLG-1227L b         b OGLE-2016-BLG-1227L                  ... -0.8289213204458156  -0.5557121192123485  -768415656     265.597125,-33.7597778
    OGLE-2015-BLG-0966L b         b OGLE-2015-BLG-0966L                  ... -0.8740141511624064  -0.4855286069187158  2084638177      268.75425,-29.0471111
                      ...       ...                 ...     ...      ... ...                 ...                  ...         ..    .                    ...
    OGLE-2017-BLG-0482L b         b OGLE-2017-BLG-0482L                  ... -0.8612591541866998  -0.5079647920007812  -287458961     269.048889,-30.5283604
      MOA-2010-BLG-353L b         b   MOA-2010-BLG-353L                  ... -0.8884412773722796 -0.45854460452933654 -1953724135     271.303917,-27.2932333
    OGLE-2014-BLG-1722L c         c OGLE-2014-BLG-1722L                  ... -0.8527200352847211  -0.5220379872608265   361334854      268.75238,-31.4690552


4. The list of confirmed planets where the host star name starts with "Kepler" using a *wildcard search*:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="pscomppars", where="hostname like 'Kepler%'", order="hostname")
    <QTable masked=True length=2366>
      pl_name    pl_letter  hostname  hd_name hip_name ...          x                   y                  z                 htm20          sky_coord       
                                                       ..    .                                                                                   deg,deg        
       str14        str1     str12      str9    str9   ...       float64             float64            float64              int32            object        
    ------------ --------- ---------- ------- -------- ... ------------------- ------------------- ------------------ -----------     ----------------------
     Kepler-10 c         c  Kepler-10                  ... 0.17284092708557064 -0.6157551422018003 0.7687467845631883   512815427      285.679298,50.2414842
     Kepler-10 b         b  Kepler-10                  ... 0.17284092708557064 -0.6157551422018003 0.7687467845631883   512815427      285.679298,50.2414842
             ...       ...        ...     ...      ... ...                 ...                 ...                ...         ..    .                    ...
    Kepler-997 b         b Kepler-997                  ...  0.2120139905204571 -0.6076812103558353 0.7653584875103029   604179197     289.2333767,49.9388952
    Kepler-998 b         b Kepler-998                  ... 0.29409419078908217 -0.5833667239066759 0.7570943616105639  1883599570     296.7541629,49.2087085
    Kepler-999 b         b Kepler-999                  ...  0.3425231804882674 -0.6014704986342327 0.7217417198007119 -1948748132     299.6604865,46.1984679


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
     K00124.01   2015-09-24
           ...          ...
     K06823.01   2018-08-16
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
