.. doctest-skip-all

.. _astroquery.alfalfa:

ALFALFA Queries (`astroquery.alfalfa`)
======================================

Getting started
---------------

This example shows how to perform an object cross-ID with ALFALFA. We'll start
with the position of a source that exists in another survey (same object we
used in the SDSS example).

.. code-block:: python

    >>> from astroquery.alfalfa import Alfalfa
    >>> from astropy import coordinates as coords
    >>> pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s')
    >>> agc = Alfalfa.query_region(pos, optical_counterpart=True)

This retrieves the AGC number of the object closest to the supplied ra and dec
(within search radius dr=3 arcminutes by default). The "optical_counterpart" keyword
argument above tells the crossID function to look for matches using the
positions of the optical counterparts of HI detected sources (painstakingly
determined by members of the ALFALFA team), rather than their radio centroids.
The AGC number is an identification number for objects in the ALFALFA survey,
and once we know it, we can download spectra (if they are available) easily,

.. code-block:: python

    >>> sp = Alfalfa.get_spectrum(agc)

This returns a PyFITS HDUList object.  If we want to have a look at the entire ALFALFA catalog, we can do that too:

.. code-block:: python

    >>> cat = Alfalfa.get_catalog()

which returns a dictionary containing HI measurements for nearly 16,000
objects.

Reference/API
-------------

.. automodapi:: astroquery.alfalfa
    :no-inheritance-diagram:
