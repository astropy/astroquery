.. doctest-skip-all

.. _astroquery.alma:

********************************
ALMA Queries (`astroquery.alma`)
********************************

Example Notebooks
=================
A series of example notebooks can be found here:

 * `What has ALMA observed toward all Messier objects? (an example of querying many sources) <http://nbviewer.ipython.org/gist/keflavich/e798e10e3bf9a93d1453>`_
 * `ALMA finder chart of the Cartwheel galaxy and public Cycle 1 data quicklooks <http://nbviewer.ipython.org/gist/keflavich/d5af22578094853e2d24>`_
 * `Finder charts toward many sources with different backgrounds <http://nbviewer.ipython.org/gist/keflavich/2ef877ec90d774645fee>`_
 * `Finder chart and downloaded data from Cycle 0 observations of Sombrero Galaxy <http://nbviewer.ipython.org/gist/keflavich/9934c9412d8f58299962>`_

Getting started
===============

`astroquery.alma` provides the astroquery interface to the ALMA archive.  It
supports object and region based querying and data staging and retrieval.

You can get interactive help to find out what keywords to query for:

.. code-block:: python

   >>> from astroquery.alma import Alma
   >>> Alma.help()
   Valid ALMA keywords:

   Position
     Source name (Resolver)           : source_name_resolver
     Source name (ALMA)               : source_name_alma
     RA Dec                           : ra_dec

   Energy
     Frequency                        : frequency
     Bandwidth                        : bandwidth
     Spectral resolution              : spectral_resolution
     Band                             : 3(84-116 GHz) = 3 , 4(125-163 GHz) = 4 , 6(211-275 GHz) = 6 , 7(275-373 GHz) = 7 , 8(385-500 GHz) = 8 , 9(602-720 GHz) = 9 , 10(787-950 GHz) = 10

   Time
     Observation date                 : start_date
     Integration time                 : integration_time

   Polarisation
     Polarisation type                : Stokes I = 0 , Single = 1 , Dual = 2 , Full = =3|4

   Observation
     Water vapour                     : water_vapour

   Project
     Project code                     : project_code
     Project title                    : project_title
     PI name                          : pi_name

   Options
     (I) View:                        : result_view          = raw
     ( ) View:                        : result_view          = project
     [x] public data only             : public_data          = public
     [x] science observations only    : science_observations = =%TARGET%
   

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
    830
    >>> m83_data.colnames
    ['Project code', 'Source name', 'RA', 'Dec', 'Band',
    'Frequency resolution', 'Integration', 'Release date', 'Frequency support',
    'Velocity resolution', 'Pol products', 'Observation date', 'PI name',
    'PWV', 'Member ous id', 'Asdm uid', 'Project title', 'Project type',
    'Scan intent', 'Spatial resolution', 'QA0 Status', 'QA2 Status']


Region queries are just like any other in astroquery:

.. code-block:: python

    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> galactic_center = coordinates.SkyCoord(0*u.deg, 0*u.deg,
    ...                                        frame='galactic')
    >>> gc_data = Alma.query_region(galactic_center, 1*u.deg)
    >>> print(len(gc_data))
    383

Downloading Data
================

You can download ALMA data with astroquery, but be forewarned, cycle 0 and
cycle 1 data sets tend to be >100 GB!


.. code-block:: python

   >>> import numpy as np
   >>> uids = np.unique(m83_data['Member ous id'])
   >>> print(uids)
        Member ous id
    -----------------------
     uid://A002/X3216af/X31
    uid://A002/X5a9a13/X689


You can then stage the data and see how big it is (you can ask for one or more
UIDs):


.. code-block:: python

   >>> link_list = Alma.stage_data(uids)
   INFO: Staging files... [astroquery.alma.core]
   >>> link_list['size'].sum()
   159.26999999999998

You can then go on to download that data.  The download will be cached so that repeat
queries of the same file will not re-download the data.  The default cache
directory is ``~/.astropy/cache/astroquery/Alma/``, but this can be changed by
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
    >>> uid_url_table = Alma.stage_data(result['Member ous id'])
    >>> # Extract the data with tarball file size < 1GB
    >>> small_uid_url_table = uid_url_table[uid_url_table['size'] < 1]
    >>> # get the first 10 files...
    >>> filelist = Alma.download_and_extract_files(small_uid_url_table[:10]['URL'])

You might want to look at the READMEs from a bunch of files so you know what kind of S/N to expect:

.. code-block:: python

    >>> filelist = Alma.download_and_extract_files(uid_url_table['URL'], regex='.*README$')


Further Examples
================
There are some nice examples of using the ALMA query tool in conjunction with other astroquery
tools in :doc:`../gallery`, especially :ref:`gallery-almaskyview`.

Reference/API
=============

.. automodapi:: astroquery.alma
    :no-inheritance-diagram:

.. automodapi:: astroquery.alma.utils
    :no-inheritance-diagram:
