.. doctest-skip-all

.. _astroquery.esasky:

************************************
ESASky Queries (`astroquery.esasky`)
************************************

Getting started
===============

This is a python interface for querying the `ESASky web service
<http://www.cosmos.esa.int/web/esdc/esasky>`__. This supports querying an object
as well as querying a region around the target. For region queries, the region
dimensions may be specified as a radius. The queries may be further constrained
by specifying a choice of catalogs or missions.  `Documentation on the ESASky
web service can be found here. <http://www.cosmos.esa.int/web/esdc/esasky-help>`__

Get the available catalog names
-------------------------------

If you know the names of all the available catalogs you can use
:meth:`~astroquery.esasky.ESASkyClass.list_catalogs`:

.. code-block:: python

    >>> catalog_list = ESASky.list_catalogs()
    >>> print(catalog_list)
    ['INTEGRAL', 'XMM-EPIC', 'XMM-OM', 'XMM-SLEW', 'Tycho-2', 
    'Gaia DR1 TGAS', 'Hipparcos-2', 'HSC', 'Planck-PGCC2', 'Planck-PCCS2E', 
    'Planck-PCCS2-HFI', 'Planck-PCCS2-LFI', 'Planck-PSZ']

Get the available maps mission names
------------------------------------

If you know the names of all the available maps missions you can use
:meth:`~astroquery.esasky.ESASkyClass.list_maps`:

.. code-block:: python

    >>> maps_list = ESASky.list_maps()
    >>> print(maps_list)
    ['INTEGRAL', 'XMM-EPIC', 'SUZAKU', 'XMM-OM-OPTICAL', 'XMM-OM-UV', 
    'HST', 'Herschel', 'ISO']

Query an object
---------------

There are two query objects methods in this module 
:meth:`~astroquery.esasky.ESASkyClass.query_object_catalogs` and 
:meth:`~astroquery.esasky.ESASkyClass.query_object_maps`. They both work in 
almost the same way except that one has catalogs as input and output and the 
other one has mission names and observations as input and output. 

For catalogs, the query returns a maximum of 2000 sources per mission.
To account for observation errors, this method will search for any sources
within 5 arcsec from the object. 

For instance to query an object around M51 in the integral catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> result = ESASky.query_object_catalogs("M51", "integral")

Note that the catalog may also be specified as a list. 
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_object_catalogs("M51", ["integral", "XMM-OM"])

To search in all available catalogs you can write ``"all"`` instead of a catalog 
name. The same thing will happen if you don't write any catalog name.

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

All the results are returned as a `astroquery.utils.TableList` object. This is a 
container for `~astropy.table.Table` objects. It is basically an extension to
`collections.OrderedDict` for storing a `~astropy.table.Table` against its name.

To access an individual table from the `astroquery.utils.TableList` object

.. code-block:: python

    >>> interesting_table = result['PLANCK-PCCS2-HFI']
    >>> print(interesting_table)
              name              ra [1]       dec [1]   
    ----------------------- ------------- -------------
    PCCS2 217 G104.83+68.55 202.485459453 47.2001843799

To do some common processing to all the tables in the returned 
`astroquery.utils.TableList` object, do just what you would do for a python 
dictionary:

.. code-block:: python

    >>> for table_name in result:
    ...     table = result[table_name]
    ...     # table is now an `astropy.table.Table` object
    ...     # some code to apply on table

As mentioned earlier, :meth:`astroquery.esasky.ESASkyClass.query_object_maps` 
works extremely similar. It will return all maps that contain the chosen object 
or coordinate. To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_object_maps("M51", "all")

The parameters are interchangeable in the same way as in :meth:`~astroquery.esasky.ESASkyClass.query_object_catalogs`.

Query a region
--------------
The region queries work in a similar way as query_object, except that you must 
choose a radius as well. There are two query region methods in this module:
:meth:`~astroquery.esasky.ESASkyClass.query_region_catalogs` and 
:meth:`~astroquery.esasky.ESASkyClass.query_region_maps`. 
The query returns a maximum of 2000 sources per mission.

To query a region either the coordinates or the object name around which to
query should be specified along with the value for the radius of the region. 
For instance to query region around M51 in the integral catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> import astropy.units as u
    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, "integral")

Note that the catalog may also be specified as a list. 
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, ["integral", "XMM-OM"])

To search in all available catalogs you can write ``"all"`` instead of a catalog 
name. The same thing will happen if you don't write any catalog name.

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

As mentioned earlier, :meth:`~astroquery.esasky.ESASkyClass.query_region_maps` works extremely similar.
To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_region_maps("M51", 10 * u.arcmin, "all")

The parameters are interchangeable in the same way as in
:meth:`~astroquery.esasky.ESASkyClass.query_region_catalogs`.

Get images
----------

You can fetch images around the specified target or coordinates. When a target
name is used rather than the coordinates, this will be resolved to coordinates
using astropy name resolving methods that utilize online services like
SESAME. Coordinates may be entered using the suitable object from
`astropy.coordinates`. 

The method returns a `dict` to separate the different
missions. All mission except Herschel returns a list of 
`~astropy.io.fits.HDUList`. For Herschel each item in the list is a 
dictionary where the used filter is the key and the HDUList is the value.

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> images = ESASky.get_images("m51", radius="20 arcmin",
    ...                            missions=['Herschel', 'XMM-EPIC'])

    Starting download of HERSCHEL data. (12 files)
    Downloading Observation ID: 1342183910 from http://archives.esac.esa.int/hsa/aio/jsp/standaloneproduct.jsp?RETRIEVAL_TYPE=STANDALONE&OBSERVATION.OBSERVATION_ID=1342183910&OBSERVING_MODE.OBSERVING_MODE_NAME=PacsPhoto&INSTRUMENT.INSTRUMENT_NAME=PACS [Done]
    Downloading Observation ID: 1342183907 from http://archives.esac.esa.int/hsa/aio/jsp/standaloneproduct.jsp?RETRIEVAL_TYPE=STANDALONE&OBSERVATION.OBSERVATION_ID=1342183907&OBSERVING_MODE.OBSERVING_MODE_NAME=PacsPhoto&INSTRUMENT.INSTRUMENT_NAME=PACS [Done]
    ...
    
    >>> print(images)
    {
    'HERSCHEL': [{'70': [HDUList], ' 160': [HDUList]}, {'70': [HDUList], ' 160': [HDUList]}, ...],
    'XMM-EPIC' : [HDUList], HDUList], HDUList], HDUList], ...]
    ...
    }

Note that the fits files also are stored to disk. By default they are saved to 
the working directory but the location can be chosen by the download_dir 
parameter:

.. code-block:: python

    >>> images = ESASky.get_images("m51", radius="20 arcmin",
    ...                            missions=['Herschel', 'XMM-EPIC'],
    ...                            download_dir="/home/user/esasky")

Get maps
--------

You can also fetch images using :meth:`astroquery.esasky.ESASkyClass.get_maps`. 
It works exactly as :meth:`astroquery.esasky.ESASkyClass.get_images` except that 
it takes a `~astroquery.utils.TableList` instead of position, radius and missions. 

.. code-block:: python

    >>> table_list = ESASky.query_region_maps("m51", radius="20 arcmin",
    ...                                       missions=['Herschel', 'XMM-EPIC'])
    >>> images = ESASky.get_maps(table_list, download_dir="/home/user/esasky")

This example is equivalent to:

.. code-block:: python

    >>> images = ESASky.get_images("m51", radius="20 arcmin",
    ...                            missions=['Herschel', 'XMM-EPIC'],
    ...                            download_dir="/home/user/esasky")


Reference/API
=============

.. automodapi:: astroquery.esasky
    :no-inheritance-diagram:
