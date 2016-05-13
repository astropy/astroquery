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

Next, enter your credentials; caching is enabled, so after the initial
successful login no further password is required if desired.

    >>> CS.login(username="uname") 
    uname, enter your CosmoSim password:
    Authenticating uname on www.cosmosim.org...
    Authentication successful!
    >>> # If running from a script (rather than an interactive python session): 
    >>> # CS.login(username="uname",password="password")
    
To store the password associated with your username in the keychain: 

    >>> CS.login(username="uname",store_password=True)
    WARNING: No password was found in the keychain for the provided username. [astroquery.cosmosim.core]
    uname, enter your CosmoSim password:
    Authenticating uname on www.cosmosim.org...
    Authentication successful!

Logging out is as simple as:

    >>> CS.logout(deletepw=True)
    Removed password for uname in the keychain.

The deletepw option will undo the storage of any password in the
keychain. Checking whether you are successfully logged in (or who is
currently logged in):

    >>> CS.check_login_status()
    Status: You are logged in as uname.

Below is an example of running an SQL query (BDMV mass function of the
MDR1 cosmological simulation at a redshift of z=0):

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
         JobID        Phase  
    --------------- ---------
    359748449665484 COMPLETED
    >>> CS.delete_job(jobid='359748449665484') 
    Deleted job: 359748449665484
    >>> CS.check_all_jobs()
         JobID        Phase  
    --------------- ---------

The above function 'check_all_jobs' also supports the usage of a
job's phase status in order to filter through all available CosmoSim
jobs. 

.. code-block:: python

    >>> CS.check_all_jobs()
         JobID        Phase  
    --------------- ---------
    359748449665484 COMPLETED
    359748449682647 ABORTED
    359748449628375 ERROR
    >>> CS.check_all_jobs(phase=['Completed','Aborted']) 
         JobID        Phase  
    --------------- ---------
    359748449665484 COMPLETED
    359748449682647 ABORTED

Additionally, 'check_all_jobs' (and 'delete_all_jobs') accepts both
phase and/or tablename (via a regular expression) as criteria for
deletion of all available CosmoSim jobs. But be careful: Leaving both
arguments blank will delete ALL jobs!

.. code-block:: python

    >>> CS.check_all_jobs()
         JobID        Phase  
    --------------- ---------
    359748449665484 COMPLETED
    359748449682647 ABORTED
    359748449628375 ERROR
    >>> CS.table_dict()
    {'359748449665484': '2014-09-07T05:01:40:0458'}
    {'359748449682647': 'table2'}
    {'359748449628375': 'table3'} 
    >>> CS.delete_all_jobs(phase=['Aborted','error'],regex='[a-z]*[0-9]*')
    Deleted job: 359748449682647 (Table: table2)
    Deleted job: 359748449628375 (Table: table3)

Note: Arguments for phase are case insensitive. Now, check to see if
the jobs have been deleted:

    >>> CS.check_all_jobs() 
         JobID        Phase  
    --------------- ---------
    359748449665484 COMPLETED

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
         JobID        Phase  
    --------------- ---------
    359748449665484 ABORTED
    359748586913123 COMPLETED
 
    >>> CS.delete_all_jobs() 
    Deleted job: 359748449665484
    Deleted job: 359748586913123
    >>> CS.check_all_jobs() 
         JobID        Phase  
    --------------- ---------

In addition to the phase and regex arguments for 'check_all_jobs',
selected jobs can be sorted using two properties:

    >>> CS.check_all_jobs(phase=['completed'],regex='[a-z]*[0-9]*',sortby='tablename')
         JobID        Phase   Tablename         Starttime        
    --------------- --------- --------- -------------------------
    361298054830707 COMPLETED    table1 2014-09-21T19:28:48+02:00
    361298050841687 COMPLETED    table2 2014-09-21T19:20:23+02:00

    >>> CS.check_all_jobs(phase=['completed'],regex='[a-z]*[0-9]*',sortby='starttime')
         JobID        Phase   Tablename         Starttime        
    --------------- --------- --------- -------------------------
    361298050841687 COMPLETED    table2 2014-09-21T19:20:23+02:00
    361298054830707 COMPLETED    table1 2014-09-21T19:28:48+02:00


Exploring Database Schema
=========================

A database exploration tool is available to help the user navigate
the structure of any simulation database in the CosmoSim database. 

Note: '@' precedes entries which are dictionaries

.. code-block:: python

    >>> CS.explore_db()
    Must first specify a database.
            Projects         Project Items                                      Information                                      
    ------------------------ ------------- --------------------------------------------------------------------------------------
                   @ Bolshoi      @ tables                                                                                       
                                       id:                                                                                      2
                              description:                                                                  The Bolshoi Database.
    ------------------------ ------------- --------------------------------------------------------------------------------------
                  @ BolshoiP      @ tables                                                                                       
                                       id:                                                                                    119
                              description:                                                              Bolshoi Planck simulation
    ------------------------ ------------- --------------------------------------------------------------------------------------
               @ Clues3_LGDM      @ tables                                                                                       
                                       id:                                                                                    134
                              description: CLUES simulation, B64, 186592, WMAP3, Local Group resimulation, 4096, Dark Matter only
    ------------------------ ------------- --------------------------------------------------------------------------------------
              @ Clues3_LGGas      @ tables                                                                                       
                                       id:                                                                                    124
                              description:          CLUES simulation, B64, 186592, WMAP3, Local Group resimulation, 4096, Gas+SFR
    ------------------------ ------------- --------------------------------------------------------------------------------------
                      @ MDPL      @ tables                                                                                       
                                       id:                                                                                    114
                              description:                                                            The MDR1-Planck simulation.
    ------------------------ ------------- --------------------------------------------------------------------------------------
                      @ MDR1      @ tables                                                                                       
                                       id:                                                                                      7
                              description:                                                        The MultiDark Run 1 Simulation.
    ------------------------ ------------- --------------------------------------------------------------------------------------
    @ cosmosim_user_username      @ tables                                                                                       
                                       id:                                                                                 userdb
                              description:                                                                 Your personal database
    ------------------------ ------------- --------------------------------------------------------------------------------------

.. code-block:: python

    >>> CS.explore_db(db='MDPL')
      Projects  Project Items     Tables   
    ----------- ------------- -------------
    --> @ MDPL: --> @ tables:         @ FOF
                           id        @ FOF5
                  description        @ FOF4
                                     @ FOF3
                                     @ FOF2
                                     @ FOF1
                                     @ BDMW
                                @ Redshifts
                               @ LinkLength
                               @ AvailHalos
                              @ Particles88 

.. code-block:: python

    >>> CS.explore_db(db='MDPL',table='FOF')
      Projects  Project Items     Tables    Table Items  Table Info Columns 
    ----------- ------------- ------------- ------------ ---------- --------
    --> @ MDPL: --> @ tables:    --> @ FOF:          id:        934        y
                           id        @ FOF5    @ columns                   x
                  description        @ FOF4 description:                   z
                                     @ FOF3                               ix
                                     @ FOF2                               iz
                                     @ FOF1                               vx
                                     @ BDMW                               vy
                                @ Redshifts                               vz
                               @ LinkLength                               iy
                               @ AvailHalos                               np
                              @ Particles88                             disp
                                                                        size
                                                                        spin
                                                                        mass
                                                                       axis1
                                                                       axis2
                                                                       axis3
                                                                       fofId
                                                                       phkey
                                                                       delta
                                                                       level
                                                                      angMom
                                                                      disp_v
                                                                     axis1_z
                                                                     axis1_x
                                                                     axis1_y
                                                                     axis3_x
                                                                     axis3_y
                                                                     axis3_z
                                                                     axis2_y
                                                                     axis2_x
                                                                     NInFile
                                                                     axis2_z
                                                                     snapnum
                                                                    angMom_x
                                                                    angMom_y
                                                                    angMom_z    

.. code-block:: python

    >>> CS.explore_db(db='MDPL',table='FOF',col='fofId')
      Projects  Project Items     Tables     Table Items     Columns   
    ----------- ------------- ------------- -------------- ------------
    --> @ MDPL: --> @ tables:    --> @ FOF: --> @ columns: --> @ fofId:
                           id        @ FOF5             id       @ disp
                  description        @ FOF4    description    @ axis1_z
                                     @ FOF3                   @ axis1_x
                                     @ FOF2                   @ axis1_y
                                     @ FOF1                        @ ix
                                     @ BDMW                        @ iz
                                @ Redshifts                   @ axis3_x
                               @ LinkLength                   @ axis3_y
                               @ AvailHalos                   @ axis3_z
                              @ Particles88                        @ vx
                                                                   @ vy
                                                                   @ vz
                                                              @ axis2_y
                                                              @ axis2_x
                                                                 @ size
                                                                @ axis1
                                                                @ axis2
                                                                @ axis3
                                                                   @ iy
                                                               @ angMom
                                                              @ NInFile
                                                                   @ np
                                                              @ axis2_z
                                                               @ disp_v
                                                                @ phkey
                                                                @ delta
                                                              @ snapnum
                                                                 @ spin
                                                                @ level
                                                             @ angMom_x
                                                             @ angMom_y
                                                             @ angMom_z
                                                                 @ mass
                                                                    @ y
                                                                    @ x
                                                                    @ z


Downloading data
================

Query results can be downloaded and used in real-time from the command
line, or alternatively they can be stored on your local machine.
 
.. code-block:: python

    >>> CS.check_all_jobs() 
         JobID        Phase  
    --------------- ---------
    359750704009965 COMPLETED

    >>> data = CS.download(jobid='359750704009965',format='csv')
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

Unless the filename attribute is specified, data is not saved out to
file.

    >>> data = CS.download(jobid='359750704009965',filename='/Users/uname/Desktop/test.csv',format='csv')
    |==========================================================================================================================| 1.5k/1.5k (100.00%)         0s

Other formats include votable, votableb1, and votableb2 (the latter
two are binary files, for easier handling of large data sets; these
formats can not be used in an interactive python session). 

Data can be stored and/or written out as a `VOTable`_.

.. _VOTable: http://astropy.readthedocs.io/en/latest/io/votable/

.. code-block:: python

    >>> data = CS.download(jobid='359750704009965',format='votable')
    >>> data
    <astropy.io.votable.tree.VOTableFile at 0x10b440150>
    >>> data = CS.download(jobid='359750704009965',filename='/Users/uname/Desktop/test.xml',format='votable')
    >>> |==========================================================================================================================| 4.9k/4.9k (100.00%)         0s


Reference/API
=============

.. automodapi:: astroquery.cosmosim
		:no-inheritance-diagram:
