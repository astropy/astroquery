.. _astroquery.esa.jwst:

****************************************
ESA JWST Archive (`astroquery.esa.jwst`)
****************************************

The James Webb Space Telescope (JWST) is a collaborative project between NASA,
ESA, and the Canadian Space Agency (CSA). Although radically different in
design, and emphasizing the infrared part of the electromagnetic spectrum,
JWST is widely seen as the successor to the Hubble Space Telescope (HST).
The JWST observatory consist of a deployable 6.6 meter passively cooled
telescope optimized for infrared wavelengths, and is operated in deep
space at the anti-Sun Earth-Sun Lagrangian point (L2). It carries four
scientific instruments: a near-infrared camera (NIRCam), a
near-infrared multi-object spectrograph (NIRSpec) covering the 0.6 - 5 μm
spectral region, a near-infrared slit-less spectrograph (NIRISS), and a
combined mid-infrared camera/spectrograph (MIRI) covering 5 - 28 μm. The JWST
focal plane (see image to the right) contains apertures for the science
instruments and the Fine Guidance Sensor (FGS).

The scientific goals of the JWST mission can be sorted into four broad themes:
The birth of stars and proto-planetary systems Planetary systems and the
origins of life

* The end of the dark ages: first light and re-ionization.
* The assembly of galaxies.
* The birth of stars and proto-planetary systems.
* Planetary systems and the origins of life.

This package provides access to the metadata and datasets provided by the
European Space Agency JWST Archive using a TAP+ REST service. TAP+ is an
extension of Table Access Protocol (TAP: http://www.ivoa.net/documents/TAP/)
specified by the International Virtual Observatory Alliance (IVOA: http://www.ivoa.net).

The TAP query language is Astronomical Data Query Language
(ADQL: http://www.ivoa.net/documents/ADQL/2.0), which is similar
to Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes: Synchronous and Asynchronous:

* Synchronous: the response to the request will be generated as soon as the
  request received by the server.
  (Do not use this method for queries that generate a big amount of results.)
* Asynchronous: the server starts a job that will execute the request.
  The first response to the request is the required information (a link)
  to obtain the job status.
  Once the job is finished, the results can be retrieved.

This module can use these two modes, usinc the 'async_job=False/True' tag in different functions.

ESA JWST TAP+ server provides two access mode: public and authenticated:

* Public: this is the standard TAP access. A user can execute ADQL queries and
  upload tables to be used in a query 'on-the-fly' (these tables will be removed
  once the query is executed). The results are available to any other user and
  they will remain in the server for a limited space of time.

* Authenticated: some functionalities are restricted to authenticated users only.
  The results are saved in a private user space and they will remain in the
  server for ever (they can be removed by the user).

  * ADQL queries and results are saved in a user private area.

  * Cross-match operations: a catalog cross-match operation can be executed.
    Cross-match operations results are saved in a user private area.

  * Persistence of uploaded tables: a user can upload a table in a private space.
    These tables can be used in queries as well as in cross-matches operations.


This python module provides an Astroquery API access.


========
Examples
========

It is highly recommended checking the status of JWST TAP before executing this module. To do this:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.get_status_messages()

This method will retrieve the same warning messages shown in JWST Science Archive with information about
service degradation.

---------------------------
1. Non authenticated access
---------------------------

1.1. Query region
~~~~~~~~~~~~~~~~~

.. doctest-remote-data::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.esa.jwst import Jwst
  >>>
  >>> coord = SkyCoord(ra=53, dec=-27, unit=(u.degree, u.degree), frame='icrs')
  >>> width = u.Quantity(5, u.deg)
  >>> height = u.Quantity(5, u.deg)
  >>> result = Jwst.query_region(coordinate=coord, width=width, height=height)
  >>> result  # doctest: +IGNORE_OUTPUT
           dist                observationid          ...
    ------------------ ------------------------------ ...
    0.5520678701664351 jw02516010001_xx107_00007_miri ...
    0.5520678701664351 jw02516010001_xx104_00004_miri ...
    0.5520678701664351 jw02516010001_xx102_00002_miri ...
    0.5520678701664351 jw02516010001_xx10b_00011_miri ...
    0.5520678701664351 jw02516010001_xx109_00009_miri ...
    0.5520678701664351 jw02516010001_xx105_00005_miri ...
    0.5520678701664351 jw02516010001_xx103_00003_miri ...
    0.5520678701664351 jw02516010001_xx10a_00010_miri ...
    0.5520678701664351 jw02516010001_xx101_00001_miri ...
    0.5520678701664351 jw02516010001_xx106_00006_miri ...
    ...                ...                            ...


1.2. Cone search
~~~~~~~~~~~~~~~~

.. doctest-remote-data::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.esa.jwst import Jwst
  >>>
  >>> coord = SkyCoord(ra=53, dec=-27, unit=(u.degree, u.degree), frame='icrs')
  >>> radius = u.Quantity(5.0, u.deg)
  >>> j = Jwst.cone_search(coordinate=coord, radius=radius, async_job=True)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> result = j.get_results()
  >>> result  # doctest: +IGNORE_OUTPUT
             dist                observationid        ...
    ------------------ ------------------------------ ...
    0.5520678701664351 jw02516010001_xx107_00007_miri ...
    0.5520678701664351 jw02516010001_xx104_00004_miri ...
    0.5520678701664351 jw02516010001_xx102_00002_miri ...
    0.5520678701664351 jw02516010001_xx10b_00011_miri ...
    0.5520678701664351 jw02516010001_xx109_00009_miri ...
    0.5520678701664351 jw02516010001_xx105_00005_miri ...
    0.5520678701664351 jw02516010001_xx103_00003_miri ...
    0.5520678701664351 jw02516010001_xx10a_00010_miri ...
    0.5520678701664351 jw02516010001_xx101_00001_miri ...
    0.5520678701664351 jw02516010001_xx106_00006_miri ...
    ...                ...                            ...


1.3. Query by target name
~~~~~~~~~~~~~~~~~~~~~~~~~

To provide the target coordinates based on its name and execute the query region method.
It uses three different catalogs to resolve the coordinates: SIMBAD, NED and VIZIER. An additional target
resolver is provider, ALL (which is also the default value), using all the aforementioned
catalogues in the defined order to obtain the required coordinates (using the following
element in the list if the target name cannot be resolved).

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> import astropy.units as u
  >>>
  >>> target_name = 'M1'
  >>> target_resolver = 'ALL'
  >>> radius = u.Quantity(5, u.deg)
  >>> result = Jwst.query_target(target_name=target_name, target_resolver=target_resolver, radius=radius)
  >>> result  # doctest: +IGNORE_OUTPUT
            dist                  observationid           ...
    -------------------- -------------------------------- ...
    0.003349189664076155   jw01714001004_xx106_00002_miri ...
    0.003349189664076155   jw01714001003_xx10q_00002_miri ...
    0.003349189664076155   jw01714001006_xx107_00003_miri ...
    0.003349189664076155   jw01714001002_xx105_00001_miri ...
    0.003349189664076155 jw01714005001_xx106_00006_nircam ...
    0.003349189664076155   jw01714001003_xx10w_00004_miri ...
    0.003349189664076155   jw01714001002_xx103_00003_miri ...
    0.003349189664076155   jw01714001004_xx104_00004_miri ...
    0.003349189664076155   jw01714001006_xx10n_00003_miri ...
    0.003349189664076155   jw01714001005_xx10p_00001_miri ...
    ...                    ...                            ...


This method uses the same parameters as query region, but also includes the target name and the catalogue
(target resolver) to retrieve the coordinates.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> import astropy.units as u
  >>>
  >>> target_name = 'LMC'
  >>> target_resolver = 'NED'
  >>> width = u.Quantity(5, u.deg)
  >>> height = u.Quantity(5, u.deg)
  >>> result = Jwst.query_target(target_name=target_name, target_resolver=target_resolver,
  ...                            width=width, height=height, async_job=True)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> result  # doctest: +IGNORE_OUTPUT
            dist                  observationid            ...
    ------------------- ---------------------------------- ...
    0.25984680687093176 jw01043010001_02101_00013_mirimage ...
    0.25984680687093176 jw01043010001_02101_00004_mirimage ...
    0.25984680687093176 jw01043010001_02101_00014_mirimage ...
    0.25984680687093176 jw01043007001_02101_00006_mirimage ...
    0.25984680687093176 jw01043008001_02101_00016_mirimage ...
    0.25984680687093176 jw01043007001_02101_00008_mirimage ...
    0.25984680687093176 jw01043009001_02101_00013_mirimage ...
    0.25984680687093176 jw01043007001_02101_00007_mirimage ...
    0.25984680687093176 jw01043007001_02101_00009_mirimage ...
    0.25984680687093176 jw01043009001_02101_00004_mirimage ...
    ...                 ...                                ...


1.4 Getting data products
~~~~~~~~~~~~~~~~~~~~~~~~~

To query the data products associated with a certain Observation ID

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> product_list = Jwst.get_product_list(observation_id='jw01063107001_02101_00013_nrca3')
  >>> print(product_list['filename'])  # doctest: +IGNORE_OUTPUT
                        filename
    ------------------------------------------------
    jw01063-o107_20220328t013707_image2_144_asn.json
            jw01063107001_02101_00013_nrca3_cal.fits
             jw01063107001_02101_00013_nrca3_cal.jpg
       jw01063107001_02101_00013_nrca3_cal_thumb.jpg
            jw01063107001_02101_00013_nrca3_i2d.fits
    ...


You can filter by product type and calibration level (using a numerical
value or the option 'ALL' -set by default- that will download
all the products associated to this observation_id with the same and lower levels).

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> product_list = Jwst.get_product_list(observation_id='jw01023029001_02101_00004_mirimage', product_type='science')
  >>> print(product_list['filename'])
                         filename
    -------------------------------------------------
    jw01023029001_02101_00004_mirimage_c1006_crf.fits
          jw01023029001_02101_00004_mirimage_cal.fits
          jw01023029001_02101_00004_mirimage_i2d.fits
     jw01023029001_02101_00004_mirimage_o029_crf.fits
         jw01023029001_02101_00004_mirimage_rate.fits
    ...


To download a data product

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> query = """select o.observationid, a.artifactid, a.filename
  ... from jwst.observation o join jwst.artifact a on a.obsid = o.obsid
  ... where o.proposal_id = '01166' and o.intent = 'science'"""
  >>> job = Jwst.launch_job(query, async_job=True)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> results = job.get_results()
  >>> results  # doctest: +IGNORE_OUTPUT
             observationid                       artifactid                                    filename
    ------------------------------- ------------------------------------ ----------------------------------------------------
    jw01166091001_02102_00002_nrca3 6ab73824-6587-4bca-84a8-eb48ac7251be jw01166-o091_20220505t044658_wfs-image2_058_asn.json
    jw01166091001_02102_00002_nrca3 c999249f-c554-4a5f-bd6a-099f1fe48864             jw01166091001_02102_00002_nrca3_cal.fits
    jw01166091001_02102_00002_nrca3 004433de-a4b3-4dc6-9177-0f9d78a97bda              jw01166091001_02102_00002_nrca3_cal.jpg
    jw01166091001_02102_00002_nrca3 5b89920d-532d-43be-b70b-973c4bfdfdcc        jw01166091001_02102_00002_nrca3_cal_thumb.jpg
    jw01166091001_02102_00002_nrca3 5a86e351-3066-4c46-8698-c49aade6ec98            jw01166091001_02102_00002_nrca3_rate.fits
    ...                             ...                                  ...
  >>> output_file = Jwst.get_product(artifact_id='6ab73824-6587-4bca-84a8-eb48ac7251be')  # doctest: +SKIP
  >>> output_file = Jwst.get_product(file_name='jw01166091001_02102_00002_nrca3_cal.fits')  # doctest: +SKIP


To download products by observation identifier, it is possible to use the get_obs_products function, with the same parameters
than get_product_list, it also supports product_type parameter as string or list. product_type as string:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_id = 'jw01122001001_0210r_00001_nrs2'
  >>> results = Jwst.get_obs_products(observation_id=observation_id, cal_level=2, product_type='science')


Here product_type as list:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_id = 'jw01122001001_0210r_00001_nrs2'
  >>> results = Jwst.get_obs_products(observation_id=observation_id, cal_level=2, product_type=['science', 'preview'])

A temporary directory is created with the files and a list of the them is provided.

When more than one product is found, a tar file is retrieved. This method extracts the products.

This method is only intended to download the products with the same calibration level or below. If an upper level is requested:

.. code-block:: python

  ValueError: Requesting upper levels is not allowed

If proprietary data is requested and the user has not logged in:

.. code-block:: python

  403 Error 403:
  Private file(s) requested: MAST token required for authentication.

It is also possible to extract the products associated to an observation with upper calibration levels with get_related_observations.
Using the observation ID as input parameter, this function will retrieve the observations (IDs) that use it to create a composite observation.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_id = 'jw02739-o001_t001_nircam_clear-f444w'
  >>> results = Jwst.get_related_observations(observation_id=observation_id)
  >>> results[0:5]
  ['jw02739001001_02105_00001_nrcalong',
   'jw02739001001_02105_00001_nrcblong',
   'jw02739001001_02105_00002_nrcalong',
   'jw02739001001_02105_00002_nrcblong',
   'jw02739001001_02105_00003_nrcalong']

To query the data products associated with a certain Proposal ID and filtered by product_type.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_list = Jwst.download_files_from_program(proposal_id='6651', product_type='preview')  # doctest: +IGNORE_OUTPUT
  INFO: Query finished. [astroquery.utils.tap.core]
  INFO: Downloading products for Observation ID: jw06651001001_05201_00001_nis [astroquery.esa.jwst.core]
  INFO: Downloading products for Observation ID: jw06651002001_05201_00001_nis [astroquery.esa.jwst.core]
  >>> print(observation_list) # doctest: +IGNORE_OUTPUT
  ['jw06651001001_05201_00001_nis', 'jw06651002001_05201_00001_nis']


1.5 Getting public tables
~~~~~~~~~~~~~~~~~~~~~~~~~

To load only table names (TAP+ capability)

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> tables = Jwst.load_tables(only_names=True)
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  >>> print(*(table.name for table in tables), sep="\n")
    ivoa.obscore
    jwst.archive
    jwst.artifact
    jwst.chunk
    jwst.harvestskipuri
    jwst.main
    jwst.moc
    jwst.observation
    ...


To load table names (TAP compatible)

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> tables = Jwst.load_tables()
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  >>> print(*(table.name for table in tables), sep="\n")
    ivoa.obscore
    jwst.archive
    jwst.artifact
    jwst.chunk
    jwst.harvestskipuri
    jwst.main
    ...

To load only a table (TAP+ capability)

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> table = Jwst.load_table('jwst.main')
  >>> print(table) # doctest: +SKIP
  TAP Table name: jwst.jwst.main
  Description: None
  Num. columns: 109


Once a table is loaded, columns can be inspected

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> table = Jwst.load_table('jwst.main')
  >>> print(*(column.name for column in table.columns), sep="\n") # doctest: +IGNORE_OUTPUT
  "public"
  algorithm_name
  calibrationlevel
  collection
  creatorid
  dataproducttype
  energy_bandpassname
  ...


1.6 Synchronous query
~~~~~~~~~~~~~~~~~~~~~

A synchronous query will not store the results at server side. These queries
must be used when the amount of data to be retrieve is 'small'.

There is a limit of 2000 rows. If you need more than that, you must use
asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>>
  >>> job = Jwst.launch_job("SELECT TOP 100 "
  ...       "instrument_name, proposal_id, calibrationlevel, "
  ...       "dataproducttype "
  ...       "FROM jwst.main ORDER BY instrument_name, observationuri")
  >>>
  >>> print(job)  # doctest: +IGNORE_OUTPUT
  <Table length=100>
        name       dtype
  ---------------- ------
   instrument_name object
       proposal_id object
  calibrationlevel  int32
   dataproducttype object
  Jobid: None
  Phase: COMPLETED
  Owner: None
  Output file: 1661441953031O-result.vot.gz
  Results: None
  >>> result = job.get_results()
  >>> result  # doctest: +IGNORE_OUTPUT
  <Table length=100>
  instrument_name proposal_id calibrationlevel dataproducttype
       object        object        int32            object
  --------------- ----------- ---------------- ---------------
              FGS        1014                3           image
              FGS        1014                3           image
              FGS        1014                3           image
              FGS        1014                3           image
              FGS        1014                3           image
              FGS        1014                2           image
              FGS        1014                1           image
              FGS        1014                1           image
              FGS        1014                2           image
              FGS        1014                2           image
              ...         ...              ...             ...
              FGS        1017                2           image
              FGS        1017                1           image
              FGS        1017                2           image
              FGS        1017                1           image
              FGS        1017                2           image
              FGS        1017                1           image
              FGS        1017                2           image
              FGS        1017                1           image
              FGS        1017                2           image
              FGS        1017                1           image
              FGS        1017                2           image


Query saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> job = Jwst.launch_job("SELECT TOP 100 "
  ...                       "instrument_name, proposal_id, calibrationlevel, "
  ...                       "dataproducttype "
  ...                       "FROM jwst.main ORDER BY instrument_name, observationuri",
  ...                       dump_to_file=True)
  >>>
  >>> print(job)  # doctest: +IGNORE_OUTPUT
  Jobid: None
  Phase: COMPLETED
  Owner: None
  Output file: 1655978085454O-result.vot.gz
  Results: None
  >>> result = job.get_results()
  >>> result  # doctest: +IGNORE_OUTPUT
    <Table length=100>
    instrument_name proposal_id calibrationlevel dataproducttype
         object        object        int32            object
    --------------- ----------- ---------------- ---------------
                FGS       01014                3           image
                FGS       01014                3           image
                FGS       01014                3           image
                FGS       01014                3           image
                FGS       01014                3           image
                FGS       01014                3           image
                FGS       01014                2           image
    ...             ...         ...              ...


1.7 Synchronous query on an 'on-the-fly' uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

.. TODO: a local file need to be added for this example
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> upload_resource = 'mytable.xml.gz'
  >>> j = Jwst.launch_job(query="SELECT * from tap_upload.table_test",
  ...                     upload_resource=upload_resource,
  ...                     upload_table_name="table_test", verbose=True)
  >>> result = j.get_results()
  >>> result.pprint()
  source_id alpha delta
  --------- ----- -----
          a   1.0   2.0
          b   3.0   4.0
          c   5.0   6.0


1.8 Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side. These queries can be accessed at any time. For anonymous users, results are kept for three days.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> job = Jwst.launch_job("select top 100 * from jwst.main", async_job=True)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> print(job)  # doctest: +IGNORE_OUTPUT
  Jobid: 1542383562372I
  Phase: COMPLETED
  Owner: None
  Output file: async_20181116165244.vot
  Results: None
  >>> r = job.get_results()
  >>> r['observationid']  # doctest: +IGNORE_OUTPUT
  <MaskedColumn name='observationid' dtype='object' length=100>
       jw01070001002_04101_00003_nrca1
       jw01070001002_04101_00003_nrca1
     jw01286007001_xx10k_00001_nirspec
        jw01290023001_xx10b_00001_miri
      jw01568006004_xx101_00001_nircam
                                   ...

Query saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> job = Jwst.launch_job("select top 100 * from jwst.main", dump_to_file=True)
  >>> print(job)  # doctest: +IGNORE_OUTPUT
  Jobid: None
  Phase: COMPLETED
  Owner: None
  Output file: 1635853688471D-result.vot.gz
  Results: None
  >>> r = job.get_results()
  >>> r['instrument_name']  # doctest: +IGNORE_OUTPUT
  <MaskedColumn name='instrument_name' dtype='object' length=100>
          NIRCAM
          NIRCAM
      NIRISS/MSA
        MIRI/IFU
    NIRCAM/IMAGE
            MIRI
             ...


1.9 Asynchronous job removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove asynchronous

.. Pseudo code with ``job_id`` list ellipsis, skipping test
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> job = Jwst.remove_jobs(["job_id_1", "job_id_2", ...])


-----------------------
2. Authenticated access
-----------------------

Authenticated users are able to access to TAP+ capabilities (shared tables, persistent jobs, etc.)
In order to authenticate a user, ``login`` method must be called. After a successful
authentication, the user will be authenticated until ``logout`` method is called.

All previous methods (``query_object``, ``cone_search``, ``load_table``, ``load_tables``, ``launch_job``) explained for
non authenticated users are applicable for authenticated ones.

The main differences are:

* Asynchronous results are kept at server side for ever (until the user decides to remove one of them).
* Users can access to shared tables.
* It is also possible to set a token after logging using ``set_token`` function.


2.1. Login/Logout
~~~~~~~~~~~~~~~~~

Using the command line:

.. Skipping authentication requiring examples
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(user='userName', password='userPassword')


It is possible to use a file where the credentials are stored:

*The file must containing user and password in two different lines.*

.. Skipping authentication requiring examples
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(credentials_file='my_credentials_file')

MAST tokens can also be used in command line functions:

.. Skipping authentication requiring examples
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(user='userName', password='userPassword', token='mastToken')

If the user is logged in and a MAST token has not been included or must be changed, it can be
specified using the ``set_token`` function.

.. Skipping authentication requiring examples
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(user='userName', password='userPassword')
  >>> Jwst.set_token(token='mastToken')

To perform a logout:

.. Skipping authentication requiring examples
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.logout()



2.2. Listing shared tables
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> tables = Jwst.load_tables(only_names=True, include_shared_tables=True)
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  >>> print(*(table.name for table in tables), sep="\n")  # doctest: +IGNORE_OUTPUT
  public.dual
  tap_schema.columns
  tap_schema.key_columns
  tap_schema.keys
  tap_schema.schemas
  tap_schema.tables
  jwst.artifact
  jwst.chunk
  jwst.main
  jwst.observation
  jwst.observationmember
  jwst.part
  jwst.plane
  jwst.plane_inputs
  ...
  user_schema_1.table1
  user_schema_2.table1
  ...


Reference/API
=============

.. automodapi:: astroquery.esa.jwst
    :no-inheritance-diagram:
