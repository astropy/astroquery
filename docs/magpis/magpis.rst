.. _astroquery.magpis:

*****************************************
MAGPIS Queries (`astroquery.magpis`)
*****************************************

Getting started
===============

This module may be used to fetch image cutouts in the FITS format from various
MAGPIS surveys. The only required parameter is the target you wish to search
for. This may be specified as a name - which is resolved online via astropy
functions or as coordinates using any of the coordinate systems available in
`astropy.coordinates`. The FITS image is returned as an
`~astropy.io.fits.HDUList` object. Here is a sample query:

.. doctest-remote-data::

    >>> from astroquery.magpis import Magpis
    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> image = Magpis.get_images(coordinates.SkyCoord(10.5*u.deg, 0.0*u.deg,
    ...                                                frame='galactic'))
    >>> image   # doctest: +IGNORE_OUTPUT

    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x4008650>]

There are some other optional parameters that you may additionally specify.
For instance the image size may be specified by setting the ``image_size``
parameter. It defaults to 1 arcmin, but may be set to any other value using the
appropriate `~astropy.units.Quantity` object.

You may also specify the MAGPIS survey from which to fetch the cutout via the
keyword ``survey``. To know the list of valid surveys:

.. doctest-remote-data::

    >>> from astroquery.magpis import Magpis
    >>> Magpis.list_surveys()
    ['gps6',
     'gps6epoch2',
     'gps6epoch3',
     'gps6epoch4',
     'gps20',
     'gps20new',
     'gps90',
     'gpsmsx',
     'gpsmsx2',
     'gpsglimpse36',
     'gpsglimpse45',
     'gpsglimpse58',
     'gpsglimpse80',
     'mipsgal',
     'atlasgal',
     'bolocam']

The default survey used is 'bolocam'. Here is a query setting these optional
parameters as well.

.. doctest-remote-data::

    >>> from astroquery.magpis import Magpis
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> image = Magpis.get_images(coordinates.SkyCoord(10.5*u.deg, 0.0*u.deg,
    ...                                                frame='galactic'),
    ...                                                image_size=10*u.arcmin,
    ...                                                survey='gps20new')
    >>> image  # doctest: +IGNORE_OUTPUT

    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x4013e10>]


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.magpis import Magpis
    >>> Magpis.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.magpis
    :no-inheritance-diagram:
