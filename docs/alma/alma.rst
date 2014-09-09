.. doctest-skip-all

.. _astroquery.alma:

********************************
ALMA Queries (`astroquery.alma`)
********************************

Getting started
===============

`astroquery.alma` provides the astroquery interface to the ALMA archive.  It
supports object and region based querying and data staging and retrieval.


Authentication
==============

Users can log in to acquire proprietary data products.  Login is performed
via the ALMA CAS (central authentication server).

.. code-block:: python

    >>> from astroquery.alma import Alma
    >>> alma = Alma()
    >>> alma("TEST") # doctest: +SKIP
    TEST, enter your ALMA password:

    Authenticating TEST on asa.alma.cl...
    Authentication failed!
    >>> alma.login("ICONDOR") # doctest: +SKIP
    ICONDOR, enter your ESO password:

    Authenticating ICONDOR on asa.alma.cl...
    Authentication successful!
    >>> alma.login("ICONDOR") # doctest: +SKIP
    Authenticating ICONDOR on asa.alma.cl...
    Authentication successful!


