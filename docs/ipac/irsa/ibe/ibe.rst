.. doctest-skip-all

.. _astroquery.ipac.irsa.ibe:

******************************************************************************
IRSA Image Server program interface (IBE) Queries (`astroquery.ipac.irsa.ibe`)
******************************************************************************


This module can has methods to perform different types of queries on the
catalogs present in the IRSA Image Server program interface (IBE), which
currently provides access to the 2MASS, WISE, and PTF image archives. In
addition to supporting the standard query methods
:meth:`~astroquery.ipac.irsa.ibe.IbeClass.query_region` and
:meth:`~astroquery.ipac.irsa.ibe.IbeClass.query_region_async`, there are also methods to
query the available missions (:meth:`~astroquery.ipac.irsa.ibe.IbeClass.list_missions`), datasets (:meth:`~astroquery.ipac.irsa.ibe.IbeClass.list_datasets`), tables (:meth:`~astroquery.ipac.irsa.ibe.IbeClass.list_tables`), and columns (:meth:`~astroquery.ipac.irsa.ibe.IbeClass.get_columns`).


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.ipac.irsa.ibe import Ibe
    >>> Ibe.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.ipac.irsa.ibe
    :no-inheritance-diagram:
