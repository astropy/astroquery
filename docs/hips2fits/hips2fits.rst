.. doctest-skip-all

.. _astroquery.hips2fits:

******************************************
HiPS2fits Service (`astroquery.hips2fits`)
******************************************

Getting started
===============

This module provides a python interface for querying `hips2fits`_.

This package implements two methods:

* :meth:`~astroquery.hips2fits.hips2fitsClass.query_with_wcs` retrieving data-sets (their associated MOCs and meta-datas) having sources in a given region.
* :meth:`~astroquery.hips2fits.hips2fitsClass.query_without_wcs` requesting `hips2fits`_ without providing WCS but the output image pixel size, the center of projection, the type of projection and the field of view. 

Examples
========

Reference/API
=============

.. automodapi:: astroquery.hips2fits
    :no-inheritance-diagram:


.. _hips2fits: http://alasky.u-strasbg.fr/hips-image-services/hips2fits

