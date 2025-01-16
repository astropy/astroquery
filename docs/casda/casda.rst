.. _astroquery.casda:

**********************************
CASDA Queries (`astroquery.casda`)
**********************************

The CSIRO ASKAP Science Data Archive (CASDA) provides access to science-ready data products
from observations at the `Australian Square Kilometre Array Pathfinder (ASKAP) <https://www.csiro.au/en/about/facilities-collections/atnf/askap-radio-telescope>`_ telescope.
These data products include source catalogues, images, spectral line and polarisation cubes, spectra and visbilities.
This package allows querying of the data products available in CASDA (`<https://research.csiro.au/casda>`_).

Listing Data Products
=====================

The metadata for data products held in CASDA may be queried using the :meth:`~astroquery.casda.CasdaClass.query_region` method.
The results are returned in a `~astropy.table.Table`.
The method takes a location and either a radius or a height and width of the region to be queried.
The location should be specified in ICRS coordinates or an `astropy.coordinates.SkyCoord` object.
For example:

.. doctest-remote-data::

    >>> from astroquery.casda import Casda
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> centre = SkyCoord.from_name('NGC 7232')
    >>> result_table = Casda.query_region(centre, radius=30*u.arcmin)
    >>> print(result_table['obs_publisher_did','s_ra', 's_dec', 'obs_release_date'][:5])  # doctest: +IGNORE_OUTPUT
    obs_publisher_did       s_ra           s_dec           obs_release_date
                            deg             deg
    ----------------- --------------- ---------------- ------------------------
            cube-1170 333.70448386919 -45.966341151806 2019-01-30T13:00:00.000Z
           cube-60339 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z
           cube-60338 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z
           cube-60337 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z
           cube-60336 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z


In most cases only public data is required. While most ASKAP data is public, some data products may not be released for quality reasons.
Some derived data produced by science teams may also be embargoed to the science team for a period of team.
To filter down to just the public data you can use the :meth:`~astroquery.casda.CasdaClass.filter_out_unreleased` method.

For example to filter out the 30 non-public results from the above data set:

.. doctest-remote-data::

    >>> public_results = Casda.filter_out_unreleased(result_table)
    >>> print(public_results['obs_publisher_did','s_ra', 's_dec', 'obs_release_date'][:5])  # doctest: +IGNORE_OUTPUT
    obs_publisher_did       s_ra           s_dec           obs_release_date
                            deg             deg
    ----------------- --------------- ---------------- ------------------------
            cube-1170 333.70448386919 -45.966341151806 2019-01-30T13:00:00.000Z
           cube-60339 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z
           cube-60338 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z
           cube-60337 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z
           cube-60336 333.74878924962  -46.50601666028 2022-03-18T00:32:52.674Z


Authentication
==============

User authentication is required to access data files from CASDA, including
calibrated visibilities, images and image cubes.
Authentication is made with OPAL credentials.
To register with OPAL, go to https://opal.atnf.csiro.au/ and click on the
link to 'Register'. Enter your email address, name, affiliation and a password.
The OPAL application will register you straight away.

OPAL user accounts are self-managed. Please keep your account details up to
date. To change user-registration details, or to request a new OPAL password,
use the link to 'Log in or reset password'.

To use download tasks, you should create an instance of the ``Casda`` class
and call the :meth:`~astroquery.casda.CasdaClass.login` method with a username. The password will either be taken
from the keyring, or if in an interactive environment then it will be requested. e.g.:

.. doctest-skip::

    >>> from astroquery.casda import Casda
    >>> casda = Casda()
    >>> casda.login(username='email@somewhere.edu.au')

.. Note::

   Prior to Astroquery v0.4.7, authentication required creating an instance of the ``Casda`` class
   with a username and password. e.g.: ``casda = Casda(username, password)``

Data Access
===========

.. versionadded:: 0.4.4

In order to access data in CASDA you must first stage the data using the :meth:`~astroquery.casda.CasdaClass.stage_data`
method.
This is because only some of the data in CASDA is held on disc at any particular time.
The :meth:`~astroquery.casda.CasdaClass.stage_data` method should be passed an astropy Table object containing an
'access_url' column.
This column should contain the datalink address of the data product.

Once the data has been assembled you can then download the data using the :meth:`~astroquery.casda.CasdaClass.download_files`
method, or using tools such as wget.
Authentication is required when staging the data, but not for the download.

An example script to download public continuum images of the NGC 7232 region
taken in scheduling block 2338 is shown below:

.. doctest-skip::

    >>> from astropy import coordinates, units as u, wcs
    >>> from astroquery.casda import Casda
    >>> centre = coordinates.SkyCoord.from_name('NGC 7232')
    >>> casda = Casda()
    >>> casda.login(username='email@somewhere.edu.au')
    >>> result = Casda.query_region(centre, radius=30*u.arcmin)
    >>> public_data = Casda.filter_out_unreleased(result)
    >>> subset = public_data[(public_data['dataproduct_subtype']=='cont.restored.t0') & (public_data['obs_id']=='2338')]
    >>> url_list = casda.stage_data(subset)
    >>> filelist = casda.download_files(url_list, savedir='/tmp')

.. Note::

   Due to server side changes, downloads now require Astroquery v0.4.6 or later.

Cutouts
=======

.. versionadded:: 0.4.7

As well as accessing full data products, the CASDA service can produce cutout images and cubes from larger data products.
The cutout support in AstroQuery allows both spatial and spectral cutouts.
To produce a spatial cutout, pass in a coordinate and either a radius or a height and a width to the
:meth:`~astroquery.casda.CasdaClass.cutout` method.
To produce a spectral cutout, pass in either a band or a channel value.
For band, the value must be a list or tuple of two `astropy.units.Quantity` objects specifying a low and high frequency
or wavelength. For an open ended range use `None` as the open value.
For channel, the value must be a list or tuple of two integers specifying the low and high channels (i.e. planes of a
cube) inclusive.
Spatial and spectral parameters can be combined to produce sub-cubes.

Once completed, the cutouts can be downloaded as described in the section above.

An example script to download a 2D cutout from the Rapid ASKAP Continuum Survey (RACS) at a specified position is shown
below:

.. doctest-skip::

    >>> from astropy import coordinates, units as u, wcs
    >>> from astroquery.casda import Casda
    >>> centre = coordinates.SkyCoord.from_name('2MASX J08161181-7039447')
    >>> casda = Casda()
    >>> casda.login(username='email@somewhere.edu.au')
    >>> result = Casda.query_region(centre, radius=30*u.arcmin)
    >>> public_data = Casda.filter_out_unreleased(result)
    >>> subset = public_data[((public_data['obs_collection'] == 'The Rapid ASKAP Continuum Survey') & #
                      (np.char.startswith(public_data['filename'], 'RACS-DR1_')) & #
                      (np.char.endswith(public_data['filename'], 'A.fits'))
                     )]
    >>> url_list = casda.cutout(subset[:1], coordinates=centre, radius=14*u.arcmin)
    >>> filelist = casda.download_files(url_list, savedir='/tmp')

An example script to download a 3D cutout from the WALLABY Pre-Pilot Eridanus cube at a specified position and velocity range
is shown below:

.. doctest-skip::

    >>> from astropy import coordinates, units as u, wcs
    >>> from astroquery.casda import Casda
    >>> centre = coordinates.SkyCoord.from_name('NGC 1371')
    >>> casda = Casda()
    >>> casda.login(username='email@somewhere.edu.au')
    >>> result = Casda.query_region(centre, radius=30*u.arcmin)
    >>> public_data = Casda.filter_out_unreleased(result)
    >>> eridanus_cube = public_data[public_data['filename'] == 'Eridanus_full_image_V3.fits']
    >>> vel = np.array([1250, 1600])*u.km/u.s
    >>> freq = vel.to(u.Hz, equivalencies=u.doppler_radio(1.420405751786*u.GHz))
    >>> url_list = casda.cutout(eridanus_cube, coordinates=centre, radius=9*u.arcmin, band=freq)
    >>> filelist = casda.download_files(url_list, savedir='/tmp')

An example script to download a 3D cutout of a spectral channel range from the WALLABY Pre-Pilot Eridanus cube
is shown below:

.. doctest-skip::

    >>> from astropy import coordinates, units as u, wcs
    >>> from astroquery.casda import Casda
    >>> centre = coordinates.SkyCoord.from_name('NGC 1371')
    >>> casda = Casda()
    >>> casda.login(username='email@somewhere.edu.au')
    >>> result = Casda.query_region(centre, radius=30*u.arcmin)
    >>> public_data = Casda.filter_out_unreleased(result)
    >>> eridanus_cube = public_data[public_data['filename'] == 'Eridanus_full_image_V3.fits']
    >>> channel = (5, 10)
    >>> url_list = casda.cutout(eridanus_cube, channel=channel)
    >>> filelist = casda.download_files(url_list, savedir='/tmp')


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.casda import Casda
    >>> Casda.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.



Reference/API
=============

.. automodapi:: astroquery.casda
    :no-inheritance-diagram:

.. _IAU format: https://cds.unistra.fr/Dic/iau-spec.html.
