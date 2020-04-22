.. doctest-skip-all

.. _astroquery.casda:

**********************************
CASDA Queries (`astroquery.casda`)
**********************************

The CSIRO ASKAP Science Data Archive (CASDA) provides access to science-ready data products
from observations at the `Australian Square Kilometre Array Pathfinder (ASKAP) <https://www.atnf.csiro.au/projects/askap/index.html>`_ telescope.
These data products include source catalogues, images, spectral line and polarisation cubes, spectra and visbilities.
This package allows querying of the data products available in CASDA (`<https://casda.csiro.au/>`_).

Listing Data Products
=====================

The metadata for data products held in CASDA may be queried using the :meth:`~astroquery.casda.CasdaClass.query_region` method.
The results are returned in a `~astropy.table.Table`.
The method takes a location and either a radius or a height and width of the region to be queried.
The location should be specified in ICRS coordinates or an `astropy.coordinates.SkyCoord` object.
For example:

.. code-block:: python

    >>> from astroquery.casda import Casda
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> centre = SkyCoord.from_name('NGC 7232')
    >>> result_table = Casda.query_region(centre, radius=30*u.arcmin)
    >>> print(result_table['obs_publisher_did','s_ra', 's_dec', 'obs_released_date'])
    obs_publisher_did       s_ra           s_dec          obs_released_date
                            deg             deg
    ----------------- --------------- ---------------- ------------------------
             cube-502 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-503 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-504 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-505 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-506 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-507 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-508 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-453 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
             cube-454 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
             cube-455 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
                  ...             ...              ...                      ...
             cube-468 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-469 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-470 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-471 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-472 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-473 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
            cube-1170 333.70448386919 -45.966341151806 2019-01-30T13:00:00.000Z
             cube-612 333.30189344648 -50.033321773361 2018-05-25T08:22:51.025Z
             cube-650 326.04487794126 -42.033324601808
             cube-651 335.54487794126 -42.033324601808
    Length = 121 rows


In most cases only public data is required. While most ASKAP data is public, some data products may not be released for quality reasons.
Some derived data produced by science teams may also be embargoed to the science team for a period of team.
To filter down to just the public data you can use the :meth:`~astroquery.casda.CasdaClass.filter_out_unreleased` method.

For example to filter out the 30 non-public results from the above data set:

.. code-block:: python

    >>> public_results = Casda.filter_out_unreleased(result_table)
    >>> print(public_results['obs_publisher_did','s_ra', 's_dec', 'obs_released_date'])
    obs_publisher_did       s_ra           s_dec          obs_released_date
                            deg             deg
    ----------------- --------------- ---------------- ------------------------
             cube-502 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-503 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-504 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-505 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-506 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-507 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-508 333.16767306594 -45.302084636451 2017-08-02T03:51:19.728Z
             cube-453 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
             cube-454 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
             cube-455 332.53629746595 -44.850153699406 2017-07-10T05:18:13.482Z
                  ...             ...              ...                      ...
             cube-468 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-469 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-470 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-471 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-472 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
             cube-473 332.53644868638 -44.834926604835 2017-07-10T05:18:48.812Z
            cube-1170 333.70448386919 -45.966341151806 2019-01-30T13:00:00.000Z
             cube-612 333.30189344648 -50.033321773361 2018-05-25T08:22:51.025Z
    Length = 81 rows


Authentication
==============

User authentication is required to access data files from CASDA, including calibrated visibilities, images and image cubes.
Authentication is made with OPAL credentials.
To register with OPAL, go to https://opal.atnf.csiro.au/ and click on the link to 'Register'. Enter your email address, name, affiliation and a password. The OPAL application will register you straight away.

OPAL user accounts are self-managed. Please keep your account details up to date. To change user-registration details, or to request a new OPAL password, use the link to 'Log in or reset password'.

To use download tasks, you should create an instance of the Casda object with a username and password. e.g.:

.. code-block:: python

    >>> from astroquery.casda import Casda
    >>> import getpass
    >>> username = 'email@somewhere.edu.au'
    >>> password = getpass.getpass(str("Enter your OPAL password: "))
    >>> casda = Casda(username, password)


Data Access
===========

In order to access data in CASDA you must first stage the data using the :meth:`~astroquery.casda.CasdaClass.stage_data` method.
This is because only some of the data in CASDA is held on disc at any particular time.
The :meth:`~astroquery.casda.CasdaClass.stage_data` method should be passed an astropy Table object containing an 'access_url' column.
This column should contain the datalink address of the data product.

Once the data has been assembled you can then download the data using the :meth:`~astroquery.casda.CasdaClass.download_files` method, or using tools such as wget.
Authentication is required when staging the data, but not for the download.

An example script to download public continuum images of the NGC 7232 region taken in scheduling block 2338 is shown below:
.. code-block:: python

    >>> from astropy import coordinates, units as u, wcs
    >>> from astroquery.casda import Casda
    >>> import getpass
    >>> centre = coordinates.SkyCoord.from_name('NGC 7232')
    >>> username = 'email@somewhere.edu.au'
    >>> password = getpass.getpass(str("Enter your OPAL password: "))
    >>> casda = Casda(username, password)
    >>> result = Casda.query_region(centre, radius=30*u.arcmin)
    >>> public_data = Casda.filter_out_unreleased(result)
    >>> subset = public_data[(public_data['dataproduct_subtype']=='cont.restored.t0') & (public_data['obs_id']=='2338')]
    >>> url_list = casda.stage_data(subset)
    >>> filelist = casda.download_files(url_list, savedir='/tmp')


Reference/API
=============

.. automodapi:: astroquery.casda
    :no-inheritance-diagram:

.. _IAU format: http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
