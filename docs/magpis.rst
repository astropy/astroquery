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
`astropy.coordinates`_. The FITS image is returned as an
`astropy.io.fits`_ `HDUList` object. Here is a sample query:

.. code-block:: python

    >>> from astroquery.magpis import Magpis
    >>> import astropy.coordinates as coord
    >>> image = Magpis.get_images(coord.GalacticCoordinates(10.5, 0.0,
    ...    unit=(u.deg,u.deg)))
    >>> image
    
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x4008650>]

There are some other optional parameters that you may additionally specify.
For instance the image size may be specified by setting the `image_size`
parameter. It defaults to 1 arcmin, but may be set to any other value using the
appropriate `astropy.units`_ `Quantity` object.

You may also specify the MAGPIS survey from which to fetch the cutout via the
keyword `survey`. To know the list of valid surveys:

.. code-block:: python

    >>> from astroquery.magpis import Magpis
    >>> Magpis.list_surveys()

        ['gps6epoch3',
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
     'bolocam']

The default survey used is 'bolocam'. Here is a query setting these optional
parameters as well.

.. code-block:: python

    >>> from astroquery.magpis import Magpis
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> image = Magpis.get_images(coord.GalacticCoordinates(10.5, 0.0,
    ...    unit=(u.deg,u.deg)), image_size=10*u.arcmin, survey='gps20new')
    >>> image

    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x4013e10>]


Reference/API
=============

.. automodapi:: astroquery.magpis
    :no-inheritance-diagram:

.. _astropy.units: http://docs.astropy.org/en/latest/units/index.html 
.. _astropy.coordinates: http://docs.astropy.org/en/latest/coordinates/index.html
.. _astropy.io.fits: http://docs.astropy.org/en/latest/io/fits/index.html
