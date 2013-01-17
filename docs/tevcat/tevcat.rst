.. _astroquery.tevcat:

****************************
TeVCat (`astroquery.tevcat`)
****************************

`TeVCat <http://tevcat.uchicago.edu>`__ is an online catalog for TeV Astronomy.
It is continuously updated as new discoveries are announced.

Unfortunately the TeVCat content cannot be downloaded easily e.g. in FITS format.
This module allows you to get it as an `~astropy.table.Table` like this:

.. code-block:: python

    >>> from astroquery.tevcat import get_tevcat
    >>> table = get_tevcat()

Reference/API
=============

.. automodapi:: astroquery.tevcat
    :no-inheritance-diagram:
