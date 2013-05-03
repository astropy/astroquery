.. _astroquery.ukidss:

*****************************************
UKIDSS Queries (`astroquery.ukidss`)
*****************************************

Getting started
===============

The following example illustrates an UKIDSS catalog/image query

.. code-block:: python

    >>> from astroquery import ukidss
    >>> Q = ukidss.UKIDSSQuery()
    >>> fitsfile = Q.get_image_gal(10.5,0.0)
    >>> fitsfile = Q.get_image_gal(10.5,0.0)
    >>> data = Q.get_catalog_gal(10.625,-0.38,radius=0.1)
    >>> bintable = data[0][1]


Reference/API
=============

.. automodapi:: astroquery.ukidss
    :no-inheritance-diagram:
