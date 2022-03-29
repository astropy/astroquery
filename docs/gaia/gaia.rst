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
    These tables can be used in queries as well as in cross-match operations.


This python module provides an Astroquery API access that implements the
``query_object`` and ``query_object_async`` methods.

The Gaia Archive table used for the methods where no table is specified is
the latest data release catalogue.

========
Examples
========

---------------------------
1. Public access
---------------------------

1.1. Query object
~~~~~~~~~~~~~~~~~

This query searches for all the objects contained in an arbitrary rectangular projection of the sky.

It is possible to choose which data release to query, by default the Gaia DR2 catalogue is used. For example::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.MAIN_GAIA_TABLE = "gaiaedr3.gaia_source" # Select early Data Release 3
  >>> Gaia.MAIN_GAIA_TABLE = "gaiadr2.gaia_source"  # Reselect Data Release 2, default

The following example searches for all the sources contained in an squared region of side = 0.1
degrees around an specific point in RA/Dec coordinates.

.. doctest-remote-data::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.gaia import Gaia
  >>>
  >>> coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
  >>> width = u.Quantity(0.1, u.deg)
  >>> height = u.Quantity(0.1, u.deg)
  >>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> r.pprint(max_lines=12, max_width=130)
           dist             solution_id     ...                                     datalink_url
                                            ...
  --------------------- ------------------- ... -----------------------------------------------------------------------------------
  0.0026034636994048854 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814214528
  0.0038518741347606357 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090339113063296
    0.00454542650096783 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814217600
                    ...                 ... ...                                                                                 ...
   0.020307185970548904 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636089514478069888
   0.020454730686780127 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636066940131244288
   0.020802655215768254 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636067141990822272
   0.021615117161838747 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090369173963776
  Length = 50 rows


Queries return a limited number of rows controlled by ``Gaia.ROW_LIMIT``. To change the default behaviour set this appropriately.

.. doctest-remote-data::

  >>> Gaia.ROW_LIMIT = 8
  >>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> r.pprint(max_width=140)
           dist             solution_id     ...                                     datalink_url
                                            ...
  --------------------- ------------------- ... -----------------------------------------------------------------------------------
  0.0026034636994048854 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814214528
  0.0038518741347606357 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090339113063296
    0.00454542650096783 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814217600
   0.005613919443965546 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636089583198816640
   0.005846434715822121 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814218752
   0.006209042666371929 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814213632
   0.007469463683838576 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090339112308864
   0.008202004514524316 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636089583198816512

To return an unlimited number of rows set ``Gaia.ROW_LIMIT`` to -1.

.. doctest-remote-data::

  >>> Gaia.ROW_LIMIT = -1
  >>> r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> r.pprint(max_lines=12, max_width=140)
           dist             solution_id     ...                                     datalink_url
                                            ...
  --------------------- ------------------- ... -----------------------------------------------------------------------------------
  0.0026034636994048854 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814214528
  0.0038518741347606357 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090339113063296
    0.00454542650096783 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636090334814217600
                    ...                 ... ...                                                                                 ...
    0.05121063325107872 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636065840618481024
   0.051957226883925664 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6636093637644158592
    0.05320916763883812 1635721458409799680 ... https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR2+6633086847005369088
  Length = 176 rows


1.2. Cone search
~~~~~~~~~~~~~~~~

This query performs a cone search centered at the specified RA/Dec coordinates with the provided
radius argument.

.. doctest-remote-data::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.gaia import Gaia
  >>>
  >>> Gaia.ROW_LIMIT = 50  # Ensure the default row limit.
  >>> coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
  >>> radius = u.Quantity(1.0, u.deg)
  >>> j = Gaia.cone_search_async(coord, radius)
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> r = j.get_results()
  >>> r.pprint()
      solution_id             designation          ...          dist
                                                   ...
  ------------------- ---------------------------- ... ---------------------
  1635721458409799680 Gaia DR2 6636090334814214528 ... 0.0026034636994048854
  1635721458409799680 Gaia DR2 6636090339113063296 ... 0.0038518741347606357
  1635721458409799680 Gaia DR2 6636090334814217600 ...   0.00454542650096783
  1635721458409799680 Gaia DR2 6636089583198816640 ...  0.005613919443965546
  1635721458409799680 Gaia DR2 6636090334814218752 ...  0.005846434715822121
  1635721458409799680 Gaia DR2 6636090334814213632 ...  0.006209042666371929
  1635721458409799680 Gaia DR2 6636090339112308864 ...  0.007469463683838576
  1635721458409799680 Gaia DR2 6636089583198816512 ...  0.008202004514524316
  1635721458409799680 Gaia DR2 6636089583198817664 ...  0.008338509690874027
  1635721458409799680 Gaia DR2 6636089578899968384 ...  0.008406677772258921
                  ...                          ... ...                   ...

  1635721458409799680 Gaia DR2 6636089510180765312 ...   0.01943176697471851
  1635721458409799680 Gaia DR2 6636066871411763712 ...  0.019464719601172412
  1635721458409799680 Gaia DR2 6636089514475519232 ...  0.019467068628703368
  1635721458409799680 Gaia DR2 6636090407832546944 ...  0.019752561500226976
  1635721458409799680 Gaia DR2 6636066940132132352 ...   0.01991656886177004
  1635721458409799680 Gaia DR2 6636066871411763968 ...  0.020149589233310516
  1635721458409799680 Gaia DR2 6636089514478069888 ...  0.020307185970548904
  1635721458409799680 Gaia DR2 6636066940131244288 ...  0.020454730686780127
  1635721458409799680 Gaia DR2 6636067141990822272 ...  0.020802655215768254
  1635721458409799680 Gaia DR2 6636090369173963776 ...  0.021615117161838747
  Length = 50 rows


1.3. Getting public tables metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Table and columns metadata are specified by IVOA TAP_ recommendation
(to access to the actual data, an ADQL query must be executed).

.. _TAP: http://ivoa.info/documents/TAP/20100327/

To load only table names metadata (TAP+ capability):

.. doctest-remote-data::

  >>> from astroquery.gaia import Gaia
  >>> tables = Gaia.load_tables(only_names=True)
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  >>> for table in (tables):
  ...   print(table.get_qualified_name())
  external.external.apassdr9
  external.external.gaiadr2_astrophysical_parameters
  external.external.gaiadr2_geometric_distance
  external.external.gaiaedr3_distance
             ...
  tap_schema.tap_schema.keys
  tap_schema.tap_schema.schemas
  tap_schema.tap_schema.tables

To load all tables metadata (TAP compatible):

.. doctest-remote-data::

  >>> from astroquery.gaia import Gaia
  >>> tables = Gaia.load_tables()
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  >>> print(tables[0])
  TAP Table name: external.external.apassdr9
  Description: The AAVSO Photometric All-Sky Survey - Data Release 9
      This publication makes use of data products from the AAVSO
      Photometric All Sky Survey (APASS). Funded by the Robert Martin Ayers
      Sciences Fund and the National Science Foundation. Original catalogue released by Henden et al. 2015 AAS Meeting #225, id.336.16. Data retrieved using the VizieR catalogue access tool, CDS, Strasbourg, France. The original description of the VizieR service was published in A&AS 143, 23. VizieR catalogue II/336.
  Num. columns: 25


To load only a table (TAP+ capability):

.. doctest-remote-data::

  >>> from astroquery.gaia import Gaia
  >>> gaiadr2_table = Gaia.load_table('gaiadr2.gaia_source')
  Retrieving table 'gaiadr2.gaia_source'
  >>> print(gaiadr2_table)
  TAP Table name: gaiadr2.gaiadr2.gaia_source
  Description: This table has an entry for every Gaia observed source as listed in the
  Main Database accumulating catalogue version from which the catalogue
  release has been generated. It contains the basic source parameters,
  that is only final data (no epoch data) and no spectra (neither final
  nor epoch).
  Num. columns: 95


Once a table is loaded, its columns can be inspected:

.. doctest-remote-data::

  >>> for column in gaiadr2_table.columns:
  ...   print(column.name)
  solution_id
  designation
  source_id
  random_index
  ref_epoch
  ra
  ra_error
  dec
  dec_error
  parallax
  parallax_error
  parallax_over_error
  ...

1.4. Synchronous query
~~~~~~~~~~~~~~~~~~~~~~

The results of a synchronous query are stored at the user side (i.e., they are not saved in the
server). These queries must be used when the amount of data to be retrieved (number of rows)
is small, otherwise, a timeout error can be raised (an error created because the execution
time of the query exceeds time execution limit; see here archive_tips_ for details). The output
of the synchronous queries is limited to 2000 rows. If you need more than that, you must use
asynchronous queries.

.. _archive_tips: https://www.cosmos.esa.int/web/gaia/archive-tips

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.gaia import Gaia
  >>>
  >>> job = Gaia.launch_job("select top 100 "
  ...                       "solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al, "
  ...                       "matched_observations,duplicated_source,phot_variable_flag "
  ...                       "from gaiadr2.gaia_source order by source_id")
  >>> r = job.get_results()
  >>> print(r['ra_dec_corr'])
   ra_dec_corr
  -------------
    0.022670548
     0.06490505
     0.11690165
    0.042778816
    0.095711425
     0.56088775
  -0.0028029205
     0.11152559
      0.6039746
     0.06599529
            ...
      0.1803336
    0.089540906
     0.23512067
       0.066183
    -0.29090926
     0.21693705
      0.1531835
     0.14783339
     0.32718197
    -0.05562011
    0.008669683
  Length = 100 rows

Query saving results in a file (you may use 'output_format' to specified the results data format,
available formats are: 'votable', 'votable_plain', 'fits', 'csv' and 'json', default is 'votable'):

.. doctest-skip::

  >>> from astroquery.gaia import Gaia
  >>> job = Gaia.launch_job("select top 100 "
  ...                       "solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al, "
  ...                       "matched_observations,duplicated_source,phot_variable_flag "
  ...                       "from gaiadr2.gaia_source order by source_id",
  ...                       dump_to_file=True, output_format='votable')
  >>> print(job.outputFile)
  1592474300458O-result.vot.gz
  >>> r = job.get_results()
  >>> print(r['solution_id'])
    solution_id
  -------------------
  1635721458409799680
  1635721458409799680
  1635721458409799680
  1635721458409799680
  1635721458409799680
                ...
  Length = 100 rows

Note: you can inspect the status of the job by typing:

.. doctest-skip::

  >>> print(job)
  Jobid: None
  Phase: COMPLETED
  Owner: None
  Output file: 1592474300458O-result.vot.gz
  Results: None


1.5. Synchronous query on an 'on-the-fly' uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

You have to provide the local path to the file you want to upload. In the following example,
the file 'my_table.xml' is located to the relative location where your python program is
running. See note below.

.. doctest-skip::

  >>> from astroquery.gaia import Gaia
  >>> upload_resource = 'my_table.xml'
  >>> j = Gaia.launch_job(query="select * from tap_upload.table_test",
  ... upload_resource=upload_resource, upload_table_name="table_test", verbose=True)
  >>> r = j.get_results()
  >>> r.pprint()
  source_id alpha delta
  --------- ----- -----
          a   1.0   2.0
          b   3.0   4.0
          c   5.0   6.0

Note: to obtain the current location, type:

.. doctest-skip::

  >>> import os
  >>> print(os.getcwd())
  /Current/directory/path

1.6. Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side and depends on the user files quota.
These queries can be accessed at any time. For anonymous users, results are kept for three days.

Queries retrieved results can be stored locally in memory (by default) or in a file.

Query without saving results in a file:

.. doctest-remote-data::
  >>> from astroquery.gaia import Gaia
  >>> job = Gaia.launch_job_async("select top 100 designation,ra,dec "
  ...                             "from gaiadr2.gaia_source order by source_id")
  INFO: Query finished. [astroquery.utils.tap.core]
  >>> r = job.get_results()
  >>> print(r)
     designation               ra                 dec
                              deg                 deg
  ---------------------- ------------------ --------------------
     Gaia DR2 4295806720 44.996153684159594 0.005615806210679649
    Gaia DR2 34361129088 45.004316164207644 0.021045032689712983
    Gaia DR2 38655544960   45.0049742449841 0.019877000365797714
   Gaia DR2 309238066432  44.99503703932583  0.03815183599451371
                ...
  Length = 100 rows

Query saving results in a file (you may use 'output_format' to specified the results data format,
available formats are: 'votable', 'votable_plain', 'fits', 'csv' and 'json', default is 'votable'):

.. doctest-skip-all::

  >>> from astroquery.gaia import Gaia
  >>> job = Gaia.launch_job_async("select top 100 ra, dec "
  ...                             "from gaiadr2.gaia_source order by source_id",
  ...                             dump_to_file=True, output_format='votable')
  Saving results to: 1611860482314O-result.vot.gz
  >>> print(job)
  Jobid: 1611860482314O
  Phase: COMPLETED
  Owner: None
  Output file: 1611860482314O-result.vot.gz
  Results: None


1.7. Asynchronous job removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove asynchronous jobs::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.remove_jobs(["job_id_1","job_id_2",...])


---------------------------
2. Authenticated access
---------------------------

Authenticated users are able to access to TAP+ capabilities (shared tables, persistent jobs, etc.)
In order to authenticate a user, ``login`` or ``login_gui`` methods must be called. After a
successful login, the user will be authenticated until ``logout`` method is called.

All previous methods (``query_object``, ``cone_search``, ``load_table``, ``load_tables``, ``launch_job``) explained for
non authenticated users are applicable for authenticated ones.

The main differences are:

* Asynchronous results are kept at server side for ever (until the user decides to remove one of them).
* Users can access to shared tables.


2.1. Login/Logout
~~~~~~~~~~~~~~~~~

There are several ways to login to Gaia archive.

**Login through graphic interface**


*Note: Python Tkinter module is required to use login_gui method.*

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()


**Login through command line**


.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login(user='userName', password='userPassword')


**Login through a credentials file**

A file where the credentials are stored can be used to login:

*The file must containing user and password in two different lines.*

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login(credentials_file='my_credentials_file')


If you do not provide any parameters at all, a prompt will ask for the user name and password::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> User: user
  >>> Password: pwd (not visible)


To logout::

  >>> Gaia.logout()



2.2. Listing shared tables
~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Gaia archive user tables can be shared among user groups.

To obtain a list of the tables shared to a user type the following::

  >>> from astroquery.gaia import Gaia
  >>> tables = Gaia.load_tables(only_names=True, include_shared_tables=True)
  INFO: Retrieving tables... [astroquery.utils.tap.core]
  INFO: Parsing tables... [astroquery.utils.tap.core]
  INFO: Done. [astroquery.utils.tap.core]
  >>> for table in (tables):
  ...   print(table.get_qualified_name())
  external.external.apassdr9
  external.external.gaiadr2_geometric_distance
  external.external.gaiaedr3_distance
  external.external.galex_ais
    ...     ...       ...
  gaiadr2.gaiadr2.vari_time_series_statistics
  gaiadr2.gaiadr2.panstarrs1_original_valid
  gaiadr2.gaiadr2.gaia_source
  gaiadr2.gaiadr2.ruwe

2.3. Uploading table to user space
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is now possible to store a table in the private user space. The table to be uploaded can
be in a VOTable_ located in a given URL, a table stored in a local file in the user machine,
a pre-computed Astropy table file or a job executed in the Gaia archive.

.. _VOTable: http://www.ivoa.net/documents/VOTable/

Each user has a database schema described as: 'user_<user_login_name>'. For instance, if a
login name is 'joe', the database schema is 'user_joe'. Your uploaded table can be
referenced as 'user_joe.table_name'


2.3.1. Uploading table from URL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An already generated VOTable, accessible through a URL, can be uploaded to Gaia archive.

The following example launches a query to Vizier TAP ('url' parameter). The result is a
VOTable that can be uploaded to the user private area.

Your schema name will be automatically added to the provided table name::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> # Provide a URL pointing to valid VOTable resource
  >>> url = ("http://tapvizier.u-strasbg.fr/TAPVizieR/tap/sync/?"
  ...        "REQUEST=doQuery&lang=ADQL&FORMAT=votable&"
  ...        "QUERY=select+*+from+TAP_SCHEMA.columns+where+table_name='II/336/apass9'")
  >>> job = Gaia.upload_table(upload_resource=url, table_name="table_test_from_url",
  ... table_description="Some description")
  Job '1539932326689O' created to upload table 'table_test_from_url'.

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user_<your_login_name>.<table_name>*)::

  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_url'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_results()


2.3.2. Uploading table from file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A file containing a table (votable, fits or csv) can be uploaded to the user private area.

The parameter 'format' must be provided when the input file is not a votable file.

Your schema name will be automatically added to the provided table name.

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> job = Gaia.upload_table(upload_resource="1535553556177O-result.vot",
  ...                         table_name="table_test_from_file", format="VOTable")

  Sending file: 1535553556177O-result.vot
  Uploaded table 'table_test_from_file'.

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user_<your_login_name>.<table_name>*)::

  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_file'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_results()


2.3.3. Uploading table from an astropy Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A in memory PyTable (See https://wiki.python.org/moin/PyTables) can be uploaded to the user private area.

Your schema name will be automatically added to the provided table name.

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> from astropy.table import Table
  >>> a=[1,2,3]
  >>> b=['a','b','c']
  >>> table = Table([a,b], names=['col1','col2'], meta={'meta':'first table'})
  >>> # Upload
  >>> Gaia.login()
  >>> Gaia.upload_table(upload_resource=table, table_name='table_test_from_astropy')


Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user_<your_login_name>.<table_name>*)::

  >>> full_qualified_table_name = 'user_<your_login_name>.table_test_from_astropy'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_results()



2.3.4. Uploading table from job
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The results generated by an *asynchronous* job (from a query executed in the Gaia archive) can be
ingested in a table in the user private area.

The following example generates a job in the Gaia archive and then, the results are ingested in a
table named: user_<your_login_name>.'t'<job_id>::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> j1 = Gaia.launch_job_async("select top 10 * from gaiadr2.gaia_source")
  >>> job = Gaia.upload_table_from_job(j1)
  Created table 't1539932994481O' from job: '1539932994481O'.

Now, you can query your table as follows (a full qualified table name must be provided,
i.e.: *user_<your_login_name>.t<job_id>*)::

  >>> full_qualified_table_name = 'user_<your_login_name>.t1539932994481O'
  >>> query = 'select * from ' + full_qualified_table_name
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_results()

2.4. Deleting table
~~~~~~~~~~~~~~~~~~~

A table from the user private area can be deleted as follows::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()
  >>> job = Gaia.delete_user_table("table_test_from_file")
  Table 'table_test_from_file' deleted.


2.5. Updating table metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It can be useful for the user to modify the metadata of a given table. For example, a user
might want to change the description (UCD) of a column, or the flags that give extra information
about certain column. This is possible using::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()
  >>> Gaia.update_user_table(table_name, list_of_changes)

where the list of changes is a list of 3 items:

["column name to be changed", "metadata parameter to be changed", "new value"]

The metadata parameter to be changed can be 'utype', 'ucd', 'flags' or 'indexed':

* values for 'utype' and 'ucd' are free text. See VOTable_ specification (sections UType and UCD), UCD_ specification and UTypes_ usage.

* value for 'flags' can be 'Ra', 'Dec', 'Mag', 'Flux' and 'PK'.

* value for 'indexed' is a boolean indicating whether the column is indexed or not.

.. _UCD: http://www.ivoa.net/documents/latest/UCD.html
.. _UTypes: http://www.ivoa.net/documents/Notes/UTypesUsage/index.html

For instance, the 'ra' column in the gaiadr2.gaia_source catalogue is specified as::

  Utype: Char.SpatialAxis.Coverage.Location.Coord.Position2D.Value2.C1
  Ucd: pos.eq.ra;meta.main

and the 'dec' column as::

  Utype: Char.SpatialAxis.Coverage.Location.Coord.Position2D.Value2.C2
  Ucd: pos.eq.dec;meta.main

It is possible to apply multiple changes at once.
This is done by putting each of the changes in a list. See example below.

In this case, we have a table (user_joe.table), with several columns: 'recno', 'nobs',
'raj2000' and 'dej2000'.

We want to set:

* 'ucd' of 'recno' column to 'ucd sample'
* 'utype' of 'nobs' column to 'utype sample'
* 'flags' of 'raj2000' column to 'Ra'
* 'flags' of 'dej2000' column to 'Dec'

We can type the following::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login_gui()
  >>> Gaia.update_user_table(table_name="user_joe.table",
  ...                        list_of_changes=[["recno", "ucd", "ucd sample"],
  ...                                         ["nobs","utype","utype sample"],
  ...                                         ["raj2000","flags","Ra"],
  ...                                         ["dej2000","flags","Dec"]])
  Retrieving table 'user_joe.table'
  Parsing table 'user_joe.table'...
  Done.
  Table 'user_joe.table' updated.

2.6. Cross match
~~~~~~~~~~~~~~~~

It is possible to run a geometric cross-match between the RA/Dec coordinates of two tables
using the crossmatch function provided by the archive. In order to do so the user must be
logged in. This is required because the cross match operation will generate a join table
in the user private area. That table contains the identifiers of both tables and the separation,
in degrees, between RA/Dec coordinates of each source in the first table and its associated
source in the second table. Later, the table can be used to obtain the actual data from both tables.

In order to perform a cross match, both tables must have defined RA and Dec columns
(Ra/Dec column flags must be set: see previous section to know how to assign those flags).

The following example uploads a table and then, the table is used in a cross match::

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> table = file or astropy.table
  >>> Gaia.upload_table(upload_resource=table, table_name='my_sources')
  >>> # the table will be uploaded into the user private space into the database
  >>> # the table can be referenced as <database user schema>.<table_name>
  >>> full_qualified_table_name = 'user_<your_login_name>.my_sources'
  >>> xmatch_table_name = 'xmatch_table'
  >>> Gaia.cross_match(full_qualified_table_name_a=full_qualified_table_name,
  ...                  full_qualified_table_name_b='gaiadr2.gaia_source',
  ...                  results_table_name=xmatch_table_name, radius=1.0)


Once you have your cross match finished, you can obtain the results::

  >>> xmatch_table = 'user_<your_login_name>.' + xmatch_table_name
  >>> query = ('SELECT c."dist"*3600 as dist, a.*, b.* FROM gaiadr2.gaia_source AS a, '
  ...          'full_qualified_table_name+' AS b, '
  ...          'xmatch_table+' AS c '
  ...          'WHERE (c.gaia_source_source_id = a.source_id AND '
  ...          'c.my_sources_my_sources_oid = b.my_sources_oid)'
  >>> job = Gaia.launch_job(query=query)
  >>> results = job.get_results()

Cross-matching catalogues is one of the most popular operations executed in the Gaia archive.
For more details about how to run different cross-matches we direct the reader to: https://gea.esac.esa.int/archive-help/tutorials/crossmatch/index.html

2.7. Tables sharing
~~~~~~~~~~~~~~~~~~~

It is possible to share tables with other users. You have to create a group, populate that
group with users, and share your table to that group. Then, any user belonging to that group
will be able to access to your shared table in a query.

2.7.1. Creating a group
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_create(group_name="my_group", description="description")

2.7.2. Removing a group
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_delete(group_name="my_group")

2.7.3. Listing groups
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> groups = Gaia.load_groups()
  >>> for group in groups:
  ...     print(group.title)

2.7.4. Adding users to a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_add_user(group_name="my_group",user_id="<user_login_name")

2.7.5. Removing users from a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_group_delete_user(group_name="my_group",user_id="<user_login_name>")


2.7.6. Sharing a table to a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_table(group_name="my_group",
  ...                  table_name="user_<user_login_name>.my_table",
  ...                  description="description")


2.7.7. Stop sharing a table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  >>> from astroquery.gaia import Gaia
  >>> Gaia.login()
  >>> Gaia.share_table_stop(table_name="user_<user_login_name>.my_table", group_name="my_group")


Reference/API
=============

.. automodapi:: astroquery.gaia
    :no-inheritance-diagram:
