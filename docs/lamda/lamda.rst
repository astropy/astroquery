.. _astroquery.lamda:

**********************************
LAMDA Queries (`astroquery.lamda`)
**********************************

Getting started
===============

The Leiden Atomic and Molecular Database (LAMDA_) stores information for energy
levels, radiative transitions, and collisional rates for many astrophysically
relevant atoms and molecules. To print the list of available molecules for
query, use:

.. doctest-remote-data::

    >>> from astroquery.lamda import Lamda
    >>> Lamda.molecule_dict  # doctest: +IGNORE_OUTPUT
    {'catom': 'http://home.strw.leidenuniv.nl/~moldata/datafiles/catom.dat',
    'c+': 'http://home.strw.leidenuniv.nl/~moldata/datafiles/c+.dat',
    'c+@uv': 'http://home.strw.leidenuniv.nl/~moldata/datafiles/c+@uv.dat',
    ...
    'o-nh2d': 'http://home.strw.leidenuniv.nl/~moldata/datafiles/o-nh2d.dat'}

The dictionary is created dynamically from the LAMDA website the first time it
is called, then cached for future use.  If there has been an update and you
want to reload the cache, clear the cache and remove the molecule dictionary as follows:

.. doctest-skip::

    >>> from astroquery.lamda import Lamda
    >>> import os
    ...
    >>> Lamda.clear_cache()
    >>> os.remove(Lamda.moldict_path)

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.

You can query for any molecule in that dictionary.

.. doctest-remote-data::

    >>> collrates, radtransitions, enlevels = Lamda.query(mol='co')

Catalogs are returned as `~astropy.table.Table` instances, except for
``collrates``, which is a dictionary of tables, with one table for each
collisional partner.


Reference/API
=============

.. automodapi:: astroquery.lamda
    :no-inheritance-diagram:

.. _LAMDA: https://home.strw.leidenuniv.nl/~moldata/
