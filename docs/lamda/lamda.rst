.. doctest-skip-all

**********************************
LAMDA Queries (`astroquery.lamda`)
**********************************

Getting started
===============

The Leiden Atomic and Molecular Database (LAMDA_) stores information for energy
levels, radiative transitions, and collisional rates for many astrophysically
relevant atoms and molecules. To print the list of available molecules for
query, use:

.. code-block:: python

    >>> from astroquery.lamda import Lamda
    >>> lamda.molecule_dict

The dictionary is created dynamically from the LAMDA website the first time it
is called, then cached for future use.  If there has been an update and you
want to reload the cache, you can find the cache file `molecules.json` and
remove it:

.. code-block:: python

    >>> Lamda.cache_location
    u'/Users/your_username/.astropy/cache/astroquery/Lamda'
    >>> Lamda.moldict_path
    u'/Users/your_username/.astropy/cache/astroquery/Lamda/molecules.json'
    >>> os.remove(Lamda.moldict_path)


You can query for any molecule in that dictionary.

.. code-block:: python

    >>> collrates,radtransitions,enlevels = Lamda.query(mol='co')

Catalogs are returned as `~astropy.table.Table` instances, except for
`collrates`, which is a dictionary of tables, with one table for each
collisional partner.

Reference/API
=============

.. automodapi:: astroquery.lamda
    :no-inheritance-diagram:

.. _LAMDA: http://home.strw.leidenuniv.nl/~moldata/
