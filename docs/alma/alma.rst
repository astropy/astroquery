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
    >>> # First example: TEST is not a valid username, it will fail
    >>> alma.login("TEST") # doctest: +SKIP
    TEST, enter your ALMA password:

    Authenticating TEST on asa.alma.cl...
    Authentication failed!
    >>> # Second example: pretend ICONDOR is a valid username
    >>> alma.login("ICONDOR", store_password=True) # doctest: +SKIP
    ICONDOR, enter your ALMA password:

    Authenticating ICONDOR on asa.alma.cl...
    Authentication successful!
    >>> # After the first login, your password has been stored
    >>> alma.login("ICONDOR") # doctest: +SKIP
    Authenticating ICONDOR on asa.alma.cl...
    Authentication successful!

Your password will be stored by the `keyring
<https://pypi.python.org/pypi/keyring>`_ module.
You can choose not to store your password by passing the argument
``store_password=False`` to `Alma.login`.  You can delete your password later
with the command ``keyring.delete_password('astroquery:asa.alma.cl',
'username')``.

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

Downloading FITS data
=====================

If you want just the QA2-produced FITS files, you can download the tarball,
extract the FITS file, then delete the tarball:

.. code-block:: python

    >>> from astroquery.alma.core import Alma
    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> orionkl = coordinates.SkyCoord('5:35:14.461 -5:21:54.41', frame='fk5',
    ...                                unit=(u.hour, u.deg))
    >>> result = Alma.query_region(orionkl, radius=0.034*u.deg)
    >>> uid_url_table = Alma.stage_data(result['Asdm_uid'], cache=False)
    >>> # Extract the data with tarball file size < 1GB
    >>> small_uid_url_table = uid_url_table[uid_url_table['size'] < 1]
    >>> # get the first 10 files...
    >>> filelist = Alma.download_and_extract_files(small_uid_url_table[:10]['URL'])

You might want to look at the READMEs from a bunch of files so you know what kind of S/N to expect:

.. code-block:: python

    >>> filelist = Alma.download_and_extract_files(uid_url_table['URL'], regex='.*README$')


Reference/API
=============

.. automodapi:: astroquery.alma
    :no-inheritance-diagram:
