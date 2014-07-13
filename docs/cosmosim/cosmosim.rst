.. _astroquery.cosmosim:

************************************
CosmoSim Queries (`astroquery.cosmosim`)
************************************

Getting started
===============

This module allows the user to query and download from one of three 
cosmological simulation projects (the MultiDark project, the BolshoiP project, 
and the CLUES project). For accessing such data a CosmoSim object must 
first be instantiated with valid credentials (no public username/password 
are implemented). Below are a couple of example queries. 

.. code-block:: python

    >>> from astroquery.cosmosim import CosmoSim
    >>> CS = CosmoSim()
    >>> CS.login(username="uname",password="pword") 
    >>> # Enter your credentials in here; caching is enabled, so after
    >>> # the initial successful login no further password is required
    >>> CS.run


Exploring Database Schema
==================



Downloading data
================

 



Reference/API
=============

.. automodapi:: astroquery.cosmosim
    :no-inheritance-diagram:
