.. doctest-skip-all

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
  >>> isla.query_tap(query='select * from ivoa.obscore') # doctest: +IGNORE_OUTPUT

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

Users can utilize this method to retrieve a target from
the Archive by specifying a target name. The output can be formatted and saved as
needed.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.get_sources(target_name='crab') # doctest: +IGNORE_OUTPUT

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
  >>> metadata# doctest: +IGNORE_OUTPUT
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
  >>> isla.get_observations(target_name='crab', radius=12.0, start_revno='0290', end_revno='0599') # doctest: +IGNORE_OUTPUT
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
The results can be exported to a file for further investigation or analysis.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.download_science_windows(science_windows=['008100430010', '033400230030'], output_file=None) # doctest: +IGNORE_OUTPUT


----------------------------------
6. Timeline retrieval and plotting
----------------------------------

This method enables the exploration of the observation timeline for a specific region in the sky.
Users can provide right ascension (RA) and declination (Dec) coordinates and adjust the radius
to refine their search. Additionally, plots can be generated to illustrate details such as
revolution numbers or distances from the observation center.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> timeline = isla.get_timeline(ra=83.63320922851562, dec=22.01447105407715, plot=True, plot_revno=True, plot_distance=True)
  >>> timeline # doctest: +IGNORE_OUTPUT
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
  >>> isla.get_epochs(target_name='J011705.1-732636', band='28_40') # doctest: +IGNORE_OUTPUT
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
8. ISLA Explorer
----------------

.. note::
    The plots and data provided by the methods in this section have been developed using
    the automatic reduction pipeline at ISDC, using INTEGRAL OSA version 11.2. No manual
    scientific validation has been performed on these outputs. They should be examined
    and validated before being used for scientific purposes. To ensure accuracy and
    reliability, please use the methods available in section 9 to download the original
    source files directly.

8.1. Retrieving Long-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method provides access to long-term timeseries data for a specified target.
Users can refine their results by selecting an instrument or energy band and may
generate a plot automatically to visualize them.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> lt_timeseries_list = isla.get_long_term_timeseries(target_name='J174537.0-290107', instrument='jem-x', plot=True)
  >>> lt_timeseries_list# doctest: +IGNORE_OUTPUT
  {'source_id': 'J174537.0-290107', 'aggregation_value': -1, 'total_items': 863, 'aggregation_unit': 'raw', 'detectors': ['JEMX1', 'JEMX2'], 'timeseries_list': [<Table length=863>
          time              rates            ratesError
         object            float64            float64
  ------------------- ------------------ ------------------
  2007-03-02 01:01:31 10.909699440002441  2.010499954223633
  2007-03-02 01:34:55 6.0742998123168945  0.805400013923645
  2007-03-02 01:51:47  3.182499885559082 0.7900999784469604
                  ...                ...                ...
  2016-03-08 08:55:04 14.921699523925781  2.262700080871582
  2016-03-08 09:28:07 15.576800346374512 2.0703999996185303
  2016-03-08 10:01:52 28.054500579833984  4.750199794769287, <Table length=4>
          time              rates             ratesError
         object            float64             float64
  ------------------- ------------------ -------------------
  2013-08-25 07:55:18  7.502500057220459   0.446399986743927
  2013-10-15 03:54:50  4.342899799346924  0.3774000108242035
  2015-09-19 22:55:18 5.5295000076293945 0.38519999384880066
  2015-09-22 10:04:41 11.792900085449219  0.7631999850273132]}

8.2. Retrieving Short-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Short-term time series data for a specific target and epoch can be accessed through this method.
Users may apply optional filters, such as instrument or energy band,
and can create a plot to visualize the extracted data.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> st_timeseries_list = isla.get_short_term_timeseries(target_name='J011705.1-732636', band='28_40', epoch='0745_06340000001', plot=True)
  >>> st_timeseries_list# doctest: +IGNORE_OUTPUT
  {'source_id': 'J011705.1-732636', 'total_items': 82, 'detectors': ['ISGRI'], 'timeseries_list': [<Table length=82>
          time               rates           rates_error
         object             float64            float64
  ------------------- ------------------- ------------------
  2008-11-18 19:03:12 0.02567444182932377 0.7811741828918457
  2008-11-18 19:19:52  0.7495294809341431 0.7880769371986389
  2008-11-18 19:36:32  0.7943239808082581 0.7840375304222107
                  ...                 ...                ...
  2008-11-19 15:22:38  1.8685616254806519 0.7967823147773743
  2008-11-19 15:39:18  3.6194331645965576 0.7971285581588745
  2008-11-19 15:52:14   4.299497127532959   1.06647527217865]}

8.3. Retrieving spectra
~~~~~~~~~~~~~~~~~~~~~~~

Spectral data for a specified target and epoch can be obtained using this method.
Additional parameters enable users to filter results by instrument or energy band,
with the option to generate plots for spectral visualization.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> spectras = isla.get_spectra(target_name='J011705.1-732636', instrument='ibis', epoch='0745_06340000001', plot=True)
  >>> spectras # doctest: +IGNORE_OUTPUT
  [{'spectra_oid': 46778, 'file_name': 'SMC_X-1_ISGRI_0745_06340000001_spectrum.fits', 'metadata': {}, 'date_start': '1858-11-17 00:00:00', 'date_stop': '1858-11-17 00:00:00', 'detector': 'ISGRI', 'spectra': <Table length=30>
   energy energy_error          rate               rate_error
  float64   float64           float64               float64
  ------- ------------ --------------------- ---------------------
     18.5          0.5    1.3224695920944214   0.18369388580322266
     20.0          1.0    0.8658972978591919   0.05929631367325783
     21.5          0.5    0.7667226791381836  0.057101089507341385
      ...          ...                   ...                   ...
   125.75         3.75  0.004203930962830782  0.004149571992456913
    134.5          5.0 0.0014642734313383698 0.0035532701294869184
   143.25         3.75  0.004885881207883358  0.004115489777177572}]


8.4. Retrieving mosaics
~~~~~~~~~~~~~~~~~~~~~~~

A mosaic image for a specific epoch can be retrieved with this method.
The query can be tailored by selecting an instrument or energy band.
Plots of the mosaic image can also be generated if visualization is required.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> mosaics = isla.get_mosaic(epoch='0727_88601650001', instrument='ibis', plot=True)
  >>> mosaics# doctest: +IGNORE_OUTPUT
  [{'file_name': 'ISGRI_0727_88601650001_28_40_mosaic_smooth.fits.gz', 'mosaic_oid': 2126, 'height': 587, 'width': 589, 'min_z_scale': -2.5965349674224854, 'max_z_scale': 2.6038904190063477, 'mosaic': <Table length=345743>
        ra            dec         data
     float64        float64     float64
  -------------- -------------- -------
   22.6550755124 -36.5822127976     nan
   22.7390065307 -36.6532690339     nan
   22.8233738975 -36.7245035258     nan
             ...            ...     ...
   184.770923897  44.6632117374     nan
  184.7323895179  44.5688775166     nan
  184.6941077098   44.474844758     nan}]

----------------------------
9. Downloading ISLA products
----------------------------

9.1. Downloading Long-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Long-term time series data can be downloaded using this method. Filters for instrument
and energy band can be applied to narrow down the data, and the results are saved to a
designated output file for further analysis.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.download_long_term_timeseries(target_name='J174537.0-290107', instrument='jem-x') # doctest: +IGNORE_OUTPUT

9.2. Downloading Short-Term Timeseries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method allows for the download of short-term time series data for a target and epoch of interest.
Users can refine their search using instrument or energy band filters and
the results are saved to a file for detailed examination.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.download_short_term_timeseries(target_name='J011705.1-732636', band='28_40', epoch='0745_06340000001') # doctest: +IGNORE_OUTPUT

9.3. Downloading spectra
~~~~~~~~~~~~~~~~~~~~~~~~

This method allows users to download spectral data for a target and epoch.
Users can apply filters, such as instrument or energy band, and save the results to an
output file for further processing.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> isla.download_spectra(target_name='J011705.1-732636', instrument='ibis', epoch='0745_06340000001') # doctest: +IGNORE_OUTPUT

9.4. Downloading mosaics
~~~~~~~~~~~~~~~~~~~~~~~~

Mosaic images corresponding to a specified epoch can be downloaded using this method.
Users can filter by instrument or energy band and save the resulting image to a file for later use.

.. doctest-remote-data::

  >>> from astroquery.esa.integral import IntegralClass
  >>> isla = IntegralClass()
  >>> mosaics = isla.download_mosaic(epoch='0727_88601650001', instrument='ibis') # doctest: +IGNORE_OUTPUT


Reference/API
=============

.. automodapi:: astroquery.esa.integral
    :no-inheritance-diagram:
