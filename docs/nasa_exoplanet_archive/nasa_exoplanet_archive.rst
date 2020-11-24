.. doctest-skip-all

.. _astroquery.nasa_exoplanet_archive:

************************************************************
NASA Exoplanet Archive (`astroquery.nasa_exoplanet_archive`)
************************************************************

This module can be used to query the `NASA Exoplanet Archive <https://exoplanetarchive.ipac.caltech.edu>`_ via
`the API <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_.
A full discussion of the available tables and query syntax is available at [1]_.

Query methods
=============

The `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_object` method can be used to query for a specific planet or planet host.
For example, the following query searches the ``exoplanets`` table of confirmed exoplanets for information about the planet K2-18 b.

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_object("K2-18 b")
    <QTable masked=True length=1>
    pl_hostname pl_letter pl_name ... rowupdate  pl_facility      sky_coord
                                  ...                              deg,deg
        str5       str1     str7  ...   str10        str2           object
    ----------- --------- ------- ... ---------- ----------- -------------------
          K2-18         b K2-18 b ... 2019-03-21          K2 172.560455,7.588391


Similarly, cone searches can be executed using the `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_region` method:

.. code-block:: python

    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord
    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_region(
    ...     table="exoplanets", coordinates=SkyCoord(ra=172.56 * u.deg, dec=7.59 * u.deg),
    ...     radius=1.0 * u.deg)
    <QTable masked=True length=2>
    pl_hostname pl_letter pl_name ...   dist     angle         sky_coord
                                  ...                           deg,deg
        str5       str1     str7  ... float64   float64          object
    ----------- --------- ------- ... -------- ---------- -------------------
          K2-18         b K2-18 b ... 6.016586 164.332463 172.560455,7.588391
          K2-18         c K2-18 c ... 6.016586 164.332463 172.560455,7.588391


The most general queries can be performed using the `~astroquery.nasa_exoplanet_archive.NasaExoplanetArchiveClass.query_criteria` method.
For example, a full table can be queried as follows:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="cumulative", select="*")
    <QTable masked=True length=9564>
     kepid   kepoi_name kepler_name  ... koi_fittype koi_score      sky_coord
                                     ...                             deg,deg
     int64      str9       str15     ...     str7     float64         object
    -------- ---------- ------------ ... ----------- --------- -------------------
    10797460  K00752.01 Kepler-227 b ...     LS+MCMC       1.0 291.93423,48.141651
    10797460  K00752.02 Kepler-227 c ...     LS+MCMC     0.969 291.93423,48.141651
         ...        ...          ... ...         ...       ...                 ...
    10155286  K07988.01           -- ...     LS+MCMC     0.092 296.76288,47.145142
    10156110  K07989.01           -- ...     LS+MCMC       0.0 297.00977,47.121021


Example queries
===============

Specific searches can be executed using the ``where``, ``select``, ``order``, and other parameters as described in the documentation [1]_.

In this section, we demonstrate

1. The number of confirmed planets discovered by TESS:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="exoplanets", select="count(*)",
    ...                                     where="pl_facility like '%TESS%'")
    <QTable length=1>
    count(*)
     int64
    --------
          45


2. The list of confirmed planets discovered by TESS and their coordinates:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(table="exoplanets", select="pl_hostname,ra,dec",
    ...                                     where="pl_facility like '%TESS%'")
    <QTable length=45>
    pl_hostname     ra        dec           sky_coord
                   deg        deg            deg,deg
       str11     float64    float64           object
    ----------- ---------- ---------- ---------------------
       HD 39091  84.291214 -80.469124  84.291214,-80.469124
      HD 219666 349.556792 -56.903786 349.556792,-56.903786
            ...        ...        ...        ...        ...
      HD 221416  353.03363 -21.801424  353.03363,-21.801424
        TOI-150 112.965667 -73.606153 112.965667,-73.606153


3. The list of confirmed planets discovered using microlensing that have data available in the archive:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="exoplanets", where="pl_discmethod like 'Microlensing' and st_nts > 0")
    <QTable masked=True length=32>
         pl_hostname      pl_letter ... pl_facility       sky_coord
                                    ...                    deg,deg
            str21            str1   ...     str4            object
    --------------------- --------- ... ----------- ---------------------
        MOA-2011-BLG-028L         b ...         MOA    270.854,-29.213417
      OGLE-2012-BLG-0724L         b ...        OGLE 268.968292,-29.818528
                      ...       ... ...         ...                   ...
        MOA-2011-BLG-262L         b ...         MOA 270.097833,-31.245258
      OGLE-2015-BLG-0966L         b ...        OGLE  268.75425,-29.047111


4. The list of confirmed planets where the host star name starts with "Kepler" using a *wildcard search*:

.. code-block:: python

    >>> from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    >>> NasaExoplanetArchive.query_criteria(
    ...     table="exoplanets", where="pl_hostname like 'Kepler%'", order="pl_hostname")
    <QTable masked=True length=2312>
    pl_hostname pl_letter    pl_name    ... rowupdate  pl_facility      sky_coord
                                        ...                              deg,deg
       str12       str1       str14     ...   str10       str34           object
    ----------- --------- ------------- ... ---------- ----------- --------------------
      Kepler-10         c   Kepler-10 c ... 2017-07-27      Kepler 285.679394,50.241299
      Kepler-10         b   Kepler-10 b ... 2015-10-15      Kepler 285.679394,50.241299
            ...       ...           ... ...        ...         ...                  ...
     Kepler-998         b  Kepler-998 b ... 2016-05-10      Kepler 296.754151,49.208744
     Kepler-999         b  Kepler-999 b ... 2016-05-10      Kepler 299.660466,46.198418


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

.. [1] `NASA Exoplanet Archive API Documentation <https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html>`_


Reference/API
=============

.. automodapi:: astroquery.nasa_exoplanet_archive
    :no-inheritance-diagram:
