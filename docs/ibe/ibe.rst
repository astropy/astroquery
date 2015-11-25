.. doctest-skip-all

.. _astroquery.ibe:

********************************************************************
IRSA Image Server program interface (IBE) Queries (`astroquery.ibe`)
********************************************************************


This module can has methods to perform different types of queries on the
catalogs present in the IRSA Image Server program interface (IBE), which
currently provides access to the 2MASS, WISE, and PTF image archives. In
addition to supporting the standard query methods
:meth:`~astroquery.ibe.IbeClass.query_region` and
:meth:`~astroquery.ibe.IbeClass.query_region_async`, there are also methods to
query the available missions (:meth:`~astroquery.ibe.IbeClass.list_missions`), datasets (:meth:`~astroquery.ibe.IbeClass.list_datasets`), tables (:meth:`~astroquery.ibe.IbeClass.list_tables`), and columns (:meth:`~astroquery.ibe.IbeClass.get_columns`).


Reference/API
=============

.. automodapi:: astroquery.ibe
    :no-inheritance-diagram:
