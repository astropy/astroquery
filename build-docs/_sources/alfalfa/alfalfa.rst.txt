.. _astroquery.alfalfa:

ALFALFA Queries (`astroquery.alfalfa`)
======================================

Getting started
---------------

This example shows how to perform an object cross-ID with ALFALFA. We'll start
with the position of a source that exists in another survey (same object we
used in the SDSS example).

.. doctest-remote-data::

    >>> from astroquery.alfalfa import Alfalfa
    >>> from astropy import coordinates as coords
    >>> pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s')
    >>> agc = Alfalfa.query_region(pos, optical_counterpart=True)
    >>> agc
    100051

This retrieves the AGC number of the object closest to the supplied ra and dec
(within search radius dr=3 arcminutes by default). The "optical_counterpart" keyword
argument above tells the crossID function to look for matches using the
positions of the optical counterparts of HI detected sources (painstakingly
determined by members of the ALFALFA team), rather than their radio centroids.

If we want to have a look at the entire ALFALFA catalog as a dictionary, we can do that too:

.. doctest-remote-data::

    >>> cat = Alfalfa.get_catalog()
    >>> cat.keys()
    dict_keys(['AGCNr', 'Name', 'RAdeg_HI', 'Decdeg_HI', 'RAdeg_OC', 'DECdeg_OC', 'Vhelio', 'W50', 'errW50', 'HIflux', 'errflux', 'SNR', 'RMS', 'Dist', 'logMsun', 'HIcode', 'OCcode', 'NoteFlag'])

which returns a dictionary containing HI measurements for nearly 16,000
objects.


Reference/API
-------------

.. automodapi:: astroquery.alfalfa
    :no-inheritance-diagram:
