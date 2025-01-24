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
  >>> isla.query_tap(query='select * from ivoa.obscore')

  access_estsize   access_format                                     access_url                                   calib_level ...    t_max       t_min    t_resolution t_xel
      int64            object                                          object                                        int32    ...   float64     float64     float64    int64
  -------------- ----------------- ------------------------------------------------------------------------------ ----------- ... ----------- ----------- ------------ -----
           26923 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwMjAwMDE=           2 ... 52594.80985 52593.47308      6.1e-05     1
          488697 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwNDAwMDE=           2 ... 52596.64583 52596.46613      6.1e-05     1
         3459831 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9MDA2MDAwNjAwMDI=           2 ... 52600.54167  52599.4592      6.1e-05     1
             ...               ...                                                                            ...         ... ...         ...         ...          ...   ...
          351253 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDQ=           2 ... 57188.63542 57188.28125      6.1e-05     1
           10195 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg4MDExMzAwMDU=           2 ... 57189.64284 57189.28867      6.1e-05     1
          817730 application/x-tar https://isla.esac.esa.int/tap/data?retrieval_type=SCW&b2JzaWQ9ODg5OTgwMTAzMDE=           2 ... 52636.82597 52636.49534      6.1e-05     1

------------------
2. Getting sources
------------------

Users can utilize this method to retrieve a target from the Archive by specifying a target name.
The output can be formatted and saved as needed.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.get_sources(target_name='crab')

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
  >>> metadata
  [{'name': 'Integral', 'link': None, 'metadata': [{'param': 'Name', 'value': 'Crab'}, {'param': 'Id', 'value': 'J053432.0+220052'}, {'param': 'Coordinates degrees', 'value': '83.6324 22.0174'}, {'param': 'Coordinates', 'value': '05 34 31.78 22 01 02.64'}, {'param': 'Galactic', 'value': '184.55 -5.78'}, {'param': 'Isgri flag2', 'value': 'very bright source'}, {'param': 'Jemx flag', 'value': 'detected'}, {'param': 'Spi flag', 'value': 'detected'}, {'param': 'Picsit flag', 'value': 'detected'}]}, {'name': 'Simbad', 'link': 'https://simbad.cds.unistra.fr/simbad/sim-id?Ident=Crab', 'metadata': [{'param': 'Id', 'value': 'NAME Crab'}, {'param': 'Type', 'value': 'SuperNova Remnant'}, {'param': 'Other types', 'value': 'HII|IR|Psr|Rad|SNR|X|gam'}]}]

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
  >>> isla.get_observations(target_name='crab', radius=12.0, start_revno='0290', end_revno='0599')
     dec                 email              end_revno       endtime       ...      starttime       surname                               title
   float64               str60                object         object       ...        object         str20                                str120
  ---------- ------------------------------ --------- ------------------- ... ------------------- ---------- --------------------------------------------------------------
  26.3157778 peter.kretschmar!@obs.unige.ch      0352 2005-09-02 21:20:59 ... 2005-08-31 11:07:06 Kretschmar Target of Opportunity Observations of an Outburst in A 0535+26
      22.684             isdc-iswt@unige.ch      0300 2005-03-30 22:42:38 ... 2005-03-30 10:34:41       ISWT                                 Crab spring/05 IBIS 10 deg arc
      20.611             isdc-iswt@unige.ch      0300 2005-03-31 13:35:11 ... 2005-03-30 22:44:07       ISWT                                 Crab spring/05 IBIS 10 deg arc
         ...                            ...       ...                 ... ...                 ...        ...                                                            ...
  22.0144444         inthelp@sciops.esa.int      0541 2007-03-21 00:08:52 ... 2007-03-20 21:30:30     Public                       Crab-2007 Spring: JEM-X VC settings test
  22.0144444         inthelp@sciops.esa.int      0541 2007-03-22 03:16:24 ... 2007-03-21 00:10:22     Public                         Crab-2007 Spring: IBIS on-axis staring
  22.0144444         inthelp@sciops.esa.int      0541 2007-03-20 15:35:22 ... 2007-03-19 12:53:21     Public                              Crab-2007 Spring: SPI 5x5 pattern


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
  >>> isla.download_science_windows(science_windows=['008100430010', '033400230030'], output_file=None)


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
  >>> timeline
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
  >>> ltt = isla.get_long_term_timeseries(target_name='J174537.0-290107', instrument='jem-x')

8.2. Retrieving Short-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method allows for the download of short-term time series data for a target and epoch of interest.
Users can refine their search using instrument or energy band filters and
the results are saved to a file for detailed examination.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> stt = isla.get_short_term_timeseries(target_name='J011705.1-732636', band='28_40', epoch='0745_06340000001')

8.3. Retrieving spectra
~~~~~~~~~~~~~~~~~~~~~~~

This method allows users to download spectral data for a target and epoch.
Users can apply filters, such as instrument or energy band, and save the results to an
output file for further processing.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> spectra = isla.get_spectra(target_name='J011705.1-732636', instrument='ibis', epoch='0745_06340000001')


8.4. Retrieving mosaics
~~~~~~~~~~~~~~~~~~~~~~~

Mosaic images corresponding to a specified epoch can be downloaded using this method.
Users can filter by instrument or energy band and save the resulting image to a file for later use.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> mosaics = isla.get_mosaic(epoch='0727_88601650001', instrument='ibis')


Reference/API
=============

.. automodapi:: astroquery.esa.integral
    :no-inheritance-diagram: