.. doctest-skip-all

.. _astroquery.image_cutouts.first:

************************************************
FIRST Queries (`astroquery.image_cutouts.first`)
************************************************

Getting started
===============

This module may be used to fetch image cutouts in the FITS format from the
`Faint Images of the Radio Sky at Twenty-cm (FIRST) <https://sundog.stsci.edu>`_
VLA radio survey.  The only required parameter is the target you wish to search
for. This may be specified as a name - which is resolved online via astropy
functions or as coordinates using any of the coordinate systems available in
`astropy.coordinates`. The FITS image is returned as an
`~astropy.io.fits.HDUList` object. Here is a sample query:

.. code-block:: python

    >>> from astroquery.image_cutouts.first import First
    >>> from astropy import coordinates
    >>> from astropy import units as u
    >>> image = First.get_images(coordinates.SkyCoord(162.530*u.deg, 30.677*u.deg,
    ...                                                frame='icrs'))
    >>> image
    
    [<astropy.io.fits.hdu.image.PrimaryHDU object at 0x11c189390>]

There are some other optional parameters that you may additionally specify.
For instance the image size may be specified by setting the ``image_size``
parameter. It defaults to 1 arcmin, but may be set to another value using the
appropriate `~astropy.units.Quantity` object.

Reference/API
=============

.. automodapi:: astroquery.image_cutouts.first
    :no-inheritance-diagram:
