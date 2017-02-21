.. doctest-skip-all

.. _astroquery.tap:

=========
TAP/TAP+
=========

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
  request received by the server.
* Asynchronous: the server will start a job that will execute the request. 
  The first response to the request is the required information (a link) to obtain 
  the job status. Once the job is finished, the results can be retrieved.

TAP+ is fully compatible with TAP specification. TAP+ adds more capabilities 
like authenticated access and persistent user storage area.

Please, check methods documentation to determine whether a method is TAP compatible.


---------------------------
1. Non authenticated access
---------------------------

1.1 Getting public tables
~~~~~~~~~~~~~~~~~~~~~~~~~

To load only table names (TAP+ capability)

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  tables = gaia.load_tables(only_names=True)
  for table in (tables):
    print (table.get_qualified_name())
  
To load table names (TAP compatible)

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  tables = gaia.load_tables()
  for table in (tables):
    print (table.get_qualified_name())
  
To load only a table (TAP+ capability)

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  table = gaia.load_table('gaiadr1.gaia_source')
 

Once a table is loaded, columns can be inspected

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  table = gaia.load_table('gaiadr1.gaia_source')
  for column in (gaiadr1_table.get_columns()):
    print (column.get_name())


1.2 Synchronous query
~~~~~~~~~~~~~~~~~~~~~

A synchronous query will not store the results at server side. These queries must be used when the amount of data to be retrieve is 'small'.

There is a limit of 2000 rows. If you need more than that, you must use asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")

  job = gaia.launch_job("select top 100 \
  solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
  from gaiadr1.gaia_source order by source_id")
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])

Query saving results in a file:

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  job = gaia.launch_job("select top 100 \
  solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
  from gaiadr1.gaia_source order by source_id", dump_to_file=True)
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])


1.3 Synchronous query on an 'on-the-fly' uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  
  upload_resource = 'my_table.xml'
  j = gaia.launch_job(query="select * from tap_upload.table_test", upload_resource=upload_resource, \
  upload_table_name="table_test", verbose=True)
  r = j.get_results()
  print (r)


1.4 Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side. These queries can be accessed at any time. For anonymous users, results are kept for three days.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id")
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])

Query saving results in a file:

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id", dump_to_file=True)
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])


1.5 Asynchronous job removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove asynchronous

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  job = gaia.remove_jobs(["job_id_1","job_id_2",...])


-----------------------------------
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
~~~~~~~~~~~~~~~~~

Graphic interface


*Note: Tkinter module is required to use login_gui method.*

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  gaia.login_gui()


Command line


::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  gaia.login(user='userName', password='userPassword')


It is possible to use a file where the credentials are stored:

*The file must containing user and password in two different lines.*

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  gaia.login(credentials_file='my_credentials_file')



To perform a logout


::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  gaia.login(credentials_file='my_credentials_file')
  ...
  
  gaia.logout()



2.2. Listing shared tables
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  from astroquery.tap.core import TapPlus

  gaia = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
  gaia.login(credentials_file='my_credentials_file')

  tables = gaia.load_tables(only_names=True, include_shared_tables=True)
  for table in (tables):
    print (table.get_qualified_name())
  

-------------------------------------------
3. Using TAP+ to connect other TAP services
-------------------------------------------

TAP+ can be used to connect other TAP services.

Example 1: TAPVizieR.u-strasbg.fr

::

  from gaia.tapplus.tap import TapPlus
  
  tap = TapPlus(url="http://TAPVizieR.u-strasbg.fr/TAPVizieR/tap")
  
  #Inspect tables
  tables = tap.load_tables()
  for table in (tables):
    print (table.get_name())
  
  #Launch sync job
  job = tap.launch_job("SELECT top 10 * from " + tables[0].get_name())
  print (job.get_results())
  
Example 2: irsa.ipac.caltech.edu

::

  from gaia.tapplus.tap import TapPlus
  
  tap = TapPlus(url="http://irsa.ipac.caltech.edu/TAP")
  
  job = tap.launch_job_async("SELECT TOP 10 * FROM fp_psc")
  r = job.get_results()
  print (r)

Please, check methods documentation to determine whether a method is TAP compatible.
