.. _astroquery.nrao:

**********************************
LAMDA Queries (`astroquery.lamda`)
**********************************

Getting started
===============

The Leiden Atomic and Molecular Database (LAMDA_) stores information for energy
levels, radiative transitions, and collisional rates for many astrophysically
relevant atoms and molecules. To print the list of available molecules for
query, use:
.. _LAMDA: http://home.strw.leidenuniv.nl/~moldata/

.. code-block:: python

    >>> from astroquery import lamda
    >>> lamda.print_mols()

A query type must be specified among `'erg_levels'` for energy levels,
`'rad_trans'` for radiative transitions, or `'coll_rates'` for collisional
rates. Example queries are show below:

.. code-block:: python

    >>> erg_t = lamda.query(mol='co', query_type='erg_levels')
    >>> rdt_t = lamda.query(mol='co', query_type='rad_trans')
    >>> clr_t = lamda.query(mol='co', query_type='coll_rates')

Catalogs are returned as `astropy.table.Table` instances. Often molecules have
collisional rates calculate for more than one collisional partner, specify the
order of the partner in the datafile using the `coll_partner_index` parameter:

.. code-block:: python

    >>> clr_t0 = lamda.query(mol='co', query_type='coll_rates', coll_partner_index=0)
    >>> clr_t1 = lamda.query(mol='co', query_type='coll_rates', coll_partner_index=1)

Reference/API
=============

.. automodapi:: astroquery.lamda
    :no-inheritance-diagram:
