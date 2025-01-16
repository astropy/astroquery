.. _astroquery.esa.hubble:

*****************************************
ESA HST Archive (`astroquery.esa.hubble`)
*****************************************

The Hubble Space Telescope (HST) is a joint ESA/NASA orbiting astronomical
observatory operating from the near-infrared into the ultraviolet.  Launched
in 1990 and scheduled to operate at least through 2020, HST carries and has
carried a wide variety of instruments producing imaging, spectrographic,
astrometric, and photometric data through both pointed and parallel
observing programs. During its lifetime HST has become one of the most
important science projects ever, with over 500 000 observations of more than
30000 targets available for retrieval from the Archive.

This package allows the access to the `European Space Agency Hubble Archive
<https://hst.esac.esa.int/ehst/>`__. All the HST observations available
in the EHST are synchronised with the MAST services for HST reprocessed
public data and corresponding metadata.  Therefore, excluding proprietary
data, all HST data in the EHST are identical to those in MAST.

It is highly recommended checking the status of eHST TAP before executing this module. To do this:

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.get_status_messages()

This method will retrieve the same warning messages shown in eHST Science Archive with information about
service degradation.

========
Examples
========

.. note::
    The recommended steps to work with eHST Astroquery module are described below:
        #. Retrieve the desired observations, fulfilling the user requirements, using one of the following methods: ``query_target``, ``query_criteria``, ``cone_search`` or ``cone_search_criteria``. In the results, the user will allways find a column named 'observation_id' that will be used as a reference.
        #. If all the products associated to an observation are required, then use ``download_product``.
        #. If only FITS files associated to an observation are required, then use ``download_fits_files``.
        #. It is possible to retrieve the name of the files associated to an observation using ``get_associated_files``, together with their calibration level, size and type.
        #. Users can filter the previous list to get the specific files to download and use them in ``download_file`` function.
        #. Use your algorithms and code to process the data.

----------------------------------------------
1. Querying target names in the Hubble archive
----------------------------------------------

The query_target function queries the name of the target as given by the proposer of the observations.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> table = esahubble.query_target(name="m31", filename="m31_query.xml.gz")  # doctest: +IGNORE_OUTPUT

This will retrieve a table with the output of the query.
It will also download a file storing all metadata for all observations
associated with target name 'm31'. The result of the query will be stored in
file 'm31_query.xml.gz'.

-------------------------------------------------------------------
2. Retrieving observations by search criteria in the Hubble archive
-------------------------------------------------------------------

The query_criteria function uses a set of established parameters to create
and execute an ADQL query, accessing the HST archive database usgin the Table
Access Protocol (TAP).

- **calibration_level** (*str or int, optional*): The identifier of the data reduction/processing applied to the data.

 + RAW (1)
 + CALIBRATED (2)
 + PRODUCT (3)
 + AUXILIARY (0)

- **data_product_type** (*str, optional*): High level description of the product.

 + image
 + spectrum
 + timeseries

- **intent** (*str, optional*): The intent of the original obsever in acquiring this observation.

 + SCIENCE
 + CALIBRATION

- **collection** (*list of strings, optional*): List of collections that are available in eHST catalogue.

 + HLA
 + HST
 + HAP

 Do not forget that this is a list of elements, so it must be defined as ['HST'], ['HST', 'HLA']...

- **instrument_name** (*list of strings, optional*): Name(s) of the instrument(s) used to generate the dataset. This is also a list of elements.
- **filters** (*list of strings, optional*): Name(s) of the filter(s) used to generate the dataset. This is also a list of elements.
- **proposal** (*int, optional*): Proposal or Program ID to be searched.
- **async_job** (*bool, optional, default 'True'*): executes the query (job) in asynchronous/synchronous mode (default synchronous)
- **output_file** (*str, optional, default None*) file name where the results are saved if dumpToFile is True. If this parameter is not provided, the jobid is used instead
- **output_format** (*str, optional, default 'votable'*) results format
- **verbose** (*bool, optional, default 'False'*): flag to display information about the process
- **get_query** (*bool, optional, default 'False'*): flag to return the query associated to the criteria as the result of this function.

This is an example of a query with all the parameters and the verbose flag activated, so the query is shown as a log message.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_criteria(calibration_level = 3,
  ...                                   data_product_type = 'image',
  ...                                   intent='SCIENCE',
  ...                                   obs_collection=['HLA'],
  ...                                   instrument_name = ['WFC3'],
  ...                                   filters = ['F555W', 'F606W'],
  ...                                   async_job = False,
  ...                                   output_file = 'output1.vot.gz',
  ...                                   output_format="votable",
  ...                                   verbose = True,
  ...                                   get_query = False)    # doctest: +IGNORE_OUTPUT
  INFO: select o.*, p.calibration_level, p.data_product_type, pos.ra, pos.dec from ehst.observation AS o JOIN ehst.plane as p on o.observation_uuid=p.observation_uuid JOIN ehst.position as pos on p.plane_id = pos.plane_id where(p.calibration_level LIKE '%PRODUCT%' AND p.data_product_type LIKE '%image%' AND o.intent LIKE '%SCIENCE%' AND (o.collection LIKE '%HLA%') AND (o.instrument_name LIKE '%WFC3%') AND (o.filter LIKE '%F555W%' OR o.filter LIKE '%F606W%')) [astroquery.esa.hubble.core]
  Launched query: 'select  TOP 2000 o.*, p.calibration_level, p.data_product_type, pos.ra, pos.dec from ehst.observation AS o JOIN ehst.plane as p on o.observation_uuid=p.observation_uuid JOIN ehst.position as pos on p.plane_id = pos.plane_id where(p.calibration_level LIKE '%PRODUCT%' AND p.data_product_type LIKE '%image%' AND o.intent LIKE '%SCIENCE%' AND (o.collection LIKE '%HLA%') AND (o.instrument_name LIKE '%WFC3%') AND (o.filter LIKE '%F555W%' OR o.filter LIKE '%F606W%'))'
  ------>http
  host = hst.esac.esa.int:80
  context = /tap-server/tap//sync
  Content-type = application/x-www-form-urlencoded
  200 200
  [('Date', 'Mon, 25 Jul 2022 15:46:58 GMT'), ('Server', 'Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips PHP/5.4.16 mod_jk/1.2.48'), ('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate'), ('Pragma', 'no-cache'), ('Expires', '0'), ('X-XSS-Protection', '1; mode=block'), ('X-Frame-Options', 'SAMEORIGIN'), ('X-Content-Type-Options', 'nosniff'), ('Content-Encoding', 'gzip'), ('Content-Disposition', 'attachment;filename="1658764018965O-result.vot"'), ('Content-Type', 'application/x-votable+xml'), ('Set-Cookie', 'JSESSIONID=B3AD5976E059A042D39AAA35C9C814FC; Path=/; HttpOnly'), ('Connection', 'close'), ('Transfer-Encoding', 'chunked')]
  Retrieving sync. results...
  Saving results to: output1.vot.gz
  Query finished.
  >>> print(result)    # doctest: +IGNORE_OUTPUT
   algorithm_name  collection ...         ra                 dec
       object        object   ...      float64             float64
  ---------------- ---------- ... ------------------ -------------------
  HLA ASSOCIATIONS        HLA ... 196.03170537675234 -49.368511417967795
          exposure        HLA ... 196.03171011284857  -49.36851677699096
          exposure        HLA ...  259.2792180139594   43.13314581814599
          exposure        HLA ...  259.2792180139594   43.13314581814599
          exposure        HLA ...  259.2792180139594   43.13314581814599
          exposure        HLA ...  259.2792180139594   43.13314581814599
  HLA ASSOCIATIONS        HLA ...  259.2792176982667  43.133150839338235
  HLA ASSOCIATIONS        HLA ...  68.97704902707727 -12.677248264318337
  HLA ASSOCIATIONS        HLA ...  68.97704902707727 -12.677248264318337
          exposure        HLA ...  68.97705442773626 -12.677252912230811
               ...        ... ...                ...                 ...
  HLA ASSOCIATIONS        HLA ... 210.80500687669544  54.278497365211976
          exposure        HLA ...  152.7572845488674   -4.80118571219738
          exposure        HLA ...  152.7572845488674   -4.80118571219738
  HLA ASSOCIATIONS        HLA ...  152.7572806802392  -4.801183163442886
          exposure        HLA ...  152.7572845488674   -4.80118571219738
  HLA ASSOCIATIONS        HLA ... 202.44374997285675 -23.750512499483055
          exposure        HLA ... 202.44375533561396 -23.750513053780008
  HLA ASSOCIATIONS        HLA ... 202.44374997285675 -23.750512499483055
          exposure        HLA ... 202.44375533561396 -23.750513053780008
          exposure        HLA ...  152.8105559087745   -4.65644496753373
          exposure        HLA ...  152.8105559087745   -4.65644496753373
  Length = 2000 rows

This will make a synchronous search, limited to 2000 results to find the observations that match these specific
requirements. It will also download a votable file called **output.vot.gz** containing the result of the
query.

The following example uses the string definition of the calibration level ('PRODUCT') and executes an asynchronous job to get all the results that match the criteria.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_criteria(calibration_level = 'PRODUCT',
  ...                                   data_product_type = 'image',
  ...                                   intent='SCIENCE',
  ...                                   obs_collection=['HLA'],
  ...                                   instrument_name = ['WFC3'],
  ...                                   filters = ['F555W', 'F606W'],
  ...                                   async_job = True,
  ...                                   output_file = 'output2.vot.gz',
  ...                                   output_format="votable",
  ...                                   verbose = False,
  ...                                   get_query = False)
  >>> print(result)  # doctest: +IGNORE_OUTPUT
   algorithm_name  collection ...         ra                 dec
  ---------------- ---------- ... ------------------ -------------------
  HLA ASSOCIATIONS        HLA ... 196.03170537675234 -49.368511417967795
          exposure        HLA ... 196.03171011284857  -49.36851677699096
          exposure        HLA ...  259.2792180139594   43.13314581814599
          exposure        HLA ...  259.2792180139594   43.13314581814599
          exposure        HLA ...  259.2792180139594   43.13314581814599
          exposure        HLA ...  259.2792180139594   43.13314581814599
  HLA ASSOCIATIONS        HLA ...  259.2792176982667  43.133150839338235
  HLA ASSOCIATIONS        HLA ...  68.97704902707727 -12.677248264318337
  HLA ASSOCIATIONS        HLA ...  68.97704902707727 -12.677248264318337
          exposure        HLA ...  68.97705442773626 -12.677252912230811
          exposure        HLA ...  68.97705442773626 -12.677252912230811
               ...        ... ...                ...                 ...
          exposure        HLA ...  345.6583071276117   56.72394842149916
          exposure        HLA ... 345.65831033427037  56.723950318257195
          exposure        HLA ...    345.65826624404   56.72397181023684
          exposure        HLA ...  345.6582969971932   56.72398324705819
          exposure        HLA ... 345.65825980977695   56.72394255099519
          exposure        HLA ...  345.6582694604474    56.7239515193261
          exposure        HLA ...  345.6582302371085   56.72396314167643
          exposure        HLA ... 345.65834620470923   56.72399729379321
  HLA ASSOCIATIONS        HLA ...  345.6583089525364  56.723967490767976
          exposure        HLA ... 295.67142911697397  -10.32552919162329
          exposure        HLA ... 140.37867144039893   45.11729184881005
  Length = 12965 rows


As has been mentioned, these parameters are optional and it is not necessary to define all of them to execute this function, as the search will be adapted to the ones that are available.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result1 = esahubble.query_criteria(calibration_level = 'PRODUCT',
  ...                                    async_job = False,
  ...                                    output_file = 'output3.vot.gz')
  >>> result2 = esahubble.query_criteria(data_product_type = 'image',
  ...                                    intent='SCIENCE',
  ...                                    async_job = False,
  ...                                    output_file = 'output4.vot.gz')
  >>> result3 = esahubble.query_criteria(data_product_type = 'timeseries',
  ...                                    async_job = False,
  ...                                    output_file = 'output5.vot.gz')

If no criteria are specified to limit the selection, this function will retrieve all the observations.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_criteria(async_job = False, verbose = True)    # doctest: +IGNORE_OUTPUT
  INFO: select o.*, p.calibration_level, p.data_product_type, pos.ra, pos.dec from ehst.observation AS o JOIN ehst.plane as p on o.observation_uuid=p.observation_uuid JOIN ehst.position as pos on p.plane_id = pos.plane_id [astroquery.esa.hubble.core]
  Launched query: 'select  TOP 2000 o.*, p.calibration_level, p.data_product_type, pos.ra, pos.dec from ehst.observation AS o JOIN ehst.plane as p on o.observation_uuid=p.observation_uuid JOIN ehst.position as pos on p.plane_id = pos.plane_id'
  ------>http
  host = hst.esac.esa.int:80
  context = /tap-server/tap//sync
  Content-type = application/x-www-form-urlencoded
  200 200
  [('Date', 'Mon, 25 Jul 2022 16:21:18 GMT'), ('Server', 'Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips PHP/5.4.16 mod_jk/1.2.48'), ('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate'), ('Pragma', 'no-cache'), ('Expires', '0'), ('X-XSS-Protection', '1; mode=block'), ('X-Frame-Options', 'SAMEORIGIN'), ('X-Content-Type-Options', 'nosniff'), ('Content-Encoding', 'gzip'), ('Content-Disposition', 'attachment;filename="1658766078997O-result.vot"'), ('Content-Type', 'application/x-votable+xml'), ('Set-Cookie', 'JSESSIONID=7098EC515E7A2240E6F3129D23564139; Path=/; HttpOnly'), ('Connection', 'close'), ('Transfer-Encoding', 'chunked')]
  Retrieving sync. results...
  Query finished.

This last example will provide the ADQL query based on the criteria defined by the user.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_criteria(calibration_level = 'PRODUCT',
  ...                                   data_product_type = 'image',
  ...                                   intent='SCIENCE',
  ...                                   obs_collection=['HLA'],
  ...                                   instrument_name = ['WFC3'],
  ...                                   filters = ['F555W', 'F606W'],
  ...                                   get_query = True)
  >>> print(result)
  select * from ehst.archive where(calibration_level=3 AND data_product_type LIKE '%image%' AND intent LIKE '%science%' AND (collection LIKE '%HLA%') AND (instrument_name LIKE '%WFC3%') AND (filter LIKE '%F555W%' OR filter LIKE '%F606W%'))

--------------------------------------
3. Cone searches in the Hubble archive
--------------------------------------

.. doctest-remote-data::

  >>> from astropy import coordinates
  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
  >>> table = esahubble.cone_search(coordinates=c, radius=7, filename="cone_search_m31_5.vot.gz")

This will perform a cone search with radius 7 arcmins. The result of the
query will be returned and stored in the votable file
'cone_search_m31_5.vot.gz'. If no filename is defined and the "save" tag is True,
the module will provide a default name. It is also possible to store only the results
in memory, without defining neither a filename nor the "save" tag.

----------------------------------------------------
4. Cone searches with criteria in the Hubble archive
----------------------------------------------------

It is also possible to perform a cone search defined by a target name or coordinates, a radius
and a set of criteria to filter the results.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.cone_search_criteria(target= 'm31',radius=7,
  ...                                         obs_collection=['HST'],
  ...                                         data_product_type = 'image',
  ...                                         instrument_name = ['ACS/WFC'],
  ...                                         filters = ['F435W'],
  ...                                         async_job = True,
  ...                                         filename = 'output1.vot.gz',
  ...                                         output_format="votable")
  >>> print(result)    # doctest: +IGNORE_OUTPUT
  algorithm_name collection            end_time           ...         ra                dec
  -------------- ---------- ----------------------------- ... ------------------ ------------------
    multidrizzle        HST 2002-06-29 15:25:57.556128+00 ... 10.773035733571806  41.28459914735614
         drizzle        HST    2002-06-29 12:15:20.787+00 ... 10.809522856742248  41.29351658280752
         drizzle        HST    2002-06-29 12:15:20.787+00 ... 10.809522856742248  41.29351658280752
         drizzle        HST    2002-06-29 12:15:20.787+00 ... 10.809522856742248  41.29351658280752
         drizzle        HST    2002-06-29 15:25:57.557+00 ... 10.809522856742248  41.29351658280752
         drizzle        HST    2002-06-29 15:25:57.557+00 ... 10.809522856742248  41.29351658280752
         drizzle        HST    2002-06-29 15:25:57.557+00 ... 10.809522856742248  41.29351658280752
        exposure        HST    2002-06-29 10:40:25.757+00 ... 10.809522856742248  41.29351658280752
        exposure        HST    2002-06-29 10:40:25.757+00 ... 10.809522856742248  41.29351658280752
        exposure        HST    2002-06-29 10:49:21.757+00 ... 10.809522856742248  41.29351658280752
        exposure        HST    2002-06-29 10:49:21.757+00 ... 10.809522856742248  41.29351658280752
             ...        ...                           ... ...                ...                ...
        exposure        HST     2013-06-19 01:44:51.32+00 ... 10.766005545644669 41.309233725982274
         drizzle        HST      2014-06-26 02:01:04.4+00 ...  10.56783424321201  41.26161655867049
         drizzle        HST      2014-06-26 02:01:04.4+00 ...  10.56783424321201  41.26161655867049
        exposure        HST    2014-06-26 00:04:17.347+00 ...  10.56783424321201  41.26161655867049
        exposure        HST    2014-06-26 00:04:17.347+00 ...  10.56783424321201  41.26161655867049
        exposure        HST 2014-06-26 00:26:04.320001+00 ...  10.56784158160213  41.26168995624255
        exposure        HST 2014-06-26 00:26:04.320001+00 ...  10.56784158160213  41.26168995624255
        exposure        HST    2014-06-26 01:37:39.337+00 ... 10.567904084182938  41.26166780758625
        exposure        HST    2014-06-26 01:37:39.337+00 ... 10.567904084182938  41.26166780758625
        exposure        HST    2014-06-26 02:01:03.337+00 ... 10.567896755477244  41.26159439998882
        exposure        HST    2014-06-26 02:01:03.337+00 ... 10.567896755477244  41.26159439998882
  Length = 323 rows


.. doctest-remote-data::

  >>> from astropy import coordinates
  >>> from astropy import units as u
  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> coords = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
  >>> result = esahubble.cone_search_criteria(coordinates=coords,
  ...                                         radius=7*u.arcmin,
  ...                                         obs_collection=['HST'],
  ...                                         instrument_name = ['WFPC2'],
  ...                                         filters = ['F606W'],
  ...                                         async_job = True,
  ...                                         filename = 'output1.vot.gz',
  ...                                         output_format="votable")
  >>> print(result)   # doctest: +IGNORE_OUTPUT
  algorithm_name collection          end_time          ...         ra                dec
  -------------- ---------- -------------------------- ... ------------------ ------------------
        exposure        HST 1996-07-11 19:57:16.567+00 ... 10.707934959432448  41.29717554921647
        exposure        HST 1996-07-11 19:57:16.567+00 ... 10.707934959432448  41.29717554921647
        exposure        HST 1996-07-11 23:10:56.567+00 ... 10.707934959432448  41.29717554921647
        exposure        HST 1996-07-11 23:10:56.567+00 ... 10.707934959432448  41.29717554921647
        exposure        HST 1995-08-07 17:18:17.427+00 ... 10.667025486961762  41.27549451122148
        exposure        HST 1995-08-07 17:18:17.427+00 ... 10.667025486961762  41.27549451122148
        exposure        HST  1998-08-13 15:41:53.99+00 ...  10.62792588770676  41.16842053688991
        exposure        HST  1998-08-13 15:41:53.99+00 ...  10.62792588770676  41.16842053688991
        exposure        HST  1998-08-13 15:53:53.99+00 ... 10.627778569005512 41.168427385527195
        exposure        HST  1998-08-13 15:53:53.99+00 ... 10.627778569005512 41.168427385527195
        exposure        HST 1999-06-06 17:52:53.323+00 ... 10.726290793310492  41.17571391732456
        exposure        HST 1999-06-06 17:52:53.323+00 ... 10.726290793310492  41.17571391732456
        exposure        HST  1999-06-06 19:19:33.45+00 ... 10.726290793310492  41.17571391732456
        exposure        HST  1999-06-06 19:19:33.45+00 ... 10.726290793310492  41.17571391732456
        exposure        HST  1998-08-13 17:18:53.99+00 ... 10.627778569005512 41.168427385527195
        exposure        HST  1998-08-13 17:18:53.99+00 ... 10.627778569005512 41.168427385527195
        exposure        HST  2002-06-29 10:28:56.79+00 ... 10.673753121140141  41.33685901875662
        exposure        HST  2002-06-29 10:28:56.79+00 ... 10.673753121140141  41.33685901875662
        exposure        HST  2002-06-29 10:35:56.79+00 ... 10.673753121140141  41.33685901875662
        exposure        HST  2002-06-29 10:35:56.79+00 ... 10.673753121140141  41.33685901875662

This will perform a cone search with radius 7 arcmins around the target (defined by
its coordinates or its name) using the filters defined when executing the function.

This function allows the same parameters than the search criteria (see Section 2).

--------------------------
5. Getting Hubble products
--------------------------

.. warning::

   Please bear in mind that the default format to download
   sets of files has been modified from TAR to ZIP.

After retrieving the metadata, the user can filter the result table and get the rows of interest.
The most important column is 'observation_id' and it is possible to use it to retrieve all the
associated files.

.. note::
    In eHST is it possible to download products based on their observation ID (mandatory) and
    a required calibration_level (RAW, CALIBRATED, PRODUCT or AUXILIARY) and/or product type (SCIENCE, PREVIEW, THUMBNAIL or AUXILIARY).

.. warning::
    Deprecation Warning: product types PRODUCT, SCIENCE_PRODUCT or POSTCARD are no longer supported. Please modify your scripts accordingly.

For instance, next commands will download all files for the raw calibration level
of the observation 'j6fl25s4q' and it will store them in a file called
'raw_data_for_j6fl25s4q.zip'.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.download_product(observation_id="j6fl25s4q", calibration_level="RAW",
  ...                            filename="raw_data_for_j6fl25s4q")
  'raw_data_for_j6fl25s4q.zip'

This second example will download the science files associated to the observation 'j6fl25s4q' and it will store them in a file called
'science_data_for_j6fl25s4q.zip', modifying the filename provided to ensure that the extension of the file is correct.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.download_product(observation_id="j6fl25s4q", product_type="SCIENCE",
  ...                            filename="science_data_for_j6fl25s4q")
  'science_data_for_j6fl25s4q.zip'

This third case will download the science files associated to the observation 'j6fl25s4q' in raw calibration level and it will store them in a file called
'science_raw_data_for_j6fl25s4q.fits.gz', modifying the filename provided to ensure that the extension of the file is correct. There is only
one file fulfilling these conditions and it is a FITS file, so the extension is adapted to the contents of the request.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.download_product(observation_id="j6fl25s4q", calibration_level="RAW",
  ...                            filename="science_raw_data_for_j6fl25s4q", product_type="SCIENCE")
  'science_raw_data_for_j6fl25s4q.fits.gz'

If the user wants to filter the files to be downloaded, this module provides additional mechanisms.

The first step is to query eHST Server to retrieve them. For instance, for observation w0ji0v01t:

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> table = esahubble.get_associated_files(observation_id='w0ji0v01t')
  >>> print(result)    # doctest: +IGNORE_OUTPUT
         filename      calibration_level    type   size_uncompressed
          object             object        object        object
    ------------------ ----------------- --------- -----------------
    w0ji0v01t_c0f.fits        CALIBRATED   science          10035 kB
     w0ji0v01t_c0f.jpg        CALIBRATED   preview             15 kB
                   ...               ...       ...               ...
    w0ji0v01t_shf.fits               RAW auxiliary             31 kB
    w0ji0v01t_trl.fits               RAW auxiliary             23 kB
    w0ji0v01t_x0f.fits               RAW auxiliary            101 kB


Now it is possible to download a specific file using the filename column.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.download_file(file="w0ji0v01t_x0f.fits")
  'w0ji0v01t_x0f.fits.gz'


This will download the compressed file 'w0ji0v01t_x0f.fits.gz'. This table can be iterated to download all the files.

In case the user is only interested in FITS files, this module contains a specific function to execute this request.

.. doctest-remote-data::
  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.download_fits_files(observation_id='w0ji0v01t') # doctest: +IGNORE_OUTPUT

---------------------------
6. Getting Hubble postcards
---------------------------

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.get_postcard(observation_id="j6fl25s4q", calibration_level="RAW", resolution=256, filename="raw_postcard_for_j6fl25s4q.jpg")
  'raw_postcard_for_j6fl25s4q.jpg'

This will download the postcard for the observation 'J8VP03010' with low
resolution (256) and it will stored in a jpg called
'raw_postcard_for_j6fl25s4q.jpg'. Resolution of 1024 is also available.

Calibration levels can be RAW, CALIBRATED, PRODUCT or AUXILIARY.

-------------------------------
7. Getting access to catalogues
-------------------------------

This function provides access to the HST archive database using the Table
Access Protocol (TAP) and via the Astronomical Data Query Language (ADQL).

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_tap(query="select top 10 * from hsc.hubble_sc", output_file="test.vot.gz") # doctest: +IGNORE_OUTPUT

This will execute an ADQL query to download the first 10 sources in the
Hubble Source Catalog (HSC) (format default: compressed
votable). The result of the query will be stored in the file
'test.vot.gz'. The result of this query can be viewed by doing
result.get_results() or printing it by doing print(result).

To access the same information shown in eHST Science Archive:
.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.query_tap(query="select top 10 * from ehst.archive", output_file="archive.vot.gz") # doctest: +IGNORE_OUTPUT


Deprecation Warning: this method was previously named as query_hst_tap. Please modify your scripts accordingly.

------------------------------------------------------
8. Getting related members of HAP and HST observations
------------------------------------------------------

This function takes in an observation id of a Composite or Simple observation.
If the observation is Simple the method returns the Composite observation that
is built on this simple observation. If the observation is Composite then the
method returns the simple observations that make it up.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.get_member_observations(observation_id="jdrz0c010")
  >>> result
  ['jdrz0cjxq', 'jdrz0cjyq']


-------------------------------------------------------
9. Getting link between Simple HAP and HST observations
-------------------------------------------------------

This function takes in an observation id of a Simple HAP or HST observation and
returns the corresponding HAP or HST observation

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.get_hap_hst_link(observation_id="hst_16316_71_acs_sbc_f150lp_jec071i9")
  >>> result
  ['jec071i9q']


-----------------------------------------------------------
10. Retrieve metadata and data from a program / proposal ID
-----------------------------------------------------------

It is possible to retrieve all the observations associated to a specific program ID using the following method:

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> result = esahubble.get_observations_from_program(program=5773)


Using the different functions described in Section 5, it is possible to get the list of files, filter and download them.
Another alternative is using 'download_files_from_program'. By specifying a program ID, users can define other
filters (in a similar way to query_criteria) and download only FITS or all the files associated.

.. doctest-remote-data::

  >>> from astroquery.esa.hubble import ESAHubble
  >>> esahubble = ESAHubble()
  >>> esahubble.download_files_from_program(program=5410,instrument_name='WFPC2',obs_collection='HLA',filters=['F814W/F450W'], only_fits=True)


Reference/API
=============

.. automodapi:: astroquery.esa.hubble
    :no-inheritance-diagram:
