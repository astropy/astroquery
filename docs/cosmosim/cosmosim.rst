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
    >>> CS.login(username="uname",password="pword") 
    >>> # Enter your credentials in here; caching is enabled, so after
    >>> # the initial successful login no further password is required
    >>> sql_query = "SELECT 0.25*(0.5+FLOOR(LOG10(Mvir)/0.25)) AS
    log_mass, COUNT(*) AS num FROM MDR1.FOF WHERE snapnum=85 GROUP BY
    FLOOR(LOG10(Mvir)/0.25) ORDER BY log_mass" # MDR1.BDMV mass function
    >>> CS.run_sql_query(query_string=sql_query)


Exploring Database Schema
==================



Downloading data
================

 



Reference/API
=============

.. automodapi:: astroquery.cosmosim
    :no-inheritance-diagram:
