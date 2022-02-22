.. _astroquery.sdss:

********************************
SDSS Queries (`astroquery.sdss`)
********************************

Getting started
===============

This example shows how to perform an object cross-ID with SDSS. We'll start
with the position of a source found in another survey, and search within a 5
arcsecond radius for optical counterparts in SDSS. Note use of the keyword
argument spectro, which requires matches to have spectroscopy, not just
photometry:

.. doctest-remote-data::

    >>> from astroquery.sdss import SDSS
    >>> from astropy import coordinates as coords
    >>> pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s', frame='icrs')
    >>> xid = SDSS.query_region(pos, spectro=True)
    >>> print(xid)
           ra              dec        ...     specobjid      run2d
    ---------------- ---------------- ... ------------------ -----
    2.02344596573482 14.8398237551311 ... 845594848269461504    26

The result is an astropy.Table.

Downloading data
================
If we'd like to download spectra and/or images for our match, we have all
the information we need in the elements of "xid" from the above example.

.. doctest-remote-data::

    >>> sp = SDSS.get_spectra(matches=xid)
    >>> im = SDSS.get_images(matches=xid, band='g')

The variables "sp" and "im" are lists of `~astropy.io.fits.HDUList` objects, one entry for
each corresponding object in xid.

Note that in SDSS, image downloads retrieve the entire plate, so further
processing will be required to excise an image centered around the point of
interest (*i.e.*, the object(s) returned by
`~astroquery.sdss.SDSSClass.query_region`).

Spectral templates
==================

.. warning::

    These templates are from the SDSS-I/II spectroscopic pipeline
    (DR7 and earlier). SDSS-III/IV (DR8 and later) spectroscopic processing
    pipelines use different templates.

It is also possible to download spectral templates from SDSS. To see what is
available, do

.. doctest-remote-data::

    >>> from astroquery.sdss import SDSS
    >>> print(SDSS.AVAILABLE_TEMPLATES)    # doctest: +IGNORE_OUTPUT
    {'star_O': 0, 'star_OB': 1, 'star_B': 2, 'star_A': [3, 4], 'star_FA': 5,
    'star_F': [6, 7], 'star_G': [8, 9], 'star_K': 10, 'star_M1': 11, 'star_M3': 12,
    'star_M5': 13, 'star_M8': 14, 'star_L1': 15, 'star_wd': [16, 20, 21], 'star_carbon': [17, 18, 19],
    'star_Ksubdwarf': 22, 'galaxy_early': 23, 'galaxy': [24, 25, 26], 'galaxy_late': 27, 'galaxy_lrg': 28,
    'qso': 29, 'qso_bal': [30, 31], 'qso_bright': 32}

Then, to download your favorite template, do something like

.. code-block:: python

    >>> template = SDSS.get_spectral_template('qso')    # doctest: +REMOTE_DATA

The variable "template" is a list of `~astropy.io.fits.HDUList` objects
(same object as "sp" in the above example). In this case there is only one
result, but in a few cases there are multiple templates available to choose
from (*e.g.*, the "galaxy" spectral template will actually return 3 templates).

Reference/API
=============

.. automodapi:: astroquery.sdss
    :no-inheritance-diagram:
