.. _astroquery.cosmosim:

****************************************
CosmoSim Queries (`astroquery.cosmosim`)
****************************************

This module allows the user to query and download from one of three 
cosmological simulation projects: the MultiDark project, the BolshoiP project, 
and the CLUES project. For accessing these databases a CosmoSim object must 
first be instantiated with valid credentials (no public username/password 
are implemented). Below are a couple of examples of usage. 

Getting started
===============


.. code-block:: python

    >>> from astroquery.cosmosim import CosmoSim
    >>> CS = CosmoSim()
    >>> # Next, enter your credentials; caching is enabled, so after
    >>> # the initial successful login no further password is required.
    >>> CS.login(username="public") # doctest: +SKIP 
    uname, enter your CosmoSim password:

    Authenticating uname on www.cosmosim.org...
    Authentication successful!
    >>> # MDR1.BDMV mass function 
    >>> sql_query = "SELECT 0.25*(0.5+FLOOR(LOG10(Mvir)/0.25)) AS log_mass, COUNT(*) AS num FROM MDR1.FOF WHERE snapnum=85 GROUP BY FLOOR(LOG10(Mvir)/0.25) ORDER BY log_mass" # doctest: +SKIP 
    >>> CS.run_sql_query(query_string=sql_query) # doctest: +SKIP 
    Job created: 359748449665484 #jobid; note: is unique to each and
    every query

Managing CosmoSim Queries
=========================

The cosmosim module provides functionality for checking the completion status
of queries, in addition to deleting them from the server. Below are a
few examples functions available to the user for these purposes. 

.. code-block:: python

    >>> CS.check_all_jobs() # doctest: +SKIP 
    {'359748449665484': 'COMPLETED'}
    >>> CS.delete_job(jobid='359748449665484') # doctest: +SKIP 
    Deleted job: 359748449665484
    >>> CS.check_all_jobs() # doctest: +SKIP 
    {}

.. code-block:: python

    >>> CS.check_all_jobs() # doctest: +SKIP 
    {'359748449665484': 'ABORTED', '359748586913123': 'COMPLETED'}
    >>> CS.delete_all_jobs() # doctest: +SKIP 
    Deleted job: 359748449665484
    Deleted job: 359748586913123
    >>> CS.check_all_jobs() # doctest: +SKIP 
    {}


Exploring Database Schema
=========================

A database exploration tool is available to help the user navigate
the structure of any simulation database in the CosmoSim database. 


Legend

'@'  :   type == dict

'$'   :   type != dict

.. code-block:: python

    >>> CS.explore_db(db='MDPL') # doctest: +SKIP 
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

    >>> CS.explore_db(db='MDPL',table='AvailHalos') # doctest: +SKIP 
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

    >>> CS.explore_db(db='MDPL',table='AvailHalos',col='redshift') # doctest: +SKIP    
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

 



Reference/API
=============

.. automodapi:: astroquery.cosmosim
    :no-inheritance-diagram:
