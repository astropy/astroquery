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

The `~astroquery.mast.MastClass.resolve_object` method accepts an object name to resolve into coordinates. If the ``resolver``
parameter is specified, then only that resolver will be queried. If the ``resolver`` parameter is not specified, then all available resolvers 
will be queried in a default order, and the first one to return a result will be used. 
Options for the ``resolver`` parameter are "SIMBAD" and "NED".

.. doctest-remote-data::
   
   >>> from astroquery.mast import Mast
   >>> mast = Mast()
   >>> coords = mast.resolve_object("M101", resolver="NED")
   >>> print(coords)
   <SkyCoord (ICRS): (ra, dec) in deg
    (210.80227, 54.34895)>

If the ``resolve_all`` parameter is set to ``True``, all resolvers will be queried, and those that give a result will be returned.
The ``resolver`` parameter is ignored in this case. The results are returned as a dictionary, with the resolver name as the key and 
the coordinates as the value.

.. doctest-remote-data::

   >>> coords = mast.resolve_object("TIC 441662144", resolve_all=True)
   >>> print(coords)
   {'TIC': <SkyCoord (ICRS): (ra, dec) in deg
    (210.75138371, 54.49144496)>}


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
