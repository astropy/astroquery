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
.. doctest-remote-data::
    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_object("K2-18 b")
    <QTable masked=True length=11>
    pl_name pl_letter hostname ... sy_kmagerr1 sy_kmagerr2      sky_coord
                               ...                               deg,deg
      str7     str1     str5   ...   float64     float64          object
    ------- --------- -------- ... ----------- ----------- --------------------
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315
    K2-18 b         b    K2-18 ...       0.019      -0.019 172.560141,7.5878315


Similarly, cone searches can be executed using the `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_region` method:

.. code-block:: python
.. doctest-remote-data::

    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord
    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_region(
    ...     table="pscomppars", coordinates=SkyCoord(ra=172.56 * u.deg, dec=7.59 * u.deg),
    ...     radius=1.0 * u.deg)
    <QTable masked=True length=2>
    pl_name pl_letter hostname ...   htm20         sky_coord
                               ...                  deg,deg
      str7     str1     str5   ...   int32           object
    ------- --------- -------- ... ---------- --------------------
    K2-18 b         b    K2-18 ... -244884223 172.560141,7.5878315
    K2-18 c         c    K2-18 ... -244884223 172.560141,7.5878315


The most general queries can be performed using the `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_criteria` method.
For example, a full table can be queried as follows:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="cumulative", select="*")
    <QTable masked=True length=9564>
     kepid   kepoi_name kepler_name  ... koi_fittype koi_score      sky_coord
                                     ...                             deg,deg
     int64      str9       str15     ...     str7     float64         object
    -------- ---------- ------------ ... ----------- --------- -------------------
    10797460  K00752.01 Kepler-227 b ...     LS+MCMC       1.0 291.93423,48.141651
    10797460  K00752.02 Kepler-227 c ...     LS+MCMC     0.969 291.93423,48.141651
    10811496  K00753.01              ...     LS+MCMC       0.0 297.00482,48.134129
    10848459  K00754.01              ...     LS+MCMC       0.0  285.53461,48.28521
    10854555  K00755.01 Kepler-664 b ...     LS+MCMC       1.0   288.75488,48.2262
         ...        ...          ... ...         ...       ...                 ...
    10155286  K07988.01              ...     LS+MCMC     0.092 296.76288,47.145142
    10156110  K07989.01              ...     LS+MCMC       0.0 297.00977,47.121021

Example queries
===============

Specific searches can be executed using the ``where``, ``select``, ``order``, and other parameters as described in the documentation [1]_, [2]_.

In this section, we demonstrate

1. The number of confirmed planets discovered by TESS:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="pscomppars", select="count(*)",
    ...                                     where="disc_facility like '%TESS%'")
    <QTable masked=True length=1>
    count(*)
     int32
    --------
         131


2. The list of confirmed planets discovered by TESS and their host star coordinates:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="pscomppars", select="pl_name,ra,dec",
    ...                                     where="disc_facility like '%TESS%'")
    <QTable masked=True length=131>
       pl_name         ra         dec            sky_coord
                      deg         deg             deg,deg
        str15       float64     float64            object
    ------------- ----------- ----------- -----------------------
    WD 1856+534 b  284.415675  53.5090244   284.415675,53.5090244
      HD 213885 b 338.9837166  -59.864829  338.9837166,-59.864829
      HD 219666 b 349.5592665 -56.9039857 349.5592665,-56.9039857
              ...         ...         ...                     ...
        TOI-257 b  47.5172608 -50.8322632  47.5172608,-50.8322632
        HD 5278 b  12.5467785 -83.7437671  12.5467785,-83.7437671
       LHS 1478 b  44.3388743  76.5514045   44.3388743,76.5514045


3. The list of confirmed planets discovered using microlensing that have data available in the archive:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="pscomppars", where="discoverymethod like 'Microlensing'")
    <QTable masked=True length=108>
           pl_name        pl_letter ...    htm20           sky_coord
                                    ...                     deg,deg
            str24            str1   ...    int32             object
    --------------------- --------- ... ----------- -----------------------
    OGLE-2016-BLG-1227L b         b ...  -768415656  265.597125,-33.7597778
    OGLE-2015-BLG-0966L b         b ...  2084638177   268.75425,-29.0471111
    OGLE-2017-BLG-0173L b         b ...  1462336374  267.970612,-29.2713604
    OGLE-2017-BLG-1140L b         b ...  -925663673  266.883057,-24.5226669
                      ...       ... ...         ...                     ...
    OGLE-2012-BLG-0358L b         b ...  2111594269      265.694875,-24.261
    OGLE-2017-BLG-0482L b         b ...  -287458961  269.048889,-30.5283604
      MOA-2010-BLG-353L b         b ... -1953724135  271.303917,-27.2932333
    OGLE-2014-BLG-1722L c         c ...   361334854   268.75238,-31.4690552


4. The list of confirmed planets where the host star name starts with "Kepler" using a *wildcard search*:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="pscomppars", where="hostname like 'Kepler%'", order="hostname")
    <QTable masked=True length=2369>
       pl_name    pl_letter   hostname  ...    htm20          sky_coord
                                        ...                    deg,deg
        str14        str1      str12    ...    int32            object
    ------------- --------- ----------- ... ----------- ----------------------
      Kepler-10 c         c   Kepler-10 ...   512815427  285.679298,50.2414842
      Kepler-10 b         b   Kepler-10 ...   512815427  285.679298,50.2414842
     Kepler-100 b         b  Kepler-100 ...  -383871624 291.3861294,41.9901394
     Kepler-100 d         d  Kepler-100 ...  -383871624 291.3861294,41.9901394
     Kepler-100 c         c  Kepler-100 ...  -383871624 291.3861294,41.9901394
    Kepler-1000 b         b Kepler-1000 ... -1745355506 286.6854729,47.0981948
              ...       ...         ... ...         ...                    ...
     Kepler-995 b         b  Kepler-995 ...  -369943676  284.6157154,39.130998
     Kepler-996 b         b  Kepler-996 ...  -288530943 291.9127633,41.5335891
     Kepler-997 b         b  Kepler-997 ...   604179197 289.2333767,49.9388952
     Kepler-998 b         b  Kepler-998 ...  1883599570 296.7541629,49.2087085
     Kepler-999 b         b  Kepler-999 ... -1948748132 299.6604865,46.1984679


5. The Kepler Objects of Interest that were vetted more recently than January 24, 2015 using a *date search*:

.. code-block:: python
.. doctest-remote-data::

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
