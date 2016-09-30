.. doctest-skip-all

.. _astroquery.esasky:

************************************
ESASky Queries (`astroquery.esasky`)
************************************

Getting started
===============

This is a python interface for querying the ESASky web service. This supports
querying an object as well as querying a region around the target. For region
queries, the region dimensions may be specified as a
radius. The queries may be further constrained by specifying 
a choice of catalogs or missions.

Get the available catalog names
-------------------

If you know the names of all the available catalogs you can use
:meth:`~astroquery.esasky.ESASkyClass.list_catalogs`:

.. code-block:: python

    >>> catalog_list = ESASky.list_catalogs()
    >>> print(catalog_list)
		['INTEGRAL', 'XMM-EPIC', 'XMM-OM', 'XMM-SLEW', 'Tycho-2', 
		'Gaia DR1 TGAS', 'Hipparcos-2', 'HSC', 'Planck-PGCC2', 'Planck-PCCS2E', 
		'Planck-PCCS2-HFI', 'Planck-PCCS2-LFI', 'Planck-PSZ']

Get the available maps mission names
-------------------

If you know the names of all the available maps missions you can use
:meth:`~astroquery.esasky.ESASkyClass.list_maps`:

.. code-block:: python

    >>> maps_list = ESASky.list_maps()
    >>> print(maps_list)
    	['INTEGRAL', 'XMM-EPIC', 'SUZAKU', 'XMM-OM-OPTICAL', 'XMM-OM-UV', 
    	'HST', 'Herschel', 'ISO']

Query an object
---------------

There are two query objects methods in this module query_object_catalogs
and query_object_maps. They both work in exactly the same way except 
that one has catalogs as input and output and the other one has mission
names and observations as input and output.

For instance to query an object around M51 in the integral catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
	>>> import astropy.units as u
    >>> result = ESASky.query_object_catalogs("M51", "integral")

Note that the catalog may also be specified as a list. 
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_object_catalogs("M51", ["integral", "XMM-OM"])

To search in all available catalogs you can write "all" instead of a catalog name.
The same thing will happen if you don't write any catalog name.

.. code-block:: python
    >>> result = ESASky.query_object_catalogs("M51", "all")
    >>> result = ESASky.query_object_catalogs("M51")

To see the result:

.. code-block:: python

    >>> print(result)
	TableList with 4 tables:
		'0:XMM-EPIC' with 4 column(s) and 3 row(s) 
		'1:HSC' with 8 column(s) and 2000 row(s) 
		'2:XMM-OM' with 12 column(s) and 220 row(s) 
		'3:PLANCK-PCCS2-HFI' with 8 column(s) and 1 row(s) 

All the results are returned as a `astroquery.utils.TableList` object. This is a container for
`~astropy.table.Table` objects. It is basically an extension to
`collections.OrderedDict` for storing a `~astropy.table.Table` against its
name.

To access an individual table from the `astroquery.utils.TableList` object

.. code-block:: python

    >>> interesting_table = result['PLANCK-PCCS2-HFI']
    >>> print(interesting_table)
	          name              ra [1]       dec [1]   
	----------------------- ------------- -------------
	PCCS2 217 G104.83+68.55 202.485459453 47.2001843799

To do some common processing to all the tables in the returned `astroquery.utils.TableList`
object, do just what you would do for a python dictionary:

.. code-block:: python

    >>> for table_name in result.keys():
    ...     table = result[table_name]
    ...     # table is now an `astropy.table.Table` object
    ...     # some code to apply on table

As mentioned earlier, query_object_maps works extremely similar.
To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_object_maps("M51", "all")

The parameters are interchangeable in the same way as in query_object_catalogs 

Query a region
--------------
The region queries work in a similar way as query_object, except that you must choose a 
radius as well. There are two query region methods in this module 
query_region_catalogs and query_region_maps.

To query a region either the coordinates or the object name around which to
query should be specified along with the value for the radius
of the region. For instance to query region around M51 in the integral catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
	>>> import astropy.units as u
    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, "integral")

Note that the catalog may also be specified as a list. 
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, ["integral", "XMM-OM"])

To search in all available catalogs you can write "all" instead of a catalog name.
The same thing will happen if you don't write any catalog name.

.. code-block:: python
    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, "all")
    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin)

In the same manner, the radius can be specified with either
a string or any `~astropy.units.Quantity`

.. code-block:: python

    >>> result = ESASKY.query_region_catalogs("M51", "10 arcmin")

To see the result:

.. code-block:: python

    >>> print(result)
	TableList with 4 tables:
		'0:XMM-EPIC' with 4 column(s) and 3 row(s) 
		'1:HSC' with 8 column(s) and 2000 row(s) 
		'2:XMM-OM' with 12 column(s) and 220 row(s) 
		'3:PLANCK-PCCS2-HFI' with 8 column(s) and 1 row(s) 

As mentioned earlier, query_region_maps works extremely similar.
To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_region_maps("M51", 10 * u.arcmin, "all")

The parameters are interchangeable in the same way as in query_region_catalogs 

Reference/API
=============

.. automodapi:: astroquery.esasky
    :no-inheritance-diagram:
