.. _astroquery.cosmosim:

************************************
CosmoSim Queries (`astroquery.cosmosim`)
************************************

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
    >>> CS.login(username="uname",password="pword") 
    Authenticating uname on www.cosmosim.org...
    Authentication successful!
    >>> sql_query = "SELECT 0.25*(0.5+FLOOR(LOG10(Mvir)/0.25)) AS
    log_mass, COUNT(*) AS num FROM MDR1.FOF WHERE snapnum=85 GROUP BY
    FLOOR(LOG10(Mvir)/0.25) ORDER BY log_mass" # MDR1.BDMV mass function
    >>> CS.run_sql_query(query_string=sql_query)
    Job created: 359748449665484 #jobid; note: will be different 

Managing CosmoSim Queries
===============

The cosmosim module provides functionality for checking the completion status
of queries, in addition to deleting them from the server. Below are a
few examples functions available to the user for these purposes. 

.. code-block:: python

    >>> CS.check_all_jobs()
    {'359748449665484': 'COMPLETED'}
    >>> CS.delete_job(jobid='359748449665484')
    Deleted job: 359748449665484
    >>> CS.check_all_jobs() 
    {}

.. code-block:: python

    >>> CS.check_all_jobs()
    {'359748449665484': 'ABORTED', '359748586913123': 'COMPLETED'}
    >>> CS.delete_all_jobs()
    Deleted job: 359748449665484
    Deleted job: 359748586913123
    >>> CS.check_all_jobs()
    {}


Exploring Database Schema
==================



Downloading data
================

 



Reference/API
=============

.. automodapi:: astroquery.cosmosim
    :no-inheritance-diagram:
