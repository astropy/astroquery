.. doctest-skip-all

.. _astroquery.gaia:

*****************************
Gaia TAP+ (`astroquery.gaia`)
*****************************

Gaia is a European space mission providing astrometry, photometry, and spectroscopy of
more than 1000 million stars in the Milky Way. Also data for significant samples of
extragalactic and Solar system objects is made available. The Gaia Archive contains
deduced positions, parallaxes, proper motions, radial velocities, and brightnesses.
Complementary information on multiplicity, photometric variability, and astrophysical
parameters is provided for a large fraction of sources.

If you use public Gaia data in your paper, please take note of our guide_ on
how to acknowledge and cite Gaia data.

.. _guide: https://gea.esac.esa.int/archive/documentation/credits.html

This package allows the access to the European Space Agency Gaia Archive
(http://gea.esac.esa.int/archive/).

Gaia Archive access is based on a TAP+ REST_ service. TAP+ is an extension of
Table Access Protocol (TAP: http://www.ivoa.net/documents/TAP/) specified by the
International Virtual Observatory Alliance (IVOA: http://www.ivoa.net).

.. _REST: https://en.wikipedia.org/wiki/Representational_state_transfer

The TAP query language is Astronomical Data Query Language
(ADQL: http://www.ivoa.net/documents/ADQL/2.0), which is similar
to Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes:

* Synchronous: the response to the request will be generated as soon as the
  request received by the server (do not use this method for queries that
  generate a big amount of results).
* Asynchronous: the server will start a job that will execute the request.
  The first response to the request is the required information (a link)
  to obtain the job status.
  Once the job is finished, the results can be retrieved.

Gaia TAP+ server provides two access modes:

* Public: this is the standard TAP access. A user can execute ADQL queries and
  upload tables to be used in a query 'on-the-fly' (these tables will be removed
  once the query is executed). The results are available to any other user and
  they will remain in the server for a limited time.

* Authenticated: some functionalities are restricted to authenticated users only.
  The ADQL queries and their outcomes will remain in the server until the user deletes
  them. The dedicated functionalities include:

  * Cross-match operations: a catalog cross-match operation can be executed.

  * Persistence of uploaded tables: a user can upload a table in a private space.
    These tables can be used in queries as well as in cross-matches operations.


This python module provides an Astroquery API access. Nevertheless, only
``query_object`` and ``query_object_async`` are implemented.

The Gaia Archive table used for the methods where no table is specified is
``gaiadr1.gaia_source``

========
Examples
========

---------------------------
1. Public access
---------------------------

1.1. Query object
~~~~~~~~~~~~~~~~~

This query searches for all the objects contained in an arbitrary rectangular projection of the sky.

The following example, searches around an specific Ra/Dec coordinates, creating a box of 0.1 degrees.

.. code-block:: python

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.gaia import Gaia
  >>>
  >>> coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
  >>> width = u.Quantity(0.1, u.deg)
  >>> height = u.Quantity(0.1, u.deg)
  >>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
  >>> r.pprint()

           dist             solution_id     ...       ecl_lat
                                            ...      Angle[deg]
  --------------------- ------------------- ... -------------------
  0.0026029414438061079 1635378410781933568 ... -36.779151653783892
  0.0038537557334594502 1635378410781933568 ... -36.773899692008634
  0.0045451702670639632 1635378410781933568 ... -36.772645786277522
  0.0056131312891700424 1635378410781933568 ... -36.781488832325074
                  ...                 ... ...                 ...
  Length = 152 rows


1.2. Cone search
~~~~~~~~~~~~~~~~

This query performs a cone search centered at the specified Ra/Dec coordinates with the provided
radius argument.

.. code-block:: python

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.gaia import Gaia
  >>>
  >>> coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
  >>> radius = u.Quantity(1.0, u.deg)
  >>> j = Gaia.cone_search_async(coord, radius)
  >>> r = j.get_results()
  >>> r.pprint()

           dist             solution_id     ...       ecl_lat
                                          ...      Angle[deg]
  --------------------- ------------------- ... -------------------
  0.0026029414438061079 1635378410781933568 ... -36.779151653783892
  0.0038537557334594502 1635378410781933568 ... -36.773899692008634
  0.0045451702670639632 1635378410781933568 ... -36.772645786277522
  0.0056131312891700424 1635378410781933568 ... -36.781488832325074
                  ...                 ... ...                 ...
  Length = 2000 rows



1.3. Getting public tables metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Table and columns metadata are specified by IVOA TAP_ recommendation
(to access to the actual data, an ADQL query must be executed).

.. _TAP: http://ivoa.info/documents/TAP/20100327/

To load only table names metadata (TAP+ capability)

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> tables = Gaia.load_tables(only_names=True)
  >>> for table in (tables):
  >>>   print(table.get_qualified_name())

  public.dual
  public.tycho2
  public.igsl_source
  public.hipparcos
  ...
  gaiadr2.gaia_source

To load all tables metadata (TAP compatible)

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> tables = Gaia.load_tables()
  >>> for table in (tables):
  >>>   print(table.get_qualified_name())

  public.dual
  public.tycho2
  public.igsl_source
  public.hipparcos
  ...
  gaiadr2.gaia_source

To load only a table (TAP+ capability)

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> table = Gaia.load_table('gaiadr2.gaia_source')
  >>> print(table)

  Table name: gaiadr2.gaia_source
  Description: This table has an entry for every Gaia observed source as listed in the
  Main Database accumulating catalogue version from which the catalogue
  release has been generated. It contains the basic source parameters,
  that is only final data (no epoch data) and no spectra (neither final
  nor epoch).
  Num. columns: 96


Once a table is loaded, columns can be inspected

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> gaiadr2_table = Gaia.load_table('gaiadr2.gaia_source')
  >>> for column in (gaiadr2_table.columns):
  >>>   print(column.name)

  solution_id
  designation
  source_id
  random_index
  ref_epoch
  ra
  ra_error
  dec
  dec_error
  ...

1.4. Synchronous query
~~~~~~~~~~~~~~~~~~~~~~

The results of a synchronous query are stored at the user side (i.e., they are not saved in the
server). These queries must be used when the amount of data to be retrieved (number of rows)
is small, otherwise, a timeout error can be raised (exceeded the amount of time for a query
to be executed).

There is a limit of 2000 rows. If you need more than that, you must use asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>>
  >>> job = Gaia.launch_job("select top 100 \
  >>> solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,\
  >>> matched_observations,duplicated_source,phot_variable_flag \
  >>> from gaiadr2.gaia_source order by source_id")
  >>>
  >>> print(job)

  <Table length=100>
          name          dtype  unit                     description
  -------------------- ------- ---- ---------------------------------------------------
           solution_id   int64                                      Solution Identifier
             ref_epoch float64   yr                                     Reference epoch
           ra_dec_corr float32      Correlation between right ascension and declination
  astrometric_n_obs_al   int32                          Total number of observations AL
  matched_observations   int16            Amount of observations matched to this source
     duplicated_source    bool                            Source with duplicate sources
    phot_variable_flag  object                             Photometric variability flag
  Jobid: None
  Phase: COMPLETED
  Owner: None
  Output file: sync_20200525141041.xml.gz
  Results: None

  >>> r = job.get_results()
  >>> print(r['solution_id'])

    solution_id
  -------------------
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  Length = 100 rows

Query saving results in a file (you may use 'output_format' to specified the results data format,
available formats are: 'votable', 'votable_plain', 'fits', 'csv' and 'json', default is 'votable'):

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> job = Gaia.launch_job("select top 100 \
  >>> solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,\
  >>> matched_observations,duplicated_source,phot_variable_flag \
  >>> from gaiadr2.gaia_source order by source_id", dump_to_file=True)
  >>>
  >>> print(job)

  Jobid: None
  Phase: COMPLETED
  Owner: None
  Output file: sync_20170223111452.xml.gz
  Results: None

  >>> r = job.get_results()
  >>> print(r['solution_id'])

    solution_id
  -------------------
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  Length = 100 rows


1.5. Synchronous query on an 'on-the-fly' uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

You have to provide the local path to the file you want to upload. In the following example,
the file 'my_table.xml' is located to the relative location where your python program is
running. See note below.

.. code-block:: python

  from astroquery.gaia import Gaia

  >>> upload_resource = 'my_table.xml'
  >>> j = Gaia.launch_job(query="select * from tap_upload.table_test", \
  >>> upload_resource=upload_resource, upload_table_name="table_test", verbose=True)
  >>> r = j.get_results()
  >>> r.pprint()

  source_id alpha delta
  --------- ----- -----
          a   1.0   2.0
          b   3.0   4.0
          c   5.0   6.0

Note: to obtain the current location, type:

.. code-block:: python

  import os
  print(os.getcwd())

1.6. Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side and depends on the user files quota.
These queries can be accessed at any time. For anonymous users, results are kept for three days.

Queries retrieved results can be stored locally in memory (by default) or in a file.

Query without saving results in a file:

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>>
  >>> job = Gaia.launch_job_async("select top 100 designation,ra,dec from gaiadr2.gaia_source order by source_id")
  >>> r = job.get_results()
  >>> print(r)

     designation               ra                 dec
                              deg                 deg
  ---------------------- ------------------ --------------------
     Gaia DR2 4295806720 44.996153684159594 0.005615806210679649
    Gaia DR2 34361129088 45.004316164207644 0.021045032689712983
    Gaia DR2 38655544960   45.0049742449841 0.019877000365797714
   Gaia DR2 309238066432  44.99503703932583  0.03815183599451371
   Gaia DR2 343597448960  44.96389532530429 0.043595184822725674
                ...
  Length = 100 rows

Query saving results in a file (you may use 'output_format' to specified the results data format,
available formats are: 'votable', 'votable_plain', 'fits', 'csv' and 'json', default is 'votable'):

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>>
  >>> job = Gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id", dump_to_file=True)
  >>>
  >>> print(job)

  Jobid: 1487845273526O
  Phase: COMPLETED
  Owner: None
  Output file: async_20170223112113.vot
  Results: None

  >>> r = job.get_results()
  >>> print(r['solution_id'])

    solution_id
  -------------------
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  Length = 100 rows


1.6. Asynchronous job removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove asynchronous

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.remove_jobs(["job_id_1","job_id_2",...])


---------------------------
2. Authenticated access
---------------------------

Authenticated users are able to access to TAP+ capabilities (shared tables, persistent jobs, etc.)
In order to authenticate a user, ``login`` or ``login_gui`` methods must be called. After a successful
authentication, the user will be authenticated until ``logout`` method is called.

All previous methods (``query_object``, ``cone_search``, ``load_table``, ``load_tables``, ``launch_job``) explained for
non authenticated users are applicable for authenticated ones.

The main differences are:

* Asynchronous results are kept at server side for ever (until the user decides to remove one of them).
* Users can access to shared tables.


2.1. Login/Logout
~~~~~~~~~~~~~~~~~

Graphic interface


*Note: Tkinter module is required to use login_gui method.*

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()


Command line


.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login(user='userName', password='userPassword')


It is possible to use a file where the credentials are stored:

*The file must containing user and password in two different lines.*

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login(credentials_file='my_credentials_file')


If you do not provide any parameters at all, a prompt will ask for user name and password.

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> User: user
  >>> Password: pwd (not visible)


To perform a logout


.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.logout()



2.2. Listing shared tables
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> tables = Gaia.load_tables(only_names=True, include_shared_tables=True)
  >>> for table in (tables):
  >>>   print(table.get_qualified_name())

  public.dual
  public.tycho2
  public.igsl_source
  tap_schema.tables
  tap_schema.keys
  tap_schema.columns
  tap_schema.schemas
  tap_schema.key_columns
  gaiadr1.phot_variable_time_series_gfov
  gaiadr1.ppmxl_neighbourhood
  gaiadr1.gsc23_neighbourhood
  ...
  user_schema_1.table1
  user_schema_2.table1
  ...

2.2. Uploading table to user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is now possible to persist a table in the private user space. The table to be uploaded can be in a url, a file, a job or a astropy Table.

The table is stored into the user private area in the database. Each user has a database schema. The schema name is 'user_<user_login_name>'.

For instance, if a login name is 'joe', the database schema is 'user_joe'.

Your uploaded table can be referenced as 'user_joe.table_name'


2.2.1. Uploading table from url to user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> # Provide a URL pointing to valid VOTable resource
  >>> url = "http://tapvizier.u-strasbg.fr/TAPVizieR/tap/sync/?REQUEST=doQuery&lang=ADQL&FORMAT=votable&QUERY=select+*+from+TAP_SCHEMA.columns+where+table_name='II/336/apass9'"
  >>> job = Gaia.upload_table(upload_resource=url, table_name="table_test_from_url", table_description="Some description")

  Job '1539932326689O' created to upload table 'table_test_from_url'.

Now, you can query your table as follows:

.. code-block:: python

  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_url'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)


2.2.2. Uploading table from file to user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> job = Gaia.upload_table(upload_resource="1535553556177O-result.vot", table_name="table_test_from_file", format="VOTable")

  Sending file: 1535553556177O-result.vot
  Uploaded table 'table_test_from_file'.

Now, you can query your table as follows:

.. code-block:: python

  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_file'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)


2.2.3. Uploading table from job to user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> j1 = Gaia.launch_job_async("select top 10 * from gaiadr2.gaia_source")
  >>> job = Gaia.upload_table_from_job(j1)

  Created table 't1539932994481O' from job: '1539932994481O'.

Now, you can query your table as follows:

.. code-block:: python

  >>> full_qualified_table_name = 'user_<your_login_name>.t1539932994481O'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)

2.2.4. Uploading table from an astropy Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> from astropy.table import Table
  >>> a=[1,2,3]
  >>> b=['a','b','c']
  >>> table = Table([a,b], names=['col1','col2'], meta={'meta':'first table'})
  >>>
  >>> # Upload
  >>> Gaia.login()
  >>> Gaia.upload_table(upload_resource=table, table_name='my_table')

Now, you can query your table as follows:

.. code-block:: python

  >>> full_qualified_table_name = 'user_<your_login_name>.my_table'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)


2.3. Deleting table from user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()
  >>> job = Gaia.delete_user_table("table_test_from_file")

  Table 'table_test_from_file' deleted.

2.4. Updating metadata of table in user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Metadata of a user table can be updated by specifying the changes to be done.

.. code-block:: python

  >>> Gaia.update_user_table(table_name, list_of_changes)

The format defined to specify a change is the following:

["column name to be changed", "metadata parameter to be changed", "new value"]

metadata parameter to be changed can be 'utype', 'ucd', 'flags' or 'indexed'

values for 'utype' and 'ucd' are free text
value for 'flags' can be 'Ra', 'Dec', 'Mag', 'Flux' and 'PK'
value for 'indexed' is a boolean indicating if the column is indexed

It is possible to specify a list of those changes for them to be applied at once.
This is done by putting each of the changes in a list. See example below.

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()
  >>> Gaia.update_user_table(table_name="user_<user_login_name>.my_table", list_of_changes=[["recno", "ucd", "ucd sample"], ["nobs","utype","utype sample"], ["raj2000","flags","Ra"], ["dej2000","flags","Dec"]])

  Retrieving table 'user_<user_login_name>.my_table'
  Parsing table 'user_<user_login_name>.my_table'...
  Done.
  Table 'user_<user_login_name>.my_table' updated.


2.5. Tables sharing
~~~~~~~~~~~~~~~~~~~

You can share your tables to other users. You have to create a group, populate that group with users, and share your table to that group.
Then, any user belonging to that group will be able to user your shared table in a query.

2.5.1. Creating a group
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_create(group_name="my_group", description="description")

2.5.2. Removing a group
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_delete(group_name="my_group")

2.5.3. Adding users to a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_add_user(group_name="my_group",user_id="<user_login_name")

2.5.4. Removing users from a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_delete_user(group_name="my_group",user_id="<user_login_name>")


2.5.5. Sharing a table to a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_table(group_name="my_group",table_name="user_<user_loign_name>.my_table",description="description")


2.5.6. Stop sharing a table
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_table_stop(table_name="user_<user_login_name>.my_table", group_name="my_group")



2.6. Cross match
~~~~~~~~~~~~~~~~

In gaia you can execute a cross match between tables based on distance.

Usually, you will use an uploaded table or a shared table.

You must be logged in in order to perform a cross match. This is required because the cross match operation will generate a join table in the user private area. That table contains the identifiers of both tables and the distance. Later, the table can be used to obtain the actual data from both tables.

The following example uploads a table and then, the table is used in a cross match:

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>>
  >>> table = file or astropy.table
  >>> Gaia.upload_table(upload_resource=table, table_name='my_sources')
  >>>
  >>> # the table will be uploaded into the user private space into the database
  >>> # the table can be referenced as <database user schema>.<table_name>
  >>>
  >>> full_qualified_table_name = 'user_<your_login_name>.my_sources'
  >>> xmatch_table_name = 'xmatch_table'
  >>> Gaia.cross_match(full_qualified_table_name_a=full_qualified_table_name, \
  >>>               full_qualified_table_name_b='gaiadr2.gaia_source', \
  >>>               results_table_name=xmatch_table_name, radius=1.0)
  >>>
  >>> # Once you have your cross match finished, you can obtain the results:
  >>> xmatch_table = 'user_<your_login_name>.' + xmatch_table_name
  >>> query = 'SELECT c."dist", a.*, b.* FROM gaiadr2.data_source AS a, '+\
  >>> full_qualified_table_name+' AS b, '+\
  >>> xmatch_table+' AS c '+\
  >>> 'WHERE (c.gaia_source_source_id = a.source_id AND c.my_sources_my_sources_oid = b.my_sources_oid)'
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)




2.7. Data products access (datalink)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Different data products are retrieved as one or more tables from the Gaia archive.

In order to download data products, you need to know the identifiers of the sources you are interested in.

So, the first step, is to execute a query to obtain the identifiers, and then you can retrieve the data.

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> query = "SELECT TOP 500 * FROM gaiadr2.gaia_source  \
  >>> WHERE CONTAINS(POINT('ICRS',gaiadr2.gaia_source.ra,gaiadr2.gaia_source.dec),\
  >>> CIRCLE('ICRS',COORD1(\
  >>> EPOCH_PROP_POS(339.8049024487712,64.8585025696523,2.3585,92.7710,190.7920,.3000,2000,2015.5)),\
  >>> COORD2(EPOCH_PROP_POS(339.8049024487712,64.8585025696523,2.3585,92.7710,190.7920,.3000,2000,2015.5)),0.001388888888888889))=1"
  >>>
  >>> job = Gaia.launch_job(query)
  >>>
  >>> results = job.get_results()
  >>> ids=results['source_id']
  >>> print(ids)
  >>>
  >>> # Retrieve data products
  >>> all = Gaia.load_data(ids=ids, format='fits', data_release='Gaia DR2')

  Retrieving data.
  Done.

  List of products available:
  Product = RVS_SPECTRA-Gaia DR2 4203426768245304192.fits
  Product = RVS_SPECTRA-Gaia DR2 4257750098718805248.fits
  Product = XP_BASIS-Gaia DR2 4203426768245304192.fits
  Product = MCMC-Gaia DR2 4257750098718805248.fits
  Product = XP_SPECTRA-Gaia DR2 4257750098718805248.fits
  Product = EPOCH_PHOTOMETRY-Gaia DR2 4257750098718805248.fits
  Product = XP_BASIS-Gaia DR2 4257750098718805248.fits
  Product = MCMC-Gaia DR2 4203426768245304192.fits
  Product = XP_SPECTRA-Gaia DR2 4203426768245304192.fits

  >>> # Get one data product above listed
  >>> all['RVS_SPECTRA-Gaia DR2 4203426768245304192.fits']

  <Table length=2400>

  wavelength    flux     flux_error
  nm
  float64    float32     float32
  ---------- ---------- -----------
  846.0   1.1543361  0.14655493
  846.01  1.0716769  0.09160478

  ...        ...         ...

  869.77  1.0126361  0.03356205
  869.78  1.0286258 0.035302058


Reference/API
=============

.. automodapi:: astroquery.gaia
    :no-inheritance-diagram:
