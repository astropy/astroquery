.. doctest-skip-all

.. _astroquery.gaia:

=========
Gaia TAP+
=========

Gaia is an ambitious mission to chart a three-dimensional map of our Galaxy, the Milky Way, 
in the process revealing the composition, formation and evolution of the Galaxy. 
Gaia will provide unprecedented positional and radial velocity measurements with the accuracies needed 
to produce a stereoscopic and kinematic census of about one billion stars in our Galaxy and 
throughout the Local Group. This amounts to about 1 per cent of the Galactic stellar population.

If you use public Gaia DR1 data in your paper, please take note of our guide_ on how to acknowledge and cite Gaia DR1.

.. _guide: http://gaia.esac.esa.int/documentation/GDR1/Miscellaneous/sec_credit_and_citation_instructions.html

This package allows the access to the European Space Agency Gaia Archive (http://archives.esac.esa.int/gaia)

Gaia Archive access is based on a TAP+ REST service. TAP+ is an extension of Table Access Protocol
(TAP: http://www.ivoa.net/documents/TAP/) specified by the International Virtual Observatory Alliance
(IVOA: http://www.ivoa.net).

The TAP query language is Astronomical Data Query Language (ADQL: http://www.ivoa.net/documents/ADQL/2.0), which is similar
to Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes: Synchronous and Asynchronous:

* Synchronous: the response to the request will be generated as soon as the request received by the server.
* Asynchronous: the server will start a job that will execute the request. The first response to the request is the required information (a link) to obtain the job status. Once the job is finished, the results can be retrieved.

Gaia TAP+ server provides two access mode: public and authenticated:

* Public: this is the standard TAP access. A user can execute ADQL queries and upload tables to be used in a query 'on-the-fly' (these tables will be removed once the query is executed). The results are available to any other user and they will remain in the server for a limited space of time.

* Authenticated: some functionalities are restricted to authenticated users only. The results are saved in a private user space and they will remain in the server for ever (they can be removed by the user).

  * ADQL queries and results are saved in a user private area.

  * Cross-match operations: a catalog cross-match operation can be executed. Cross-match operations results are saved in a user private area.

  * Persistence of uploaded tables: a user can upload a table in a private space. These tables can be used in queries as well as in cross-matches operations.


This python module provides an Astroquery API access. Nevertheless, only ``query_object`` and ``query_object_async`` are implemented.

The Gaia Archive table used for the methods where no table is specified is ``gaiadr1.gaia_source``

---------------------------
1. Non authenticated access
---------------------------

1.1. Query object
~~~~~~~~~~~~~~~~~

::

  import astropy.units as u
  from astropy.coordinates.sky_coordinate import SkyCoord
  from astropy.units import Quantity
  from astroquery.gaia import Gaia
  
  coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
  width = Quantity(0.1, u.deg)
  height = Quantity(0.1, u.deg)
  r = Gaia.query_object(coordinate=coord, width=width, height=height)
  print (r)


1.2. Cone search
~~~~~~~~~~~~~~~~

::

  import astropy.units as u
  from astropy.coordinates.sky_coordinate import SkyCoord
  from astropy.units import Quantity
  from astroquery.gaia import Gaia
  
  coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
  radius = Quantity(1.0, u.deg)
  j = Gaia.cone_search(coord, radius)
  r = j.get_results()
  print (r)


1.3 Getting public tables
~~~~~~~~~~~~~~~~~~~~~~~~~

To load only table names (TAP+ capability)

::

  from astroquery.gaia import Gaia
  tables = Gaia.load_tables(only_names=True)
  for table in (tables):
    print (table.get_qualified_name())
  
To load table names (TAP compatible)

::

  from astroquery.gaia import Gaia
  tables = Gaia.load_tables()
  for table in (tables):
    print (table.get_qualified_name())
  
To load only a table (TAP+ capability)

::

  from astroquery.gaia import Gaia
  table = Gaia.load_table('gaiadr1.gaia_source')
 

Once a table is loaded, columns can be inspected

::

  from astroquery.gaia import Gaia
  table = Gaia.load_table('gaiadr1.gaia_source')
  for column in (gaiadr1_table.get_columns()):
    print (column.get_name())


1.4 Synchronous query
~~~~~~~~~~~~~~~~~~~~~

A synchronous query will not store the results at server side. These queries must be used when the amount of data to be retrieve is 'small'.

There is a limit of 2000 rows. If you need more than that, you must use asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

::

  from astroquery.gaia import Gaia

  job = Gaia.launch_job("select top 100 \
  solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
  from gaiadr1.gaia_source order by source_id")
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])

Query saving results in a file:

::

  from astroquery.gaia import Gaia
  job = Gaia.launch_job("select top 100 \
  solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
  from gaiadr1.gaia_source order by source_id", dump_to_file=True)
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])


1.5 Synchronous query on an 'on-the-fly' uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

::

  from astroquery.gaia import Gaia
  
  upload_resource = 'my_table.xml'
  j = Gaia.launch_job(query="select * from tap_upload.table_test", upload_resource=upload_resource, \
  upload_table_name="table_test", verbose=True)
  r = j.get_results()
  print (r)


1.6 Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side. These queries can be accessed at any time. For anonymous users, results are kept for three days.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

::

  from astroquery.gaia import Gaia

  job = Gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id")
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])

Query saving results in a file:

::

  from astroquery.gaia import Gaia
  
  job = Gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id", dump_to_file=True)
  
  print (job)
  r = job.get_results()
  print (r['solution_id'])


1.6 Asynchronous job removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove asynchronous

::

  from astroquery.gaia import Gaia
  
  job = Gaia.remove_jobs(["job_id_1","job_id_2",...])


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

::

  from astroquery.gaia import Gaia
  
  Gaia.login_gui()


Command line


::

  from astroquery.gaia import Gaia
  
  Gaia.login(user='userName', password='userPassword')


It is possible to use a file where the credentials are stored:

*The file must containing user and password in two different lines.*

::

  from astroquery.gaia import Gaia
  
  Gaia.login(credentials_file='my_credentials_file')



To perform a logout


::

  from astroquery.gaia import Gaia
  
  Gaia.logout()



2.2. Listing shared tables
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  from astroquery.gaia import Gaia

  tables = Gaia.load_tables(only_names=True, include_shared_tables=True)
  for table in (tables):
    print (table.get_qualified_name())
  


