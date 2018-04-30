
.. doctest-skip-all
.. _astroquery.cds:

**********************************
CDS MOC Service (`astroquery.cds`)
**********************************

Getting started
===============

This module provides a python interface for querying the MOC service from the `Centre de Données de Strasbourg` (CDS).
The CDS MOC service is available at : http://alasky.unistra.fr/MocServer/query

The CDS MOC Server tool aims at retrieving as fast as possible the list of astronomical data sets
(catalogs, surveys, ...) having at least one observation in a specifical sky region.
The default result is an ID list but one can ask for different output formats :

* The number of the data sets.
* A dictionary containing the lists of meta-data for all the resulting data sets. These lists of meta-data are each indexed by the ID of the data set they are referring to.
* A MOC resulting from the union/intersection of all the MOC of the resulting data sets.
* An ID list (default result).

MOC Server is based on Multi-Order Coverage maps (MOC) described in the IVOA REC standard.

The CDS MOC Server tool contains a list of meta-data and a MOC for approx ~20000 data sets (catalogs, surveys, ...).
When requesting for the data sets having at least one observation in a sky region, the CDS MOC Server does the following:

1. The sky region (cone, polygon, MOC) is converted into a MOC at the order 29 (max order)
2. For each of the 20000 data sets, the MOC server performs the intersection of the MOC from the data set with the one defined at the past step.
3. The data sets matching the query are those giving a non-empty MOC intersection.
   
In addition to filtering astronomical data sets with a specifical sky region, it is also possible to search for data sets having a specifical set of meta-data. For instance, one can ask for the data sets covering at least 50% of the sky (moc_sky_fraction meta-data >= 50%). Examples of meta-data (or data set properties) are listed here : http://alasky.unistra.fr/MocServer/query?get=example&fmt=ascii

Requirements
----------------------------------------------------
The following packages are required for the use of the ``cds``:

* mocpy : https://github.com/cds-astro/mocpy
* pyvo : https://pyvo.readthedocs.io/en/latest/

Examples
========

.. include:: cone_search_query.rst
.. include:: complex_query.rst

Reference/API
=============

.. automodapi:: astroquery.cds
    :no-inheritance-diagram:
