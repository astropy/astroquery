.. _astroquery.mast:

********************************
MAST Queries (`astroquery.mast`)
********************************

Introduction
============

The Mikulski Archive for Space Telescopes (MAST) is a NASA funded project made to
collect and archive a variety of scientific data to support the astronomical community.
The data housed in MAST includes science and engineering data, with a primary focus on
data sets in the optical, ultraviolet, and near-infrared parts of the spectrum, from over
20 space-based missions. MAST offers single mission-based queries as well as cross-mission
queries. Astroquery's astroquery.mast module is one tool used to query and access the data
in this Archive.

astroquery.mast offers 3 main services: `~astroquery.mast.MastClass`,
`~astroquery.mast.CatalogsClass`, and Cutouts. MastClass allows direct programatic access
to the MAST Portal. Along with `~astroquery.mast.ObservationsClass`, it is used to query
MAST observational data. The Catalogs class is used to query MAST catalog data. The
available catalogs include the Pan-STARRS and Hubble Source catalogs along with a few others
listed under the Catalog Queries section of this page. Lastly, Cutouts, a newer addition to
astroquery.mast, provides access to full-frame image cutouts of Transiting Exoplanet Survey
Satellite (TESS), MAST Hubble Advanced Product (HAP),and deep-field images, through
`~astroquery.mast.TesscutClass`, `~astroquery.mast.HapcutClass`, and
`~astroquery.mast.ZcutClass` respectively. For a full description of MAST query options,
please read the `MAST API Documentation <https://mast.stsci.edu/api/v0/>`__.

Getting Started
===============

This module can be used to query the Barbara A. Mikulski Archive for Space
Telescopes (MAST). Below are examples of the types of queries that can be used,
and how to access data products.

.. toctree::
   :maxdepth: 2

   mast_obsquery
   mast_missions
   mast_catalog
   mast_cut
   mast_mastquery


Accessing Proprietary Data
==========================

To access data that is not publicly available users may log into their
`MyST Account <https://archive.stsci.edu/registration/index.html>`_.
This can be done by using the `~astroquery.mast.MastClass.login` function,
or by initializing a class instance with credentials.

If a token is not supplied, the user will be prompted to enter one.

To view tokens accessible through your account, visit https://auth.mast.stsci.edu/info

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

\* For security tokens should not be typed into a terminal or Jupyter notebook
but instead input using a more secure method such as `~getpass.getpass`.


MAST tokens expire after 10 days of inactivity, at which point the user must generate a new token.  If
the key is used within that time, the token's expiration pushed back to 10 days.  A token's max
age is 60 days, afterward the user must generate a token.
The ``store_token`` argument can be used to store the token securely in the user's keyring.
This token can be overwritten using the ``reenter_token`` argument.
To logout before a session expires, the `~astroquery.mast.MastClass.logout` method may be used.


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

The Space Telescope Science Institute `Notebooks Repository <https://github.com/spacetelescope/notebooks>`_ includes many examples that use Astroquery.


Reference/API
=============

.. automodapi:: astroquery.mast
    :no-inheritance-diagram:
    :inherited-members:


.. testcleanup::

    >>> from astroquery.utils import cleanup_saved_downloads
    >>> cleanup_saved_downloads(['mastDownload*', 'tess-*', 'lwp13058*', '3dhst*'])
