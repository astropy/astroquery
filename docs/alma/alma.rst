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

Querying Targets and Regions
============================

You can query by object name or by circular region:

.. code-block:: python

    >>> from astroquery.alma import Alma
    >>> m83_data = Alma.query_object('M83')
    >>> print(len(m83_data))
    225
    >>> m83_data.colnames
    ['Project_code', 'Source_name', 'RA', 'Dec', 'Band',
    'Frequency_resolution', 'Integration', 'Release_date', 'Frequency_support',
    'Velocity_resolution', 'Pol_products', 'Observation_date', 'PI_name',
    'PWV', 'Member_ous_id', 'Asdm_uid', 'Project_title', 'Project_type',
    'Scan_intent']


Region queries are just like any other in astroquery:

.. code-block:: python

    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> galactic_center = coordinates.SkyCoord(0*u.deg, 0*u.deg,
    ...                                        frame='galactic')
    >>> gc_data = Alma.query_region(galactic_center, 1*u.deg)
    >>> print(len(gc_data))
    82

Downloading Data
================

You can download ALMA data with astroquery, but be forewarned, cycle 0 and
cycle 1 data sets tend to be >100 GB!


.. code-block:: python

   >>> import numpy as np
   >>> uids = np.unique(m83_data['Asdm_uid'])
   >>> print(uids)
           Asdm_uid
    -----------------------
    uid://A002/X3b3400/X90f
    uid://A002/X3b3400/Xaf3
    uid://A002/X3fbe56/X607
    uid://A002/X4b29af/X24c
     uid://A002/X4b29af/X5c

You can then stage the data and see how big it is (you can ask for one or more
UIDs):


.. code-block:: python

   >>> link_list = Alma.stage_data(uids[0:2])
   >>> Alma.data_size(link_list)
   INFO: Staging files... [astroquery.alma.core]
   <Quantity 146.51379712000002 Gbyte>

You can then go on to download that data.  The download will be cached so that repeat
queries of the same file will not re-download the data.  The default cache
directory is `~/.astropy/cache/astroquery/Alma/`, but this can be changed by
changing the ``cache_location`` variable:

.. code-block:: python

   >>> myAlma = Alma()
   >>> myAlma.cache_location = '/big/external/drive/'
   >>> myAlma.download_files(link_list, cache=True)

You can also do the downloading all in one step:

.. code-block:: python

   >>> myAlma.retrieve_data_from_uid(uids[0])

Reference/API
=============

.. automodapi:: astroquery.alma
    :no-inheritance-diagram:
