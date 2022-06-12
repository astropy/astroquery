.. _astroquery.desi:

*********************************************
DESI LegacySurvey Queries (`astroquery.desi`)
*********************************************

Getting started
===============

This module provides a way to query the DesiLegacySurvey service.
Presented below are examples that illustrate the different types of queries
that can be formulated.

Query a region
==============

This example shows how to query a certain region with DesiLegacySurvey.
We'll use a set of coordinates that define the region of interest,
and search within a 5 arcmin radius.

.. doctest-remote-data::

    >>> from astroquery.desi import DESILegacySurvey
    >>> from astropy.coordinates import Angle, SkyCoord
    >>> ra = Angle('11h04m27s', unit='hourangle').degree
    >>> dec = Angle('+38d12m32s', unit='hourangle').degree
    >>> coordinates = SkyCoord(ra, dec, unit='degree')
    >>> radius = Angle(5, unit='arcmin')
    >>> table_out = DESILegacySurvey.query_region(coordinates, radius, data_release=9)
    >>> print(table_out[:5])
         ls_id              dec                ra         ... type wise_coadd_id
                                                          ...
    ---------------- ----------------- ------------------ ... ---- -------------
    9907734382838387 38.12628495570797  166.0838654387131 ...  PSF      1667p378
    9907734382838488 38.12798336424771  166.0922968862182 ...  PSF      1667p378
    9907734382838554 38.12858283671958  166.0980673954384 ...  REX      1667p378
    9907734382838564 38.12840803351445  166.09921863682337 ...  EXP      1667p378
    9907734382838584 38.12836885301038  166.10070750146636 ...  REX      1667p378

The result is an astropy.Table.

Get images
==========

To download images for a certain region of interest,
we can define our region in the same way used in the example above.

.. doctest-remote-data::

    >>> from astroquery.desi import DESILegacySurvey
    >>> from astropy.coordinates import Angle, SkyCoord
    >>>
    >>> ra = Angle('11h04m27s', unit='hourangle').degree
    >>> dec = Angle('+38d12m32s', unit='hourangle').degree
    >>> radius_input = 0.5
    >>> pixels = 60
    >>>
    >>> pos = SkyCoord(ra, dec, unit='degree')
    >>> radius = Angle(radius_input, unit='arcmin')
    >>> im = DESILegacySurvey.get_images(pos, pixels, radius, data_release=9)

All the information we need can be found within the object "im".

.. doctest-remote-data::

    >>> hdul = im[0]
    >>> hdul[0].header
    SIMPLE  =                    T / file does conform to FITS standard
    BITPIX  =                  -32 / number of bits per data pixel
    NAXIS   =                    2 / number of data axes
    NAXIS1  =                   60 / length of data axis 1
    NAXIS2  =                   60 / length of data axis 2
    EXTEND  =                    T / FITS dataset may contain extensions
    COMMENT   FITS (Flexible Image Transport System) format is defined in 'Astronomy
    COMMENT   and Astrophysics', volume 376, page 359; bibcode: 2001A&A...376..359H
    BANDS   = 'g       '
    BAND0   = 'g       '
    CTYPE1  = 'RA---TAN'           / TANgent plane
    CTYPE2  = 'DEC--TAN'           / TANgent plane
    CRVAL1  =             166.1125 / Reference RA
    CRVAL2  =     38.2088888888889 / Reference Dec
    CRPIX1  =                 30.5 / Reference x
    CRPIX2  =                 30.5 / Reference y
    CD1_1   = -0.000277777777777778 / CD matrix
    CD1_2   =                   0. / CD matrix
    CD2_1   =                   0. / CD matrix
    CD2_2   = 0.000277777777777778 / CD matrix
    IMAGEW  =                  60. / Image width
    IMAGEH  =                  60. / Image height

The variable "im" is a list of `~astropy.io.fits.HDUList` objects, one entry for
each corresponding object.


Reference/API
=============

.. automodapi:: astroquery.desi
  :no-inheritance-diagram:
