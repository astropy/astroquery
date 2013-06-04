.. _astroquery.alfalfa:

*****************************************
ALFALFA Queries (`astroquery.alfalfa`)
*****************************************

Getting started
===============

This example shows how to perform an object cross-ID with ALFALFA. We'll start
with the position of a source that exists in another survey (same object we
used in the SDSS example).

.. code-block:: python

    >>> from astroquery import alfalfa
    >>> agc = alfalfa.crossID(ra='0h8m05.63s', dec='14d50m23.3s', dr=5,
    >>>     optical_counterpart=True) 

This retrieves the AGC number of the object closest to the supplied ra and dec
(within search radius dr=5 arcseconds). The "optical_counterpart" keyword
argument above tells the crossID function to look for matches using the
positions of the optical counterparts of HI detected sources (painstakingly
determined by members of the ALFALFA team), rather than their radio centroids.
The AGC number is an identification number for objects in the ALFALFA survey,
and once we know it, we can download spectra (if they are available) easily,

.. code-block:: python

    >>> sp = alfalfa.get_spectrum(agc)

This returns a simple object which gives users access to the spectrum's FITS
file, and contains a few convenience properties to access the data quickly.
For example, we can access the frequency / velocity axis and the data
respectively via

.. code-block:: python

    >>> sp.freq, sp.varr, sp.data

Reference/API
=============

.. automodapi:: astroquery.alfalfa
    :no-inheritance-diagram:
