.. doctest-skip-all

.. _astroquery.cadc:

************************
Cadc (`astroquery.cadc`)
************************

The Canadian Astronomy Data Centre (CADC) is a world-wide distribution centre for
astronomical data obtained from telescopes. The CADC specializes in data mining,
processing, distribution and transferring of very large astronomical datasets.

This package allows the access to the data at the CADC
(http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca)

============
Basic Access
============

NOTE: ```astroquery.cadc``` is dependent on the ```pyvo``` package. Please
install it prior to using the ```cadc``` module.

The CADC hosts a number of collections and ```get_collections``` returns a list
of all these collections:

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> for collection, details in sorted(cadc.get_collections().items()):
  >>>    print('{} : {}'.format(collection, details))

  APASS : {'Description': 'The APASS collection at the CADC', 'Bands': ['Optical', 'Infrared']}
  BLAST : {'Description': 'The BLAST collection at the CADC', 'Bands': ['Millimeter']}
  CFHT : {'Description': 'The CFHT collection at the CADC', 'Bands': ['Optical', 'Infrared']}
  CFHTMEGAPIPE : {'Description': 'The CFHTMEGAPIPE collection at the CADC', 'Bands': ['Infrared', 'Optical']}
  CFHTTERAPIX : {'Description': 'The CFHTTERAPIX collection at the CADC', 'Bands': ['Optical', 'Infrared']}
  CFHTWIRWOLF : {'Description': 'The CFHTWIRWOLF collection at the CADC', 'Bands': ['Infrared']}
  CGPS : {'Description': 'The CGPS collection at the CADC', 'Bands': ['Radio', 'Millimeter', 'Infrared']}
  CHANDRA : {'Description': 'The CHANDRA collection at the CADC', 'Bands': ['X-ray']}
  DAO : {'Description': 'The DAO collection at the CADC', 'Bands': ['Infrared', 'Optical']}
  DAOPLATES : {'Description': 'The DAOPLATES collection at the CADC', 'Bands': ['Optical']}
  FUSE : {'Description': 'The FUSE collection at the CADC', 'Bands': ['UV']}
  GEMINI : {'Description': 'The GEMINI collection at the CADC', 'Bands': ['Infrared', 'Optical']}
  HST : {'Description': 'The HST collection at the CADC', 'Bands': ['Infrared', 'Optical', 'UV']}
  HSTHLA : {'Description': 'The HSTHLA collection at the CADC', 'Bands': ['Optical', 'Infrared', 'UV']}
  IRIS : {'Description': 'The IRIS collection at the CADC', 'Bands': ['Infrared']}
  JCMT : {'Description': 'The JCMT collection at the CADC', 'Bands': ['Millimeter']}
  JCMTLS : {'Description': 'The JCMTLS collection at the CADC', 'Bands': ['Millimeter']}
  MACHO : {'Description': 'The MACHO collection at the CADC', 'Bands': ['Optical']}
  MOST : {'Description': 'The MOST collection at the CADC', 'Bands': ['Optical']}
  NOAO : {'Description': 'The NOAO collection at the CADC', 'Bands': ['Optical', 'Infrared']}
  OMM : {'Description': 'The OMM collection at the CADC', 'Bands': ['Optical', 'Infrared']}
  SDSS : {'Description': 'The SDSS collection at the CADC', 'Bands': ['Infrared', 'Optical']}
  SUBARU : {'Description': 'The SUBARU collection at the CADC', 'Bands': ['Optical']}
  TESS : {'Description': 'The TESS collection at the CADC', 'Bands': ['Optical']}
  UKIRT : {'Description': 'The UKIRT collection at the CADC', 'Bands': ['Optical', 'Infrared']}
  VGPS : {'Description': 'The VGPS collection at the CADC', 'Bands': ['Radio']}
  VLASS : {'Description': 'The VLASS collection at the CADC', 'Bands': ['Radio']}
  XMM : {'Description': 'The XMM collection at the CADC', 'Bands': ['Optical', 'UV', 'X-ray']}


The most basic ways to access the CADC data and metadata is by region or by
name. The following example queries CADC for Canada France Hawaii Telescope
data for a given region and resolves the URLs for downloading the corresponding
data.

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> result = cadc.query_region('08h45m07.5s +54d18m00s', collection='CFHT')
  >>> print(result)
    caomObservationURI sequenceNumber proposal_keywords target_standard ... energy_transition_transition          time_bounds [2]           polarization_states      lastModified_2
                                                                    ...                                              d
    ------------------ -------------- ----------------- --------------- ... ---------------------------- ---------------------------------- ------------------- -----------------------
    caom:CFHT/2376828        2376828                                 0 ...                               58546.328009 .. 58546.32960815509                     2019-03-04T08:14:46.470
    caom:CFHT/2366188        2366188                                 0 ...                              58490.4676995 .. 58490.47001630555                     2019-02-07T12:41:55.814
    caom:CFHT/2366432        2366432                                 0 ...                               58491.407547 .. 58491.40986379398                     2019-02-07T12:24:09.625
    caom:CFHT/2366188        2366188                                 0 ...                              58490.4676995 .. 58490.47001630555                     2019-01-07T11:27:37.922
    caom:CFHT/2366432        2366432                                 0 ...                               58491.407547 .. 58491.40986379398                     2019-01-08T10:03:36.057

  >>> urls = cadc.get_data_urls(result)
  >>> for url in urls:
  >>>     print(url)

    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o.fits.fz?RUNID=xo7r3w23t22gr8zz
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366188p.fits.fz?RUNID=c27nw5wjv4c116wx
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366432p.fits.fz?RUNID=ucfuuhr12uik5y9z
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366188o.fits.fz?RUNID=pbrewkej9zpm65qp
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2366432o.fits.fz?RUNID=bwh3jo0povcdx503


The next example queries all the data in that region and filters the results
on the name of the target (as an example - any other filtering possible) and
resolves the URLs for both the primary and auxiliary data (in this case
preview files)

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> result = cadc.query_region('08h45m07.5s +54d18m00s')
  >>> print(len(result))

        662

  >>> urls = cadc.get_data_urls(result[result['target_name'] == 'Nr3491_1'],
                                include_auxiliaries=True)
  >>> for url in urls:
  >>>    print(url)

    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o_preview_zoom_1024.jpg?RUNID=bxpv43misqekd16f
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o.fits.fz?RUNID=bxpv43misqekd16f
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o_preview_1024.jpg?RUNID=bxpv43misqekd16f
    https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHT/2376828o_preview_256.jpg?RUNID=bxpv43misqekd16f


CADC data can also be queried on the target name. Note that the name is not
resolved. Instead it is matched against the target name in the CADC metadata.

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> result = cadc.query_name('M31')
  >>> print(len(result))

    103949

  >>> result = cadc.query_name('Nr3491_1')
  >>> print(result)

    caomObservationURI sequenceNumber proposal_keywords target_standard ... energy_transition_transition          time_bounds [2]          polarization_states      lastModified_2
                                                                        ...                                              d
    ------------------ -------------- ----------------- --------------- ... ---------------------------- --------------------------------- ------------------- -----------------------
     caom:CFHT/2376828        2376828                                 0 ...                              58546.328009 .. 58546.32960815509                     2019-03-04T08:14:46.470


If only a subsection of the FITS file is needed, CADC can query an area and
resolve the cutout of a result.

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> coords = '01h45m07.5s +23d18m00s'
  >>> radius = '0.01 deg'
  >>> images = cadc.get_images(coords, radius, collection='CFHT')
  >>> for image in images:
  ...    print(image)

    [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x7f3805a06ef0>]
    [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x7f3805b23b38>]


Alternatively, if the query result is large and data does not need to be
in memory, lazy access to the downloaded FITS file can be used.

.. code-block:: python

  >>> from astropy import units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> coords = SkyCoord(10, 20, unit='deg')
  >>> radius = 0.01*u.deg
  >>> readable_objs = cadc.get_images_async(coords, radius, collection='CFHT')
  >>> for obj in readable_objs:
  ...    print(obj)

    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F449264c.fits.gz&RUNID=qs0jrrwbsd45qcxk&POS=CIRCLE+10.00000850225453+20.000001529485854+0.1 with ID 139878698093816
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F289915a.fits.gz&RUNID=qom9bhlqi8g9bx2j&POS=CIRCLE+10.00000850225453+20.000001529485854+0.1 with ID 139878697229280
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F1821295x.fits.fz&RUNID=qom9bhlqi8g9bx2j&POS=CIRCLE+10.00000850225453+20.000001529485854+0.1 with ID 139878696451264
    Downloaded object from URL https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F248912o.fits.gz&RUNID=qom9bhlqi8g9bx2j&POS=CIRCLE+10.00000850225453+20.000001529485854+0.1 with ID 139878590752136


If the cutout urls from a complicated query are needed, the result table
can be passed into the function, along with the cutout coordinates and radius.

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> coords = '01h45m07.5s +23d18m00s'
  >>> radius = 0.1
  >>> results = cadc.query_region(coords, radius, collection='CFHT')
  >>> filtered_results = results[results['time_exposure'] > 120.0]
  >>> image_list = cadc.get_image_list(filtered_results, coords, radius)
  >>> print(image_list)
    ['https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368279o.fits.fz&RUNID=z8zh87jsbp154wbq&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1',
    'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368278o.fits.fz&RUNID=z8zh87jsbp154wbq&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1',
    'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368279p.fits.fz&RUNID=z8zh87jsbp154wbq&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1',
    'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync?ID=ad%3ACFHT%2F2368278p.fits.fz&RUNID=z8zh87jsbp154wbq&POS=CIRCLE+26.2812589776878+23.299999818906816+0.1']


Note that the examples above are for accessing data anonymously. Users with
access to proprietary data can use authenticated sessions to instantiate the
```Cadc``` class or call ```login``` on it before querying or accessing the
data.

CADC metadata is available through a TAP service. While the above interfaces
offer a quick and simple access to the data, the TAP interface presented in
the next sections allows for more complex queries.

=============================
Query CADC metadata using TAP
=============================

Cadc TAP access is based on a TAP+ REST service. TAP+ is an extension of
Table Access Protocol (TAP: http://www.ivoa.net/documents/TAP/) specified by the
International Virtual Observatory Alliance (IVOA: http://www.ivoa.net).

The TAP query language is Astronomical Data Query Language
(ADQL: http://www.ivoa.net/documents/ADQL/2.0), which is similar
to Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes: Synchronous and Asynchronous:

* Synchronous: the response to the request will be generated as soon as the
  request received by the server.
  (In general, avoid using this method for queries that take a long time to
  run before the first rows are returned as it might lead to timeouts on the
  client side.)
* Asynchronous: the server will start a job that will execute the request.
  The first response to the request is the required information (a link)
  to obtain the job status.
  Once the job is finished, the results can be retrieved.

The functions can be run as an authenticated user, the ``list_async_jobs()``
function will error if not authenticated. For authentication you need an account
with the CADC, go to http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/, choose a
language, click on Login in the top right area, click on the Request an Account
link, enter your information and wait for confirmation of your account creation.

There are two type of authentication:

* Username/Password
  Cadc().login(user='yourusername', password='yourpassword')

* Certificate
  Cadc().login(certificate_file='path/to/certificate/file')

For certificate authentication to get a certificate go to
https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/, choose a language, login, click
on your name where the login button used to be, from the drop-down menu click
Obtain a Certificate and save the certificate. When adding authentication used
the path to where you saved the certificate. Remember that certificates expire
and you will need to get a new one.

When logging in, both forms of authentication are allowed. Authentication will
be applied to each subsequent call. When a job is created with authentication
any further calls will require authentication.

There is one way to logout which will cancel any kind of authentication that was used

* Logout
  Cadc.logout()

CADC metadata is modeled using the CAOM (Common Archive Observation Model) -
https://www.opencadc.org/caom2/


======================
Examples of TAP access
======================

---------------------------
1. Non authenticated access
---------------------------

1.1. Get tables
~~~~~~~~~~~~~~~~~

To get list of table objects

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> tables=cadc.get_tables(only_names=True)
  >>> for table in tables:
  >>>   print(table)

  caom2.caom2.Observation
  caom2.caom2.Plane
  caom2.caom2.Artifact
  caom2.caom2.Part
  caom2.caom2.Chunk
  caom2.caom2.ObservationMember
  caom2.caom2.ProvenanceInput
  caom2.caom2.EnumField
  caom2.caom2.ObsCoreEnumField
  caom2.caom2.distinct_proposal_id
  caom2.caom2.distinct_proposal_pi
  caom2.caom2.distinct_proposal_title
  caom2.caom2.HarvestSkipURI
  caom2.caom2.SIAv1
  ivoa.ivoa.ObsCore
  ivoa.ivoa.ObsFile
  ivoa.ivoa.ObsPart
  tap_schema.tap_schema.schemas
  tap_schema.tap_schema.tables
  tap_schema.tap_schema.columns
  tap_schema.tap_schema.keys
  tap_schema.tap_schema.key_columns


1.2. Get table
~~~~~~~~~~~~~~~~

To get a single table object

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>>
  >>> cadc = Cadc()
  >>> table=cadc.get_table(table='caom2.Observation')
  >>> for col in table.columns:
  >>>   print(col.name)

  observationURI
  obsID
  collection
  observationID
  algorithm_name
  type
  intent
  sequenceNumber
  metaRelease
  proposal_id
  proposal_pi
  proposal_project
  proposal_title
  proposal_keywords
  target_name
  target_type
  target_standard
  target_redshift
  target_moving
  target_keywords
  telescope_name
  telescope_geoLocationX
  telescope_geoLocationY
  telescope_geoLocationZ
  telescope_keywords
  requirements_flag
  instrument_name
  instrument_keywords
  environment_seeing
  environment_humidity
  environment_elevation
  environment_tau
  environment_wavelengthTau
  environment_ambientTemp
  environment_photometric
  members
  typeCode
  lastModified
  maxLastModified
  metaChecksum
  accMetaChecksum
  Length = 2000 rows



1.3 Run synchronous query
~~~~~~~~~~~~~~~~~~~~~~~~~~

A synchronous query will not store the results at server side. These queries
must be used when the amount of data to be retrieve is 'small'.

There is a limit of 2000 rows. If you need more than that, you must use asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> results = cadc.exec_sync("SELECT top 100 observationID, intent FROM caom2.Observation")
  >>> print(results)

            observationID             intent
  ------------------------------ -----------
                        m1030610     science
    myc03@930813_093655_ukt_0129     science
  m99bu22@000130_165639_das_0112     science
  m95an03@950515_134612_das_0447     science
    myc03@930813_093836_ukt_0130     science
  m99bu22@000130_170940_cbe_0113     science
  m95an03@950515_135307_cbe_0448     science
    myc03@930813_093951_ukt_0131     science
  m99bu22@000130_171325_cbe_0114     science
  m95an03@950515_135732_das_0449     science
                             ...         ...
  m99bu76@000105_171630_cbe_0237     science
                          100308     science
  m95an05@950323_142753_das_0676     science
    myc05@970308_042319_cbe_0146     science
  m99bu76@000105_171955_cbe_0238     science
                          996691     science
                         1083691 calibration
                         1005480 calibration
                       jbte02020     science
                         1083689 calibration
                         1005486 calibration
  Length = 100 rows

Query saving results in a file:

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> job = cadc.exec_sync("SELECT TOP 10 observationID, obsID FROM caom2.Observation AS Observation",
  >>>                      output_file='test_output_noauth.tsv', output_format='tsv')

1.5 Synchronous query with temporary uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> upload_resource = 'data/votable.xml'

  >>> j = cadc.run_query("SELECT * FROM tap_upload.test_table_upload", 'sync', \
  >>>                    upload_resource=upload_resource, upload_table_name="test_table_upload")
  >>> print(j.get_results())

           uri                    contentChecksum            ...   contentType
                                                             ...
  --------------------- ------------------------------------ ... ----------------
  ad:IRIS/I001B1H0.fits md5:b6ead425ae84289246e4528bbdd7da9a ... application/fits
  ad:IRIS/I001B2H0.fits md5:a6b082ca530bf5db5a691985d0c1a6ca ... application/fits
  ad:IRIS/I001B3H0.fits md5:2ada853a8ae135e16504aeba4e47489e ... application/fits


1.6 Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side. These queries can be accessed at any time.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> job = cadc.create_async("SELECT TOP 100 observationID, instrument_name, target_name FROM caom2.Observation AS Observation")
  >>> job.run().wait()
  >>> job.raise_if_error()
  >>> print(job.fetch_result().to_table())

          observationID          instrument_name           target_name
  ------------------------------ --------------- --------------------------------
  m95au08@950207_091918_ukt_0062           UKT14                             OMC1
    myn03@931121_092519_das_0193             DAS                             G225
     ml83@920201_073519_ukt_0049           UKT14
  m95au08@950207_092056_ukt_0063           UKT14                             OMC1
    myn03@931121_094005_das_0194             DAS                             G225
     ml83@920201_074436_ukt_0050           UKT14
  m95au08@950207_092119_ukt_0064           UKT14                             OMC1
                       o4qpk0exq        STIS/CCD                           LIST-2
                          299729           SISFP FLAT POUR LE FILTRE 6611/10 FILT
                          201314        COUDE_F8                             TEST
                             ...             ...                              ...
     hst_07909_f8_wfpc2_total_wf           WFPC2                             HIGH
  hst_07909_g0_wfpc2_f450w_pc_04           WFPC2                             HIGH
  hst_07909_hp_wfpc2_f300w_pc_02           WFPC2                             HIGH
             GN-2015A-Q-86-5-046          GMOS-N                       J1655+2533
     hst_07909_ia_wfpc2_f606w_pc           WFPC2                              ANY
                         1943508       MegaPrime                               D4
    scuba2_00001_20180212T035813         SCUBA-2
            GS-CAL20150607-2-046          GMOS-S                             Bias
           GN-CAL20040311-20-036            NIRI                         GCALflat
           GS-CAL20150411-11-054          GMOS-S                             Bias
                          168750           HRCAM                          TAU CET
  Length = 100 rows


1.7 Load job
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous jobs can be loaded. You need the jobid in order to load the job.


.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> job = cadc.create_async("SELECT TOP 100 observationID, instrument_name, target_name FROM caom2.Observation AS Observation")
  >>> job.run().wait()
  >>> job.raise_if_error()
  >>> loaded_job = cadc.load_async_job(jobid=job.job_id)
  >>> print(loaded_job.fetch_result().to_table())

          observationID          instrument_name           target_name
  ------------------------------ --------------- --------------------------------
  m95au08@950207_091918_ukt_0062           UKT14                             OMC1
    myn03@931121_092519_das_0193             DAS                             G225
     ml83@920201_073519_ukt_0049           UKT14
  m95au08@950207_092056_ukt_0063           UKT14                             OMC1
    myn03@931121_094005_das_0194             DAS                             G225
     ml83@920201_074436_ukt_0050           UKT14
  m95au08@950207_092119_ukt_0064           UKT14                             OMC1
                       o4qpk0exq        STIS/CCD                           LIST-2
                          299729           SISFP FLAT POUR LE FILTRE 6611/10 FILT
                          201314        COUDE_F8                             TEST
                             ...             ...                              ...
     hst_07909_f8_wfpc2_total_wf           WFPC2                             HIGH
  hst_07909_g0_wfpc2_f450w_pc_04           WFPC2                             HIGH
  hst_07909_hp_wfpc2_f300w_pc_02           WFPC2                             HIGH
             GN-2015A-Q-86-5-046          GMOS-N                       J1655+2533
     hst_07909_ia_wfpc2_f606w_pc           WFPC2                              ANY
                         1943508       MegaPrime                               D4
    scuba2_00001_20180212T035813         SCUBA-2
            GS-CAL20150607-2-046          GMOS-S                             Bias
           GN-CAL20040311-20-036            NIRI                         GCALflat
           GS-CAL20150411-11-054          GMOS-S                             Bias
                          168750           HRCAM                          TAU CET
  Length = 100 rows

---------------------------
2. Authenticated access
---------------------------

Some capabilities (shared tables, persistent jobs, etc.) are only available to
authenticated users.

One authentication option is to instantiate the ``Cadc`` class with a pre-existing,
``pyvo.auth.authsession.AuthSession`` or ``requests.Session`` object that
contains the necessary credentials. Note that the session will be used
for all the service interaction. The former session attempts to pair the
credentials with the auth methods in the service capabilities while the
latter sends the credentials with all requests.

The second option is to use the ``login`` methods must be called.

After a successful authentication, user credentials will be used until
the ``logout`` method is called.

All previous methods (``get_tables``, ``get_table``, ``run_query``) explained for
non authenticated users are applicable for authenticated ones.


2.1 Login/Logout
~~~~~~~~~~~~~~~~~

Login with username and password

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> cadc.login(user='userName', password='userPassword')


Login with certificate

.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> cadc.login(certificate_file='/path/to/cert/file')


To perform a logout


.. code-block:: python

  >>> from astroquery.cadc import Cadc
  >>> cadc = Cadc()
  >>> cadc.logout()

Reference/API
=============

.. automodapi:: astroquery.cadc
    :no-inheritance-diagram:
