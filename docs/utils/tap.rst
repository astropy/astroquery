.. doctest-skip-all

.. _astroquery.utils.tap:

*********************************
TAP/TAP+ (`astroquery.utils.tap`)
*********************************

Table Access Protocol (TAP: http://www.ivoa.net/documents/TAP/) specified by the
International Virtual Observatory Alliance (IVOA: http://www.ivoa.net) defines
a service protocol for accessing general table data.

TAP+ is the ESAC Space Data Centre (ESDC: http://www.cosmos.esa.int/web/esdc/)
extension of the Table Access Protocol.

The TAP query language is Astronomical Data Query Language (ADQL:
http://www.ivoa.net/documents/ADQL/2.0), which is similar
to Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes: Synchronous and Asynchronous:

* Synchronous: the response to the request will be generated as soon as the
  request received by the server. (Do not use this method for queries that
  generate a big amount of results.)

* Asynchronous: the server will start a job that will execute the request.
  The first response to the request is the required information (a link) to obtain
  the job status. Once the job is finished, the results can be retrieved.

TAP+ is fully compatible with TAP specification. TAP+ adds more capabilities
like authenticated access and persistent user storage area.

Please, check methods documentation to determine whether a method is TAP compatible.

========
Examples
========


1. Non authenticated access
---------------------------

1.1 Getting public tables
^^^^^^^^^^^^^^^^^^^^^^^^^

To load only table names (TAP+ capability)

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="https://gea.esac.esa.int/tap-server/tap")
  >>> tables = gaia.load_tables(only_names=True)
  >>> for table in (tables):
  >>>   print(table.get_qualified_name())

  public.dual
  public.tycho2
  public.igsl_source
  public.hipparcos
  public.hipparcos_newreduction
  public.hubble_sc
  public.igsl_source_catalog_ids
  tap_schema.tables
  tap_schema.keys
  tap_schema.columns
  tap_schema.schemas
  tap_schema.key_columns
  gaiadr1.phot_variable_time_series_gfov
  gaiadr1.ppmxl_neighbourhood
  gaiadr1.gsc23_neighbourhood
  gaiadr1.ppmxl_best_neighbour
  gaiadr1.sdss_dr9_neighbourhood
  ...
  gaiadr1.tgas_source
  gaiadr1.urat1_original_valid
  gaiadr1.allwise_original_valid

To load table names (TAP compatible)

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> tables = gaia.load_tables()
  >>> for table in (tables):
  >>>   print(table.get_qualified_name())

  public.dual
  public.tycho2
  public.igsl_source
  public.hipparcos
  public.hipparcos_newreduction
  public.hubble_sc
  public.igsl_source_catalog_ids
  tap_schema.tables
  tap_schema.keys
  tap_schema.columns
  tap_schema.schemas
  tap_schema.key_columns
  gaiadr1.phot_variable_time_series_gfov
  gaiadr1.ppmxl_neighbourhood
  gaiadr1.gsc23_neighbourhood
  gaiadr1.ppmxl_best_neighbour
  gaiadr1.sdss_dr9_neighbourhood
  ...
  gaiadr1.tgas_source
  gaiadr1.urat1_original_valid
  gaiadr1.allwise_original_valid

To load only a table (TAP+ capability)

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> table = gaia.load_table('gaiadr1.gaia_source')
  >>> print(table)

  Table name: gaiadr1.gaia_source
  Description: This table has an entry for every Gaia observed source as listed in the
  Main Database accumulating catalogue version from which the catalogue
  release has been generated. It contains the basic source parameters,
  that is only final data (no epoch data) and no spectra (neither final
  nor epoch).
  Num. columns: 57

Once a table is loaded, columns can be inspected

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> table = gaia.load_table('gaiadr1.gaia_source')
  >>> for column in (table.columns):
  >>>   print(column.name)

  solution_id
  source_id
  random_index
  ref_epoch
  ra
  ra_error
  dec
  dec_error
  ...
  ecl_lon
  ecl_lat


1.2 Synchronous query
^^^^^^^^^^^^^^^^^^^^^

A synchronous query will not store the results at server side. These queries must be used when the amount of data to be retrieve is 'small'.

There is a limit of 2000 rows. If you need more than that, you must use asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="https://gea.esac.esa.int/tap-server/tap")
  >>>
  >>> job = gaia.launch_job("select top 100 \
  >>> solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
  >>> from gaiadr1.gaia_source order by source_id")
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
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  Length = 100 rows

Query saving results in a file:

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> job = gaia.launch_job("select top 100 \
  >>> solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
  >>> from gaiadr1.gaia_source order by source_id", dump_to_file=True)
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
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  Length = 100 rows


1.3 Synchronous query on an 'on-the-fly' uploaded table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A table can be uploaded to the server in order to be used in a query.

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>>
  >>> upload_resource = 'my_table.xml'
  >>> j = gaia.launch_job(query="select * from tap_upload.table_test", upload_resource=upload_resource, \
  >>> upload_table_name="table_test", verbose=True)
  >>> r = j.get_results()
  >>> r.pprint()

  source_id alpha delta
  --------- ----- -----
          a   1.0   2.0
          b   3.0   4.0
          c   5.0   6.0


1.4 Asynchronous query
^^^^^^^^^^^^^^^^^^^^^^

Asynchronous queries save results at server side. These queries can be accessed at any time. For anonymous users, results are kept for three days.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id")
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
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  Length = 100 rows

Query saving results in a file:

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>>
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id", dump_to_file=True)
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
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
                ...
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  1635378410781933568
  Length = 100 rows


1.5 Asynchronous job removal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To remove asynchronous

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> job = gaia.remove_jobs(["job_id_1","job_id_2",...])


2. Authenticated access (TAP+ only)
-----------------------------------

Authenticated users are able to access to TAP+ capabilities (shared tables, persistent jobs, etc.)
In order to authenticate a user, ``login`` or ``login_gui`` methods must be called. After a successful
authentication, the user will be authenticated until ``logout`` method is called.

All previous methods (``query_object``, ``cone_search``, ``load_table``, ``load_tables``, ``launch_job``) explained for
non authenticated users are applicable for authenticated ones.

The main differences are:

* Asynchronous results are kept at server side for ever (until the user decides to remove one of them).
* Users can access to shared tables.


2.1. Login/Logout
^^^^^^^^^^^^^^^^^

Graphic interface


*Note: Tkinter module is required to use login_gui method.*

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login_gui()


Command line


.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login(user='userName', password='userPassword')


It is possible to use a file where the credentials are stored:

*The file must containing user and password in two different lines.*

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login(credentials_file='my_credentials_file')


If you do not provide any parameters at all, a prompt will ask for user name and password.

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> User: user
  >>> Password: pwd (not visible) 


To perform a logout


.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login(credentials_file='my_credentials_file')
  >>> ...
  >>>
  >>> gaia.logout()



2.2. Listing shared tables
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login(credentials_file='my_credentials_file')
  >>> tables = gaia.load_tables(only_names=True, include_shared_tables=True)
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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is now possible to persist a table in the private user space. The table to be uploaded can be in a url, a file, a job or a astropy Table.

The table is stored into the user private area in the database. Each user has a database schema. The schema name is 'user_<user_login_name>'.

For instance, if a login name is 'joe', the database schema is 'user_joe'.

Your uploaded table can be referenced as 'user_joe.table_name'

2.2.1. Uploading table from url to user space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> # Provide a URL pointing to a valid VOTable resource
  >>> url = "http://tapvizier.u-strasbg.fr/TAPVizieR/tap/sync/?REQUEST=doQuery&lang=ADQL&FORMAT=votable&QUERY=select+*+from+TAP_SCHEMA.columns+where+table_name='II/336/apass9'"
  >>> job = gaia.upload_table(upload_resource=url, table_name="table_test_from_url", table_description="Some description")

  Job '1539932326689O' created to upload table 'table_test_from_url'.

Now, you can query your table as follows:

.. code-block:: python

  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_url'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)


2.2.2. Uploading table from file to user space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> job = gaia.upload_table(upload_resource="1535553556177O-result.vot", table_name="table_test_from_file", format="VOTable")

  Sending file: 1535553556177O-result.vot
  Uploaded table 'table_test_from_file'.

Now, you can query your table as follows:

.. code-block:: python
  
  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_file'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)

2.2.3. Uploading table from job to user space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> j1 = gaia.launch_job_async("select top 10 * from gaiadr2.gaia_source")
  >>> job = gaia.upload_table_from_job(j1)
  
  Created table 't1539932994481O' from job: '1539932994481O'.

Now, you can query your table as follows:

.. code-block:: python
  
  >>> full_qualified_table_name = 'user_<your_login_name>.t1539932994481O'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)


2.2.4. Uploading table from an astropy Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> from astropy.table import Table
  >>> a=[1,2,3]
  >>> b=['a','b','c']
  >>> table = Table([a,b], names=['col1','col2'], meta={'meta':'first table'})
  >>>
  >>> # Upload
  >>> gaia.login()
  >>> gaia.upload_table(upload_resource=table, table_name='my_table')

Now, you can query your table as follows:

.. code-block:: python
  
  >>> full_qualified_table_name = 'user_<your_login_name>.my_table'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = gaia.launch_job(query=query)
  >>> results = job.get_resultsjob)
  >>> print(results)

2.3. Deleting table from user space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login_gui()
  >>> job = gaia.delete_user_table("table_test_from_file")
  
  Table 'table_test_from_file' deleted.
  
2.4. Updating metadata of table in user space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Metadata of a user table can be updated by specifying the changes to be done.

.. code-block:: python

  >>> gaia.update_user_table(table_name, list_of_changes)

The format defined to specify a change is the following:

["column name to be changed", "metadata parameter to be changed", "new value"]

metadata parameter to be changed can be 'utype', 'ucd', 'flags' or 'indexed'

values for 'utype' and 'ucd' are free text
value for 'flags' can be 'Ra', 'Dec', 'Mag', 'Flux' and 'PK'
value for 'indexed' is a boolean indicating if the column is indexed

It is possible to specify a list of those changes for them to be applied at once. 
This is done by putting each of the changes in a list. See example below.

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login_gui()
  >>> gaia.update_user_table(table_name="user_<user_login_name>.my_table", list_of_changes=[["recno", "ucd", "ucd sample"], ["nobs","utype","utype sample"], ["raj2000","flags","Ra"], ["dej2000","flags","Dec"]])
  
  Retrieving table 'user_<user_login_name>.my_table'
  Parsing table 'user_<user_login_name>.my_table'...
  Done.
  Table 'user_<user_login_name>.my_table' updated.                                                          

2.5. Tables sharing
^^^^^^^^^^^^^^^^^^^

You can share your tables to other users. You have to create a group, populate that group with users, and share your table to that group.
Then, any user belonging to that group will be able to user your shared table in a query.

2.5.1 Creating a group
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> gaia.share_group_create(group_name="my_group", description="description")

2.5.2 Removing a group
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> gaia.share_group_delete(group_name="my_group")

2.5.3 Adding users to a group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> gaia.share_group_add_user(group_name="my_group",user_id="<user_login_name")


2.5.4 Removing users from a group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> gaia.share_group_delete_user(group_name="my_group",user_id="<user_login_name>")


2.5.5 Sharing a table to a group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> gaia.share_table(group_name="my_group",table_name="user_<user_loign_name>.my_table",description="description")


2.5.6 Stop sharing a table
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> gaia.login()
  >>> gaia.share_table_stop(table_name="user_<user_login_name>.my_table", group_name="my_group")


2.6. Data access
~~~~~~~~~~~~~~~~

TAP+ services may provide a data access entry point.

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> params_dict = {}
  >>> params_dict['VALID_DATA'] = "true"
  >>> params_dict['ID'] = "1000103304040175360" 
  >>> params_dict['FORMAT'] = "votable"
  >>> params_dict['RETRIEVAL_TYPE'] = "epoch_photometry"
  >>> gaia.load_data(params_dict=params_dict, output_file="results.vot")

You may download data into memory:

.. code-block:: python
  
  >>> results = gaia.load_data(params_dict=params_dict)


2.7. Datalink access
~~~~~~~~~~~~~~~~~~~~

This service provides links to data:

.. code-block:: python
  
  >>> from astroquery.utils.tap.core import TapPlus
  >>> gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  >>> ids="1000103304040175360,1000117258390464896"
  >>> results = gaia.get_datalink(ids=ids)



3. Using TAP+ to connect other TAP services
-------------------------------------------

TAP+ can be used to connect other TAP services.

Example 1: TAPVizieR.u-strasbg.fr

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> tap = TapPlus(url="http://TAPVizieR.u-strasbg.fr/TAPVizieR/tap")
  >>> #Inspect tables
  >>> tables = tap.load_tables()
  >>> for table in (tables):
  >>>   print(table.get_name())

  ...
  J/ApJS/173/104/memb
  J/A+A/376/441/table1
  J/A+AS/110/81/table2
  J/ApJS/73/781/snr_indx
  V/15/notes
  J/A+AS/115/285/refs
  J/ApJS/165/338/table1
  IX/24/obsnames
  J/A+AS/122/463/tab2-14
  J/ApJS/107/521/table1
  J/MNRAS/275/1102/table1a
  J/ApJ/647/328/table4
  J/A+A/402/1/table1a
  J/AJ/115/1856/v12
  ...

  >>> #Launch sync job
  >>> job = tap.launch_job("SELECT top 10 * from " + tables[0].get_name())
  >>> r = job.get_results()
  >>> r.pprint()

                         title                         class [1] ... comment
  ---------------------------------------------------- --------- ... -------
  The 2MASS Point Source and 2MASS6x catalogues (2003)       2 ...
          The 2MASS Extended Source Catalogue (2003)         2 ...
       Astrographic catalog (mean epoch around 1900)         2 ...
  AKARI IRC (9/18um) and FIS (60-160um)all-sky Surveys       2 ...
           All-Sky Compiled Catalog of 2.5M*  (2003)         2 ...
       The DENIS database (3rd Release 2005 version)         2 ...
     The Carlsberg Meridian Catalog 14 (-30<Dec<+50)         2 ...
           GALEX-DR5 sources from AIS and MIS (2011)         2 ...
         Spitzer's GLIMPSE catalogs (Galactic Plane)         2 ...
   The HST Guide Star Catalog reduced on Tycho (ACT)         2 ...
  Example 2: irsa.ipac.caltech.edu

.. code-block:: python

  >>> from astroquery.utils.tap.core import TapPlus
  >>> tap = TapPlus(url="http://irsa.ipac.caltech.edu/TAP")
  >>> job = tap.launch_job_async("SELECT TOP 10 * FROM fp_psc")
  >>> r = job.get_results()
  >>> r.pprint()

     name      dtype   unit format n_bad
  ------------- ------- ----- ------ -----
         cntr   int32                  0
        hemis  object                  0
        xdate  object                  0
         scan   int32                  0
           id   int32                  0
           ra float64   deg     %r     0
          dec float64   deg     %r     0
         glon float64   deg     %r     0
         glat float64   deg     %r     0
            x float64           %r     0
            y float64           %r     0
            z float64           %r     0
      err_maj float64  arcs     %r     0
      err_min float64  arcs     %r     0
      err_ang   int32   deg            0
       x_scan float64  arcs     %r     0
       y_scan float64  arcs     %r     0
  ...

Please, check methods documentation to determine whether a method is TAP compatible.


=============
Reference/API
=============

.. automodapi:: astroquery.utils.tap
    :no-inheritance-diagram:
