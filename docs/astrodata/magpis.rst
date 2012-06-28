.. _astrodata.magpis:

*****************************************
MAGPIS Queries (`astrodata.magpis`)
*****************************************

Getting started
===============

The following example illustrates a MAGPIS image query::

    >>> from astrodata import magpis
    >>> fitsfile = magpis.get_magpis_image_gal(10.5,0.0)
    >>> fitsfile = magpis.get_magpis_image_gal(10.5,0.0,survey='gpsmsx')


Reference/API
=============

.. automodapi:: astrodata.magpis
    :no-inheritance-diagram:
