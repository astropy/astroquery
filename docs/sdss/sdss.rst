.. _astroquery.sdss:

********************************
SDSS Queries (`astroquery.sdss`)
********************************

Default Data Release
====================

The default data release is set to Data Release 17 (DR17), which is
the final data release of the Sloan Digital Sky Survey IV.  DR17
contains new optical and infrared spectra from both Apache Point
Observatory and Las Campanas Observatory. Previously released
integral-field datacubes and maps, stellar library spectra, as well as
images, are also included in DR17.  Users may select alternate DR's.

Getting started
===============

This example shows how to perform an individual object cross-ID with SDSS.
We'll start with the position of a source found in another survey, and search
within a 5 arcsecond radius (a "cone search") for optical counterparts in SDSS.
Note use of the keyword argument ``spectro``, which requires matches to have
spectroscopy, not just photometry:

.. doctest-remote-data::

    >>> from astroquery.sdss import SDSS
    >>> from astropy import coordinates as coords
    >>> pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s', frame='icrs')
    >>> xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)
    >>> print(xid)
           ra              dec        ...     specobjid      run2d
    ---------------- ---------------- ... ------------------ -----
    2.02344596573482 14.8398237551311 ... 845594848269461504    26

The result is an astropy.Table.

Searching regions and multiple objects
======================================

You can use `~astroquery.sdss.SDSSClass.query_region` to search multiple
locations; the input coordinates can be a single `astropy.coordinates` object
or a `list` or `~astropy.table.Column` of coordinates.
However, it is important to specify exactly what kind of search is
desired.  When `~astroquery.sdss.SDSSClass.query_region` is invoked with the
``radius`` keyword, a circle around each point is searched. This is also
called a "cone search".  When invoked in this mode,
`~astroquery.sdss.SDSSClass.query_region` is equivalent to
`~astroquery.sdss.SDSSClass.query_crossid`. Because of this equivalence, there
is a strict limit of 3 arcmin on the value of ``radius`` which is imposed
by the SDSS servers.

`~astroquery.sdss.SDSSClass.query_region` can also be used to search a
rectangular region centered on a coordinate or each coordinate in a list.
This mode is invoked with the ``width`` keyword, which is the width in
right ascension. Optionally, the ``height`` keyword can be used to specify
a different range of declination.  With these parameters,
`~astroquery.sdss.SDSSClass.query_region` constructs a rectangle in RA, dec
that does *not* correct for the geometry at high declination, also known as
the :math:`\cos \delta` correction.  At high declination, these rectangles
would appear much more like trapezoids. However, this is the more intuitive
interpretation of "this range of RA, that range of Dec" that many people use.
Finally, though, the constructed rectangles *do* account for RA wrap-around,
so an appropriate region of the celestial sphere is searched, even if the
central coordinate is very close to RA = 0.

Finally note that either ``radius`` or ``width`` must be specified.
Specifying neither or both will raise an exception.

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


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.sdss import SDSS
    >>> SDSS.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.sdss
    :no-inheritance-diagram:
