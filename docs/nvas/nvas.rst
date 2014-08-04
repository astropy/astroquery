.. doctest-skip-all

.. _astroquery.nvas:

********************************
NVAS Queries (`astroquery.nvas`)
********************************

Getting started
===============

This module may be used to retrieve the NVAS VLA archive images. All images are
returned as a list of `~astropy.io.fits.HDUList` objects. Images may be
fetched by specifying directly an object name around which to search - in this
case the name will be resolved to coordinates by astropy name resolving methods
that use online services like SESAME. The search centre may also be entered as
a coordinate using any coordinate system from `astropy.coordinates`. ICRS
coordinates can also be entered directly as a string that conforms to the
format specified by `astropy.coordinates`. Some other parameters you may
optionally specify are the ``radius`` and the frequency band for which the image
must be fetched. You can also specify the maximum allowable noise level in mJy
via the ``max_rms`` keyword parameter. By default this is set to 10000 mJy 

.. code-block:: python
    
    >>> from astroquery.nvas import Nvas
    >>> import astropy.units as u
    >>> images = Nvas.get_images("3c 273", radius=2*u.arcsec, band="K", max_rms=500)

    1 images found.
    Downloading http://www.vla.nvas.edu/astro/archive/pipeline/position/J122906.7+020308/22.4I0.37_TEST_1995NOV15_1_352.U55.6S.imfits
    |===========================================|  10M/ 10M (100.00%)     19m37s

    >>> images

    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x3376150>]]


The ``radius`` may be specified in any appropriate unit using a `~astropy.units.Quantity`
object. Apart from that it may also be entered as a string in a format
parsable by `~astropy.coordinates.Angle`. The frequency bands are specified
using the ``band`` keyword parameter. This defaults to a value of ``all`` - i.e all
the bands. Here's a list of the valid values that this parameter can take. ::

    "all", "L", "C", "X", "U", "K", "Q"

Let's look at an example that uses coordinates for specifying the search
centre.

.. code-block:: python

    >>> from astroquery.nvas import Nvas
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> images = Nvas.get_images(coord.SkyCoord(49.489, -0.37,
    ...                          unit=(u.deg, u.deg), frame='galactic'),
    ...                          band="K")

                                 
You may also fetch UVfits files rather than the IMfits files which is the
default. To do this simply set the ``get_uvfits`` to ``True``, in any of the query
methods. You can also fetch the URLs to the downloadable images rather than the
actual images themselves. To do this use the
:meth:`~astroquery.nvas.NvasClass.get_image_list` which takes in all the same
arguments as :meth:`~astroquery.nvas.NvasClass.get_images` above except for the
``verbose`` argument which isn't relevant in this case.

.. code-block:: python
  
    >>> from astroquery.nvas import Nvas
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> image_urls = Nvas.get_image_list("05h34m31.94s 22d00m52.2s",
    ...                                  radius='0d0m0.6s', max_rms=500)

    WARNING: Coordinate string is being interpreted as an ICRS
    coordinate. [astroquery.utils.commons]

    >>> image_urls
    
     ['http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.5+220114/1.51I4.12_T75_1986AUG12_1_118.U3.06M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.5+220114/1.51I3.92_T75_1986AUG20_1_373.U2.85M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.5+220114/4.89I1.22_T75_1986AUG12_1_84.8U2.73M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/1.44I1.26_AH0336_1989FEB03_1_197.U8.29M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/1.44I1.32_AH0336_1989FEB03_1_263.U3.84M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/4.91I0.96_AH595_1996OCT14_1_41.3U2.45M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/4.91I0.89_AH595_1996OCT11_1_43.2U2.45M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/4.91I0.99_AH0595_1996OCT16_1_66.4U2.55M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/8.46I2.18_AM503_1996FEB23_1_243.U2.59M.imfits',
     'http://www.vla.nrao.edu/astro/archive/pipeline/position/J053431.9+220052/8.46I1.60_AM503_1996FEB01_1_483.U2.59M.imfits']


Reference/API
=============

.. automodapi:: astroquery.nvas
    :no-inheritance-diagram:
