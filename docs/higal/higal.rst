.. doctest-skip-all

.. _astroquery.higal:

**************************************
HiGal Image Cutout and Catalog service
**************************************

Getting started
===============

The HiGal image cutout service is a sub-service of the Space Science Data
Center Sky Explorer (https://tools.ssdc.asi.it/).  It enables image cutout
queries and catalog queries.

An example catalog query:

.. python::
    >>> from astroquery.higal import HiGal
    >>> from astropy import units as u, coordinates
    >>> target = coordinates.SkyCoord(49.5, -0.3, frame='galactic', unit=(u.deg, u.deg))
    >>> result = HiGal.query_region(coordinates=target, radius=0.25*u.deg)
    >>> result
    <Table length=689>
       DEC         DESIGNATION       ERR_FINT ERR_FPEAK   FINT    FPEAK    FWHMA   FWHMB     GLAT      GLON      NAME       PA       RA    RMS_SURROUND rowid
     float64          str22          float64   float64  float64  float64  float64 float64  float64   float64    str10    float64  float64    float64    int64
    --------- ---------------------- -------- --------- -------- -------- ------- ------- --------- --------- ---------- ------- --------- ------------ -----
    14.335341 HIGALPB049.3443-0.4849    0.171    11.126  2.66513  203.692   22.77   17.43 -0.484918 49.344287 HIGAL_BLUE   -74.4 290.95059      28.8882  5567
    14.358867 HIGALPB049.3808-0.5031    0.158    14.851  3.72149  425.767   15.18   17.28 -0.503143 49.380769 HIGAL_BLUE    64.1 290.98497      56.3716  5513
    ...


And an example image query:

.. python::
    >>> from astroquery.higal import HiGal
    >>> from astropy import units as u, coordinates
    >>> target = coordinates.SkyCoord(49.5, -0.3, frame='galactic', unit=(u.deg, u.deg))
    >>> result = HiGal.get_images(coordinates=target, radius=0.25*u.deg)
    [[<astropy.io.fits.hdu.image.PrimaryHDU object at 0xb15715a58>],
     [<astropy.io.fits.hdu.image.PrimaryHDU object at 0xb156fda58>],
     [<astropy.io.fits.hdu.image.PrimaryHDU object at 0xb1571af98>],
     [<astropy.io.fits.hdu.image.PrimaryHDU object at 0xb1523e978>],
     [<astropy.io.fits.hdu.image.PrimaryHDU object at 0xb15243be0>]]
    

Reference/API
=============

.. automodapi:: astroquery.higal
    :no-inheritance-diagram:
