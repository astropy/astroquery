.. _astroquery.mast:

********************************
MAST Queries (`astroquery.mast`)
********************************

Introduction
============

The `Barbara A. Mikulski Archive for Space Telescopes (MAST) <https://archive.stsci.edu/>`__ is an astronomical data archive 
that hosts data for over `20 different missions <https://archive.stsci.edu/missions-and-data>`__, including NASA's 
flagship space telescopes. MAST includes both science and engineering data, with a primary focus on datasets in optical, 
ultraviolet, and near-infrared wavelengths. 

The `astroquery.mast` module provides a programmatic interface to query and access data from MAST. The MAST
module offers five main services to aid users in searching and downloading data from the archive.

- **Observation Queries**: Query MAST observational data using our `Portal API <https://mast.stsci.edu/api/v0/>`__. 
  Use this class to search for observations across missions, filter results, and retrieve data products.
- **Mission-Specific Queries**: Query mission-specific metadata for select MAST missions
  like Hubble and James Webb using our `MAST Search API <https://mast.stsci.edu/search/docs/?urls.primaryName=>`__. Use this 
  class to search for mission-specific datasets, filter results, and retrieve data products.
- **Catalogs Queries**: Query MAST catalog data. Use this class to search for sources in MAST-hosted catalogs
  like Pan-STARRS and the Hubble Source Catalog.
- **Image Cutouts**: Access image cutouts of data from TESS and Hubble. Use these classes to create and download cutouts 
  of specific regions of interest.
- **Advanced MAST Queries**: Provides low-level, direct access to the our `Portal API <https://mast.stsci.edu/api/v0/>`__. 
  This interface is useful for advanced queries, custom services, and functionality not yet wrapped by higher-level classes.


Getting Started
===============

The sections below describe the core `astroquery.mast` interfaces and common usage patterns.
Use the table of contents to jump directly to the class or workflow most relevant to your science goals.

.. toctree::
   :maxdepth: 2

   mast_obsquery
   mast_missions
   mast_catalog
   mast_cut
   mast_mastquery


Accessing Proprietary Data
==========================

To access exclusive data that is not publicly available, users may log into their
`MyST Account <https://archive.stsci.edu/registration/index.html>`_.
Each of the MAST query clases has a `~astroquery.mast.MastClass.login` function that allows users to authenticate
using a token. If a token is not supplied, the user will be prompted to enter one. Alternatively,
a query class may be initialized with the ``mast_token`` parameter set to a valid token string.

To view the authentication tokens associated with your account, visit the
`MAST authentication information page <https://auth.mast.stsci.edu/info>`__.

.. doctest-skip::

   >>> from astroquery.mast import Observations
   ...
   >>> my_session = Observations.login(token="12348r9w0sa2392ff94as841")
   INFO: MAST API token accepted, welcome User Name [astroquery.mast.core]
   ...
   >>> sessioninfo = Observations.session_info()
   eppn: user_name@stsci.edu
   ezid: uname
   ...

For security reasons, authentication tokens should not be hard-coded into scripts or Jupyter
notebooks. Instead, users should enter tokens using a secure input method such as
`~getpass.getpass`, which prevents the token from being displayed or logged.

MAST authentication tokens expire after **10 days of inactivity**. Each time a token is used
within that window, its expiration is reset to 10 days from the most recent use. Tokens have
a **maximum lifetime of 60 days**, after which a new token must be generated regardless of
activity.

The ``store_token`` argument on the `~astroquery.mast.MastClass.login` method can be used to securely 
store a token in the user’s system keyring for reuse in future sessions. A stored token may be replaced 
by setting the ``reenter_token`` argument to **True**. To manually end an authenticated session, 
use the `~astroquery.mast.MastClass.logout` method.


Resolving Object Names
=======================

Each of the MAST query classes has a `~astroquery.mast.MastClass.resolve_object` method that translates named targets into
coordinates. This method uses the `STScI Archive Name Translation Application (SANTA) <https://mastresolver.stsci.edu/Santa-war/>`_
service.

The `~astroquery.mast.MastClass.resolve_object` method accepts either a single object name or a list of object names. If the
``resolver`` parameter is specified, then only that resolver will be queried. If the ``resolver`` parameter is not specified,
then all available resolvers will be queried in a default order, and the first one to return a result will be used.
Valid options for the ``resolver`` parameter are "SIMBAD" and "NED".

The return value depends on whether ``resolve_all`` is set and whether the input is a single object name or multiple names:

* If ``resolve_all`` is **False** and a single object is passed, returns a `~astropy.coordinates.SkyCoord` object with
  the resolved coordinates.
* If ``resolve_all`` is **True** and a single object is passed, returns a dictionary where the keys are the resolver
  names and the values are `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.
* If ``resolve_all`` is **False** and multiple objects are passed, returns a dictionary where the keys are the object
  names and the values are `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.
* If ``resolve_all`` is **True** and multiple objects are passed, returns a dictionary where the keys are the object
  names and the values are nested dictionaries. In each nested dictionary, the keys are the resolver names and the
  values are `~astropy.coordinates.SkyCoord` objects with the resolved coordinates.

When multiple object names are provided, they are automatically split into batches of up to 30 names per request
to the SANTA service. This avoids timeouts and ensures reliable responses. Large input lists are therefore resolved
across multiple requests, with results combined into the final return object.

.. doctest-remote-data::
   
   >>> from pprint import pprint
   >>> from astroquery.mast import Mast
   >>> mast = Mast()
   ...
   >>> # Resolve a single object
   >>> coords = mast.resolve_object("M101", resolver="NED")
   >>> print(coords)  # doctest: +IGNORE_OUTPUT
   <SkyCoord (ICRS): (ra, dec) in deg
       (210.80227, 54.34895)>
   ...
   >>> # Resolve multiple objects
   >>> coords_multi = mast.resolve_object(["M101", "M51"], resolver="SIMBAD")
   >>> pprint(coords_multi)  # doctest: +IGNORE_OUTPUT
   {'M101': <SkyCoord (ICRS): (ra, dec) in deg
       (210.802429, 54.34875)>,
    'M51': <SkyCoord (ICRS): (ra, dec) in deg
       (202.469575, 47.195258)>}
   ...
   >>> # Resolve a single object with all resolvers
   >>> coords_dict = mast.resolve_object("M101", resolve_all=True)
   >>> pprint(coords_dict)  # doctest: +IGNORE_OUTPUT
   {'NED': <SkyCoord (ICRS): (ra, dec) in deg
       (210.80227, 54.34895)>,
    'SIMBAD': <SkyCoord (ICRS): (ra, dec) in deg
       (210.802429, 54.34875)>,
    'SIMBADCFA': <SkyCoord (ICRS): (ra, dec) in deg
       (210.802429, 54.34875)>}
   ...
   >>> # Resolve multiple objects with all resolvers
   >>> coords_dict_multi = mast.resolve_object(["M101", "M51"], resolve_all=True)
   >>> pprint(coords_dict_multi)  # doctest: +IGNORE_OUTPUT
   {'M101': {'NED': <SkyCoord (ICRS): (ra, dec) in deg
      (210.80227, 54.34895)>,
            'SIMBAD': <SkyCoord (ICRS): (ra, dec) in deg
      (210.802429, 54.34875)>,
            'SIMBADCFA': <SkyCoord (ICRS): (ra, dec) in deg
      (210.802429, 54.34875)>},
   'M51': {'NED': <SkyCoord (ICRS): (ra, dec) in deg
      (202.48417, 47.23056)>,
            'SIMBAD': <SkyCoord (ICRS): (ra, dec) in deg
      (202.469575, 47.195258)>,
            'SIMBADCFA': <SkyCoord (ICRS): (ra, dec) in deg
      (202.469575, 47.195258)>}}


Additional Resources
====================

The `MAST Notebooks Repository <https://github.com/spacetelescope/mast_notebooks>`__ includes a collection of
Jupyter notebook tutorials, many of which utilize `astroquery.mast` to access MAST data programmatically.


Reference/API
=============

.. automodapi:: astroquery.mast
    :no-inheritance-diagram:
    :inherited-members:


.. testcleanup::

    >>> from astroquery.utils import cleanup_saved_downloads
    >>> cleanup_saved_downloads(['mastDownload*', 'tess-*', 'lwp13058*', '3dhst*'])
