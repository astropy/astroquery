.. doctest-skip-all

.. _astroquery.cosmosim:

****************************************
CosmoSim Queries (`astroquery.cosmosim`)
****************************************

This module allows the user to query and download from one of three 
cosmological simulation projects: the MultiDark project, the BolshoiP project, 
and the CLUES project. For accessing these databases a CosmoSim object must 
first be instantiated with valid credentials (no public username/password 
are implemented). Below are a couple of examples of usage. 

Requirements
============

The following packages are required for the use of this module:

* requests
* keyring
* getpass
* bs4


Getting started
===============


.. code-block:: python

    >>> from astroquery.cosmosim import CosmoSim
    >>> CS = CosmoSim()
    >>> # Next, enter your credentials; caching is enabled, so after
    >>> # the initial successful login no further password is required.
    >>> CS.login(username="uname") 
    uname, enter your CosmoSim password:

    Authenticating uname on www.cosmosim.org...
    Authentication successful!
    >>> # It also knows if you are running from a script. To login
    >>> # from a script (rather than an interactive python session): 
    >>> # CS.login(username="uname",password="password")
    >>> # MDR1.BDMV mass function 
    >>> sql_query = "SELECT 0.25*(0.5+FLOOR(LOG10(mass)/0.25)) AS log_mass, COUNT(*) AS num FROM MDR1.FOF WHERE snapnum=85 GROUP BY FLOOR(LOG10(mass)/0.25) ORDER BY log_mass" 
    >>> CS.run_sql_query(query_string=sql_query) 
    Job created: 359748449665484 #jobid; note: is unique to each and
    every query

Managing CosmoSim Queries
=========================

The cosmosim module provides functionality for checking the completion status
of queries, in addition to deleting them from the server. Below are a
few examples of functions available to the user for these purposes. 

.. code-block:: python

    >>> CS.check_all_jobs() 
    {'359748449665484': 'COMPLETED'}
    >>> CS.delete_job(jobid='359748449665484') 
    Deleted job: 359748449665484
    >>> CS.check_all_jobs() 
    {}

The above function 'check_all_jobs' also supports the usage of a
job's phase status in order to filter through all available CosmoSim
jobs. 

.. code-block:: python

    >>> CS.check_all_jobs()
    {'359748449665484': 'COMPLETED'}
    {'359748449682647': 'ABORTED'}
    {'359748449628375': 'ERROR'} 
    >>> CS.check_all_jobs(phase=['Completed','Aborted']) 
    {'359748449665484': 'COMPLETED'}
    {'359748449682647': 'ABORTED'}

Additionally, 'delete_all_jobs' accepts both phase and/or tablename
(via a regular expression) as criteria for deletion of all available
CosmoSim jobs. But be careful: Leaving both arguments blank will
delete ALL jobs!

.. code-block:: python

    >>> CS.check_all_jobs()
    {'359748449665484': 'COMPLETED'}
    {'359748449682647': 'ABORTED'}
    {'359748449628375': 'ERROR'} 
    >>> CS.table_dict()
    {'359748449665484': '2014-09-07T05:01:40:0458'}
    {'359748449682647': 'table2'}
    {'359748449628375': 'table3'} 
    >>>
    CS.delete_all_jobs(phase=['Aborted','error'],regex='[a-z]*[0-9]*')
    # phases are case insensitive
    Deleted job: 359748449682647 (Table: table2)
    Deleted job: 359748449628375 (Table: table3)
    >>> CS.check_all_jobs() 
    {'359748449665484': 'COMPLETED'}

Getting rid of this last job can be done by deleting all jobs with
phase COMPLETED, or it can be done simply by providing the 'delete_job'
function with its unique jobid. Lastly, this could be accomplished by
matching its tablename to the following regular expression:
'[0-9]*-[0-9]*-[0-9]*[A-Z]*[0-9]*:[0-9]*:[0-9]*:[0-9]*'.  All jobs
created without specifying the tablename argument in 'run_sql_query'
are automatically assigned one based upon the creation date and time
of the job, and is therefore the default tablename format.

Deleting all jobs, regardless of tablename, and job phase:

.. code-block:: python

    >>> CS.check_all_jobs() 
    {'359748449665484': 'ABORTED', '359748586913123': 'COMPLETED'}
    >>> CS.delete_all_jobs() 
    Deleted job: 359748449665484
    Deleted job: 359748586913123
    >>> CS.check_all_jobs() 
    {}


Exploring Database Schema
=========================

A database exploration tool is available to help the user navigate
the structure of any simulation database in the CosmoSim database. 


Legend

'@'  :   type == dict

'$'   :   type != dict

.. code-block:: python

    >>> CS.explore_db(db='MDPL') 
    ########
    # MDPL #
    ########
    @ tables
       --> FOF5
       --> FOF4
       --> FOF3
       --> FOF2
       --> FOF1
       --> Particles88
       --> FOF
       --> LinkLength
       --> BDMW
       --> AvailHalos
       --> Redshifts
       --> Particles42
    $ id
       --> 114
    $ description
       --> The MDR1-Planck simulation.
 
.. code-block:: python

    >>> CS.explore_db(db='MDPL',table='AvailHalos') 
    ########
    # MDPL #
    ########
    @ tables
       @ AvailHalos
          $ id
             --> 932
          @ columns
             --> FOF5
             --> FOF4
             --> FOF3
             --> FOF2
             --> FOF1
             --> redshift
             --> BDM
             --> FOF
             --> snapnum
          $ description
             --> 

.. code-block:: python

    >>> CS.explore_db(db='MDPL',table='AvailHalos',col='redshift') 
    ########
    # MDPL #
    ########
    @ tables
       @ AvailHalos
          @ columns
             @ redshift
                --> id:21613
                --> description:
    
Downloading data
================

Query results can be downloaded and used in real-time from the command
line, or alternatively they can be stored on your local machine.
 
.. code-block:: python

    >>> CS.check_all_jobs() 
    {'359750704009965': 'COMPLETED'}
    >>> data = CS.download(jobid='359750704009965')
    [<Response [200]>]
    >>> print(data)
    (['row_id', 'log_mass', 'num'],
     [[1, 10.88, 3683],
      [2, 11.12, 452606],
      [3, 11.38, 3024674],
      [4, 11.62, 3828931],
      [5, 11.88, 2638644],
      [6, 12.12, 1572685],
      [7, 12.38, 926764],
      [8, 12.62, 544650],
      [9, 12.88, 312360],
      [10, 13.12, 174164],
      [11, 13.38, 95263],
      [12, 13.62, 50473],
      [13, 13.88, 25157],
      [14, 14.12, 11623],
      [15, 14.38, 4769],
      [16, 14.62, 1672],
      [17, 14.88, 458],
      [18, 15.12, 68],
      [19, 15.38, 4]])

.. code-block:: python

    >>> CS.download(jobid='359750704009965',filename='/Users/username/Desktop/MDR1massfunction.dat')
    [<Response [200]>]
    Data written to file: /Users/username/Desktop/MDR1massfunction.dat   
    (['row_id', 'log_mass', 'num'],
     [[1, 10.88, 3683],
      [2, 11.12, 452606],
      [3, 11.38, 3024674],
      [4, 11.62, 3828931],
      [5, 11.88, 2638644],
      [6, 12.12, 1572685],
      [7, 12.38, 926764],
      [8, 12.62, 544650],
      [9, 12.88, 312360],
      [10, 13.12, 174164],
      [11, 13.38, 95263],
      [12, 13.62, 50473],
      [13, 13.88, 25157],
      [14, 14.12, 11623],
      [15, 14.38, 4769],
      [16, 14.62, 1672],
      [17, 14.88, 458],
      [18, 15.12, 68],
      [19, 15.38, 4]]) 

Data can be stored and/or written out as a `VOTable`_.

.. _VOTable: http://astropy.readthedocs.org/en/latest/io/votable/

.. code-block:: python

    >>> data = CS.download(jobid='359750704009965',format='votable')
    [<Response [200]>]
    >>> data
    <astropy.io.votable.tree.VOTableFile at 0x10b440150>
    >>> data.to_xml('/Users/username/Desktop/data.xml')
    >>> CS.download(jobid='359750704009965',filename='/Users/username/Desktop/MDR1massfunction.dat')
    [<Response [200]>]
    Data written to file: /Users/username/Desktop/MDR1massfunction.dat   
    (['row_id', 'log_mass', 'num'],
     [[1, 10.88, 3683],
      [2, 11.12, 452606],
      [3, 11.38, 3024674],
      [4, 11.62, 3828931],
      [5, 11.88, 2638644],
      [6, 12.12, 1572685],
      [7, 12.38, 926764],
      [8, 12.62, 544650],
      [9, 12.88, 312360],
      [10, 13.12, 174164],
      [11, 13.38, 95263],
      [12, 13.62, 50473],
      [13, 13.88, 25157],
      [14, 14.12, 11623],
      [15, 14.38, 4769],
      [16, 14.62, 1672],
      [17, 14.88, 458],
      [18, 15.12, 68],
      [19, 15.38, 4]]) 

Reference/API
=============

.. automodapi:: astroquery.cosmosim
		:no-inheritance-diagram:
