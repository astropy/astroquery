.. _astroquery.esa.integral:

**********************************************************************
ESA Integral Science Legacy Archive (ISLA) (`astroquery.esa.integral`)
**********************************************************************

INTEGRAL is the INTernational Gamma-Ray Astrophysics Laboratory of the
European Space Agency. It observes the Universe in the X-ray and soft
gamma-ray band. Since its launch, on October 17, 2002, the ISDC receives
the spacecraft telemetry within seconds and provides alerts, processed
data and analysis software to the worldwide scientific community.

========
Examples
========

---------------------------
1. ADQL Queries to ISLA TAP
---------------------------

The Query TAP functionality facilitates the execution of custom Table Access Protocol (TAP)
queries within the Integral Science Legacy Archive. Results can be exported to a specified
file in the chosen format, and queries may be executed asynchronously.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.query_tap(query='select * from ivoa.obscore')  # doctest: +IGNORE_OUTPUT
  <Table length=6743>
  access_estsize   access_format                                     access_url                                   calib_level dataproduct_type         em_max        ... t_exptime    t_max       t_min    t_resolution t_xel
      int64            object                                          object                                        int32         object             float64        ...  float64    float64     float64     float64    int64
  -------------- ----------------- ------------------------------------------------------------------------------ ----------- ---------------- --------------------- ... --------- ----------- ----------- ------------ -----
           26923 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwMjAwMDE=           2            image 1.241528257871965e-13 ...  115497.0 52594.80985 52593.47308      6.1e-05     1
          488697 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwNDAwMDE=           2            image 1.241528257871965e-13 ...   15526.0 52596.64583 52596.46613      6.1e-05     1
         3459831 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwNjAwMDI=           2            image 1.241528257871965e-13 ...   93525.0 52600.54167  52599.4592      6.1e-05     1
          829304 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwNjAwMDM=           2            image 1.241528257871965e-13 ...   32400.0 52601.52083 52601.14583      6.1e-05     1
         2690370 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwNjAwMDU=           2            image 1.241528257871965e-13 ...  103739.0 52603.65248 52602.45179      6.1e-05     1
             ...               ...                                                                            ...         ...              ...                   ... ...       ...         ...         ...          ...   ...
          680110 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDE=           2            image 1.241528257871965e-13 ...   29700.0 57181.66231 57181.28125      6.1e-05     1
          802534 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDI=           2            image 1.241528257871965e-13 ...   30600.0 57183.65356 57183.28074      6.1e-05     1
          861813 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDM=           2            image 1.241528257871965e-13 ...   30600.0 57184.66102 57184.28819      6.1e-05     1
          351253 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDQ=           2            image 1.241528257871965e-13 ...   30600.0 57188.63542 57188.28125      6.1e-05     1
           10195 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDU=           2            image 1.241528257871965e-13 ...   30600.0 57189.64284 57189.28867      6.1e-05     1
          817730 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg5OTgwMTAzMDE=           2            image 1.241528257871965e-13 ...   24200.0 52636.82597 52636.49534      6.1e-05     1

------------------
2. Getting sources
------------------

Users can utilize this method to retrieve a target from the Archive by specifying a target name.
The output can be formatted and saved as needed.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.get_sources(target_name='crab')
  <Table length=1>
   name          ra               dec           source_id
  object      float64           float64           object
  ------ ----------------- ----------------- ----------------
    Crab 83.63320922851562 22.01447105407715 J053432.0+220052

-----------------------------------------
3. Getting metadata associated to sources
-----------------------------------------

By invoking this method, users gain access to detailed metadata for a given source,
identified by its target name. The metadata provides in-depth information about the source's archival.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> metadata = isla.get_source_metadata(target_name='Crab')
  >>> metadata  # doctest: +IGNORE_OUTPUT
  [{'name': 'Integral', 'link': None, 'metadata': {'columns': ['description', 'value'], 'rows': [{'description': 'Name', 'value': 'Crab'}, {'description': 'Id', 'value': 'J053432.0+220052'}, {'description': 'Coordinates degrees', 'value': '83.6324 22.0174'}, {'description': 'Coordinates', 'value': '05:34:31.78 22:01:02.64'}, {'description': 'Galactic', 'value': '184.55 -5.78'}, {'description': 'Isgri flag2', 'value': 'very bright source'}, {'description': 'Jemx flag', 'value': 'detected'}, {'description': 'Spi flag', 'value': 'detected'}, {'description': 'Picsit flag', 'value': 'detected'}]}}, {'name': 'Simbad', 'link': 'https://simbad.cds.unistra.fr/simbad/sim-id?Ident=Crab', 'metadata': {'columns': ['description', 'value'], 'rows': [{'description': 'Id', 'value': 'NAME Crab'}, {'description': 'Type', 'value': 'SuperNova Remnant'}, {'description': 'Other types', 'value': 'gam|HII|IR|Psr|Rad|SNR|X'}]}}, {'name': 'Publications', 'link': None, 'metadata': None}]

------------------------------------
4. Retrieving observations from ISLA
------------------------------------

Observation data can be extracted using this method, defining a criteria such as target name,
coordinates, search radius, time range, or revolution number range.
The data can be formatted and saved to a file, with the option to perform the
operation asynchronously.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.get_observations(target_name='crab', radius=12.0, start_revno='0290', end_revno='0599')  # doctest: +IGNORE_OUTPUT
  <Table length=28>
     dec     end_revno       endtime       exposure    obsid    prop_id     ra     ... scw_number  scw_size       srcname       start_revno      starttime       surname                               title
   float64     object         object        int64      object     str7   float64   ...   int64      int64          str20           object          object         str20                                str120
  ---------- --------- ------------------- -------- ----------- ------- ---------- ... ---------- ---------- ------------------ ----------- ------------------- ---------- --------------------------------------------------------------
  26.3157778      0352 2005-09-02 21:20:59   200032 03200490001 0320049  84.727375 ...        110 8865617044          A 0535+26        0352 2005-08-31 11:07:06 Kretschmar Target of Opportunity Observations of an Outburst in A 0535+26
  21.5003972      0301 2005-04-01 15:16:17    55000 03998020003 0399802 90.9793537 ...         47 2220095363                GPS        0301 2005-03-31 21:33:56       ISWT                    Galactic Plane Survey for AO 03, Pattern 02
      22.684      0300 2005-03-30 22:42:38    41400 88600690001 8860069     94.424 ...         45 1714289129 10 deg around Crab        0300 2005-03-30 10:34:41       ISWT                                 Crab spring/05 IBIS 10 deg arc
      20.611      0300 2005-03-31 13:35:11    41400 88600690002 8860069     73.003 ...         45 1881430682 10 deg around Crab        0300 2005-03-30 22:44:07       ISWT                                 Crab spring/05 IBIS 10 deg arc
  17.1577222      0300 2005-03-30 01:19:34    45000 88600710001 8860071 80.5439167 ...         49 1981344397  Crab SPI/IBIS 5x5        0300 2005-03-29 12:01:31       ISWT                                    Crab spring/05 SPI/IBIS 5*5
         ...       ...                 ...      ...         ...     ...        ... ...        ...        ...                ...         ...                 ...        ...                                                            ...
  22.0144722      0483 2006-09-29 16:31:27    45000 88601140004 8860114 83.6332083 ...         48 2048814449  Crab cal IBIS/SPI        0483 2006-09-29 01:41:20     Public                                   Crab calibration autumn 2006
  22.0144444      0541 2007-03-20 18:38:03    10000 88601230001 8860123 83.6329167 ...          3  460762160     Crab cal JEM-X        0541 2007-03-20 15:51:22     Public                       Crab-2007 Spring: JEM-X grey filter test
  22.0144444      0541 2007-03-20 21:29:01     8500 88601240001 8860124 83.6329167 ...          3  392713076     Crab cal JEM-X        0541 2007-03-20 18:39:32     Public                    Crab-2007 Spring: JEM-X anode segments test
  22.0144444      0541 2007-03-21 00:08:52     9500 88601250001 8860125 83.6329167 ...          3  418415105     Crab cal JEM-X        0541 2007-03-20 21:30:30     Public                       Crab-2007 Spring: JEM-X VC settings test
  22.0144444      0541 2007-03-22 03:16:24    96041 88601260001 8860126 83.6329167 ...         26 4305461837      Crab cal IBIS        0541 2007-03-21 00:10:22     Public                         Crab-2007 Spring: IBIS on-axis staring
  22.0144444      0541 2007-03-20 15:35:22    90000 88601270001 8860127 83.6329167 ...         99 4305389452  Crab cal IBIS/SPI        0541 2007-03-19 12:53:21     Public                              Crab-2007 Spring: SPI 5x5 pattern


------------------------------
5. Downloading Science Windows
------------------------------

Science window data can be downloaded using this method by providing only one identifier,
such as science window IDs, observation ID, revolution number, or proposal ID.
An additional parameter, read_fits (default value True) reads automatically the downloaded FITS files.

* If ``read_fits=True``, a list of objects containing filename, path and the FITS file opened is returned.
* If ``read_fits=False``, the file name and path where the file has been downloaded is provided.


.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> results = isla.download_science_windows(science_windows=['008100430010', '033400230030'], output_file=None, read_fits=False)  # doctest: +IGNORE_OUTPUT


---------------------
6. Timeline retrieval
---------------------

This method enables the exploration of the observation timeline for a specific region in the sky.
Users can provide right ascension (RA) and declination (Dec) coordinates and adjust the radius
to refine their search.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> from astropy.coordinates import SkyCoord
  >>> isla = IntegralClass()
  >>> coordinates = SkyCoord(83.63320922851562, 22.01447105407715, unit="deg")
  >>> timeline = isla.get_timeline(coordinates=coordinates)
  >>> timeline  # doctest: +IGNORE_OUTPUT
  {'total_items': 8714, 'fraFC': 0.8510442965343126, 'totEffExpo': 16416293.994214607, 'timeline': <Table length=8714>
       scwExpo            scwRevs                scwTimes                scwOffAxis
       float64            float64                 object                  float64
  ------------------ ------------------ -------------------------- ---------------------
   5147.824025240096  39.07800595179441 2003-02-07 07:01:25.500000 0.0025430719729003476
   4212.920636876789  39.09690979681126 2003-02-07 08:21:21.500000 0.0025430719729003476
   4212.920651101999  39.11392562227784 2003-02-07 09:33:18.500000 0.0025430719729003476
                 ...                ...                        ...                   ...
  1675.7455103834102 2767.3106645083526 2024-04-17 13:39:13.500000     4.729406754053243
  1815.2853971426027   2767.31963717696 2024-04-17 14:13:35.500000     4.203559877974954
    2014.34083657953 2767.3294779577823        2024-04-17 14:51:17     4.731196416616404}

--------------------
7. Retrieving epochs
--------------------

A list of observation epochs can be retrieved using this method, focusing on periods when data for a
specific target, instrument, or energy band is available.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.get_epochs(target_name='J011705.1-732636', band='28_40')
  <Table length=50>
       epoch
       object
  ----------------
  0152_01200360001
  0745_06340000001
  0746_06340000001
               ...
  1618_12200430006
  1618_12200430009
  1618_12200430011

This will perform an ADQL search to the Integral database and will return the output.

----------------
8. Data Download
----------------

For each of the following features, an additional parameter, read_fits, is available.

* If ``read_fits=True``, a list of objects containing filename, path and the FITS file opened is returned.
* If ``read_fits=False``, the file names and paths where the files have been downloaded is provided.

8.1. Retrieving Long-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method provides access to long-term timeseries data for a specified target.
Users can refine their results by selecting an instrument or energy band.


.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> ltt = isla.get_long_term_timeseries(target_name='J174537.0-290107', instrument='jem-x', read_fits=False)  # doctest: +IGNORE_OUTPUT


8.2. Retrieving Short-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method allows for the download of short-term time series data for a target and epoch of interest.
Users can refine their search using instrument or energy band filters and
the results are saved to a file for detailed examination.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> stt = isla.get_short_term_timeseries(target_name='J011705.1-732636', band='28_40', epoch='0745_06340000001', read_fits=False)  # doctest: +IGNORE_OUTPUT


8.3. Retrieving spectra
~~~~~~~~~~~~~~~~~~~~~~~

This method allows users to download spectral data for a target and epoch.
Users can apply filters, such as instrument or energy band, and save the results to an
output file for further processing.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> spectra = isla.get_spectra(target_name='J011705.1-732636', instrument='ibis', epoch='0745_06340000001', read_fits=False)  # doctest: +IGNORE_OUTPUT


8.4. Retrieving mosaics
~~~~~~~~~~~~~~~~~~~~~~~

Mosaic images corresponding to a specified epoch can be downloaded using this method.
Users can filter by instrument or energy band and save the resulting image to a file for later use.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> mosaics = isla.get_mosaic(epoch='0727_88601650001', instrument='ibis', read_fits=False)  # doctest: +IGNORE_OUTPUT +IGNORE_WARNINGS

Reference/API
=============

.. automodapi:: astroquery.esa.integral
    :no-inheritance-diagram:
