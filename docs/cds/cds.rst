
.. doctest-skip-all
.. _astroquery.cds:


**********************************
CDS MOC Service (`astroquery.cds`)
**********************************

Getting started
===============

This module provides a python interface for querying the `CDS MOC Service`_ from the `Centre de Données de Strasbourg (CDS)`_.

The `CDS MOC Server`_ tool aims at retrieving as fast as possible the list of astronomical data sets
(catalogs, surveys, ...) having at least one observation in a specific sky region.
The default result is an ID list but one can ask for different output formats such as:

* The number of the data sets.
* A dictionary containing the lists of meta data for all the resulting data sets. These lists of meta data are each indexed by the ID of the data set they are referring to.
* A MOC resulting from the union/intersection of all the MOCs of the resulting data sets.
* An ID list of data sets (default result).

`CDS MOC Server`_ is based on Multi-Order Coverage maps (MOC) described in the `IVOA REC standard`_.

The `CDS MOC Server`_ tool contains a list of meta data and MOC for approx ~20000 data sets.
When requesting for the data sets having at least one observation in a sky region, the `CDS MOC Server`_ does the following:

1. The sky region from the user (cone, polygon, MOC) is converted into a MOC
2. For each of the 20000 data sets, the MOC server performs the intersection of the MOC from the data set with the one defined at the past step.
3. The data sets matching the query are those giving a non-empty MOC intersection.
   
In addition to filtering astronomical data sets with a specific sky region, it is also possible to search for data sets having a specific set of meta data.
For instance, one can ask for the data sets covering at least 50% of the sky (the ``moc_sky_fraction`` meta data of the selected data sets must be >= 50%).
Examples of meta data (equally, another used term is data set properties) are listed `here <http://alasky.unistra.fr/MocServer/query?get=example&fmt=ascii>`_


Requirements
----------------------------------------------------
The following packages are required for the use of the ``cds``:

* `mocpy`_
* `pyvo`_

Examples
========

.. include:: cone_search_query.rst
.. include:: complex_query.rst

Reference/API
=============

.. automodapi:: astroquery.cds
    :no-inheritance-diagram:
    :skip: Constrains, PropertyConstrain
    :skip: OutputFormat

.. :include:: references.rst
