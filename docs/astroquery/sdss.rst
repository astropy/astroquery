.. _astroquery.sdss:

*****************************************
SDSS Queries (`astroquery.sdss`)
*****************************************

Getting started
===============

This example shows how to perform an object cross-ID with SDSS. We'll start
with the position of a source found in another survey, and search within a 5
arcsecond radius for optical counterparts in SDSS.

.. code-block:: python

    >>> from astroquery import sdss
    >>> xid = sdss.crossID(ra='0h8m05.63s', dec='14d50m23.3s', dr=5)
    >>> print xid
    [{'mjd': 52251, 'plate': 751, 'dec': 14.83982059, 'run': 1739, 'specClass': 3, 
    'z': 0.04541, 'field': 315, 'fiberID': 160, 'ra': 2.02344483, 'specobjid': 211612124516974592, 
    'rerun': 40, 'camcol': 3, 'objid': 587727221951234166}]
    
The result is a list, where each element is a dictionary containing information
about an SDSS source within our search radius. In this case, there is only 
one match.

Downloading data
================
If we'd like to download spectra and/or images for our match, we have all
the information we need in the elements of "xid" from the above example. 

..code-block:: python

    >>> sp = sdss.get_spectrum(crossID=xid[0])
    >>> im = sdss.get_image(crossID=xid[0], band='g')

or equivalently,

..code-block:: python

    >>> sp = sdss.get_spectrum(plate=xid[0]['plate'], fiberID=xid[0]['fiberID'],
    >>>     mjd=xid[0]['mjd'])
    >>> im = sdss.get_image(run=xid[0]['run'], rerun=xid[0]['rerun'],
    >>>     camcol=xid[0]['camcol'], field=xid[0]['field'], band='g')
    
The variables "sp" and "im" are simple objects which give users access to the
FITS files, and contain a few convenience properties to access the data quickly.
For example,

..code-block:: python

    >>> sp.hdulist
    >>> sp.data.mean(), sp.header.get('BUNIT')

will show the contents of the FITS file we downloaded, and then print the mean 
flux in the spectrum and its units.

In SDSS, image downloads retrieve the entire plate, we've included a simple 
method to make "postage-stamp" images. To view a region 30x30 arcseconds
centered on our matched object, do

..code-block:: python

    >>> pstamp = im.cutout(ra=xid[0]['ra'], dec=xid[0]['dec'], dr=30)
    
Spectral templates
==================
It is also possible to download spectral templates from SDSS. To see what is 
available, do

..code-block:: python
    
    >>> from astroquery import sdss
    >>> print sdss.spec_templates.keys()
    
Then, to download your favorite template, do something like

..code-block:: python

    >>> template = sdss.get_spectral_template('qso')

The variable "template" is a list of astroquery.sdss.core.Spectrum instances
(same object as "sp" in the above example). 

Reference/API
=============

.. automodapi:: astroquery.sdss
    :no-inheritance-diagram:
