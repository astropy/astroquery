.. _astroquery.magpis:

*****************************************
MAGPIS Queries (`astroquery.magpis`)
*****************************************

Getting started
===============

The following example illustrates a MAGPIS image query::

    >>> from astroquery import magpis
    >>> fitsfile = magpis.get_magpis_image_gal(10.5,0.0)
    >>> fitsfile = magpis.get_magpis_image_gal(10.5,0.0,survey='gpsmsx')


Reference/API
=============

.. automodapi:: astroquery.magpis
    :no-inheritance-diagram:
