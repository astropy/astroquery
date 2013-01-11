.. _astroquery.nrao:

*****************************************
NRAO Queries (`astroquery.nrao`)
*****************************************

Getting started
===============

The following example illustrates an NRAO VLA archive image query

.. code-block:: python
    >>> from astroquery import nrao
    >>> fitsfiles = nrao.get_nrao_image(10.5,0.0)

fitsfiles will be a list of FITS HDUs downloaded from the archive.  You can
specify a band and you can query in other coordinates; the default is galactic.


Reference/API
=============

.. automodapi:: astroquery.nrao
    :no-inheritance-diagram:
