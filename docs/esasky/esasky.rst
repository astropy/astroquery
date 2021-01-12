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
by specifying a choice of catalogs, missions, or spectra.  `Documentation on the ESASky
web service can be found here. <http://www.cosmos.esa.int/web/esdc/esasky-help>`__

Get the available catalog names
-------------------------------

If you know the names of all the available catalogs you can use
:meth:`~astroquery.esasky.ESASkyClass.list_catalogs`:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> catalog_list = ESASky.list_catalogs()
    >>> print(catalog_list)
    ['LAMOST', 'AllWise', 'AKARI-IRC-SC', 'TwoMASS', 'INTEGRAL',
    'CHANDRA-SC2', 'XMM-EPIC-STACK', 'XMM-EPIC', 'XMM-OM', 'XMM-SLEW',
    'Tycho-2', 'Gaia-eDR3', 'Hipparcos-2', 'HSC', 'Herschel-HPPSC-070',
    'Herschel-HPPSC-100', 'Herschel-HPPSC-160', 'Herschel-SPSC-250',
    'Herschel-SPSC-350', 'Herschel-SPSC-500', 'Planck-PGCC',
    'Planck-PCCS2E-HFI', 'Planck-PCCS2-HFI', 'Planck-PCCS2-LFI',
    'Planck-PSZ2']

Get the available maps mission names
------------------------------------

If you know the names of all the available maps missions you can use
:meth:`~astroquery.esasky.ESASkyClass.list_maps`:

.. code-block:: python

    >>> maps_list = ESASky.list_maps()
    >>> print(maps_list)
    ['INTEGRAL', 'XMM', 'Chandra', 'SUZAKU', 'XMM-OM-OPTICAL',
    'XMM-OM-UV', 'HST-UV', 'HST-OPTICAL', 'HST-IR', 'ISO-IR',
    'Herschel', 'AKARI', 'Spitzer', 'ALMA']

Get the available maps mission names
------------------------------------

If you know the names of all the available spectra you can use
:meth:`~astroquery.esasky.ESASkyClass.list_spectra`:

.. code-block:: python

    >>> spectra_list = ESASky.list_spectra()
    >>> print(spectra_list)
    ['XMM-NEWTON', 'Chandra', 'IUE', 'HST-UV',
    'HST-OPTICAL', 'HST-IR', 'ISO-IR', 'Herschel', 'LAMOST']

Query an object
---------------

There are three query objects methods in this module
:meth:`~astroquery.esasky.ESASkyClass.query_object_catalogs`,
:meth:`~astroquery.esasky.ESASkyClass.query_object_maps`, and
:meth:`~astroquery.esasky.ESASkyClass.query_object_spectra`, which all work in
almost the same way.

For catalogs, the query returns a maximum of 10000 sources per mission by
default. However, this can be modified by the row_limit parameter.
You can set the parameter to -1, which will result in the maximum number of
sources (currently 100 000).
To account for observation errors, this method will search for any sources
within 5 arcsec from the object.

For instance to query an object around M51 in the Hubble catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> result = ESASky.query_object_catalogs("M51", "HSC")

Note that the catalog may also be specified as a list.
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_object_catalogs("M51", ["HSC", "XMM-OM"])

To search in all available catalogs you can write ``"all"`` instead of a catalog
name. The same thing will happen if you don't write any catalog name.

.. code-block:: python

    >>> result = ESASky.query_object_catalogs("M51", "all")
    >>> result = ESASky.query_object_catalogs("M51")

To see the result:

.. code-block:: python

    >>> print(result)
    TableList with 9 tables:
        '0:ALLWISE' with 13 column(s) and 1 row(s)
        '1:TWOMASS' with 9 column(s) and 3 row(s)
        '2:CHANDRA-SC2' with 41 column(s) and 9 row(s)
        '3:XMM-EPIC-STACK' with 13 column(s) and 1 row(s)
        '4:XMM-EPIC' with 14 column(s) and 11 row(s)
        '5:XMM-OM' with 11 column(s) and 5 row(s)
        '6:HSC' with 9 column(s) and 230 row(s)
        '7:HERSCHEL-HPPSC-070' with 15 column(s) and 1 row(s)
        '8:HERSCHEL-HPPSC-100' with 15 column(s) and 1 row(s)

All the results are returned as a `~astroquery.utils.TableList` object. This is a
container for `~astropy.table.Table` objects. It is basically an extension to
`~collections.OrderedDict` for storing a `~astropy.table.Table` against its name.

To access an individual table from the `~astroquery.utils.TableList` object

.. code-block:: python

    >>> interesting_table = result['ALLWISE']
    >>> print(interesting_table)
            name             ra        dec     ... w3mpro_error w4mpro w4mpro_error
                            deg        deg     ...     mag       mag       mag
    ------------------- ----------- ---------- ... ------------ ------ ------------
    J132952.72+471142.6 202.4696996 47.1951717 ...        0.023  3.386        0.036

To do some common processing to all the tables in the returned
`~astroquery.utils.TableList` object, you can just use a for loop:

.. code-block:: python

    >>> for table in result:
    ...     colnames = table.colnames
    ...     # table is now an `astropy.table.Table` object
    ...     # some code to apply on table

As mentioned earlier, :meth:`astroquery.esasky.ESASkyClass.query_object_maps`
and :meth:`astroquery.esasky.ESASkyClass.query_object_spectra`
works extremely similar. It will return all maps or spectra that contain the chosen
object or coordinate. To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_object_maps("M51", "all")
    >>> result = ESASky.query_object_spectra("M51", "all")

The parameters are interchangeable in the same way as in :meth:`~astroquery.esasky.ESASkyClass.query_object_catalogs`.

Query a region
--------------
The region queries work in a similar way as query_object, except that you must
choose a radius as well. There are three query region methods in this module
:meth:`astroquery.esasky.ESASkyClass.query_region_catalogs`,
:meth:`astroquery.esasky.ESASkyClass.query_region_maps`, and
:meth:`astroquery.esasky.ESASkyClass.query_region_spectra`.
The row_limit parameter can be set to choose the maximum number of row to be
selected. If this parameter is not set, the method will return the first 10000
sources. You can set the parameter to -1, which will result in the maximum
number of sources (currently 100 000).

To query a region either the coordinates or the object name around which to
query should be specified along with the value for the radius of the region.
For instance to query region around M51 in the HSC catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> import astropy.units as u
    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, "HSC")

Note that the catalog may also be specified as a list.
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, ["HSC", "XMM-OM"])

To search in all available catalogs you can write ``"all"`` instead of a catalog
name. The same thing will happen if you don't write any catalog name.

.. code-block:: python

    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin, "all")
    >>> result = ESASky.query_region_catalogs("M51", 10 * u.arcmin)

In the same manner, the radius can be specified with either
a string or any `~astropy.units.Quantity`

.. code-block:: python

    >>> result = ESASky.query_region_catalogs("M51", "10 arcmin")

To see the result:

.. code-block:: python

    >>> print(result)
    TableList with 18 tables:
        '0:LAMOST' with 21 column(s) and 41 row(s)
        '1:ALLWISE' with 13 column(s) and 1762 row(s)
        '2:AKARI-IRC-SC' with 13 column(s) and 1 row(s)
        '3:TWOMASS' with 9 column(s) and 188 row(s)
        '4:CHANDRA-SC2' with 41 column(s) and 430 row(s)
        '5:XMM-EPIC-STACK' with 13 column(s) and 214 row(s)
        '6:XMM-EPIC' with 14 column(s) and 823 row(s)
        '7:XMM-OM' with 11 column(s) and 4849 row(s)
        '8:XMM-SLEW' with 9 column(s) and 2 row(s)
        '9:GAIA-EDR3' with 20 column(s) and 932 row(s)
        '10:HSC' with 9 column(s) and 10000 row(s)
        '11:HERSCHEL-HPPSC-070' with 15 column(s) and 93 row(s)
        '12:HERSCHEL-HPPSC-100' with 15 column(s) and 122 row(s)
        '13:HERSCHEL-HPPSC-160' with 15 column(s) and 93 row(s)
        '14:HERSCHEL-SPSC-250' with 16 column(s) and 59 row(s)
        '15:HERSCHEL-SPSC-350' with 16 column(s) and 24 row(s)
        '16:HERSCHEL-SPSC-500' with 16 column(s) and 7 row(s)
        '17:PLANCK-PCCS2-HFI' with 8 column(s) and 8 row(s)

You can use, :meth:`~astroquery.esasky.ESASkyClass.query_region_maps`
and :meth:`~astroquery.esasky.ESASkyClass.query_region_maps` with the same parameters.
To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_region_maps("M51", 10 * u.arcmin, "all")
    >>> result = ESASky.query_region_spectra("M51", 10 * u.arcmin, "all")

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
    ...                            missions=['Herschel', 'ISO-IR'])
    Starting download of HERSCHEL data. (25 files)
    Downloading Observation ID: 1342188589 from http://archives.esac.esa.int/hsa/whsa-tap-server/data?RETRIEVAL_TYPE=STANDALONE&observation_oid=8618001&DATA_RETRIEVAL_ORIGIN=UI [Done]
    Downloading Observation ID: 1342188328 from http://archives.esac.esa.int/hsa/whsa-tap-server/data?RETRIEVAL_TYPE=STANDALONE&observation_oid=8637833&DATA_RETRIEVAL_ORIGIN=UI
    ...

    >>> print(images)
    {
    'HERSCHEL': [{'70': [HDUList], '160': HDUList}, {'70': HDUList, '160': HDUList}, ...],
    'ISO' : [HDUList, HDUList, HDUList, HDUList, ...]
    ...
    }

Note that the fits files also are stored to disk. By default they are saved to
the working directory but the location can be chosen by the download_dir
parameter:

.. code-block:: python

    >>> images = ESASky.get_images("m51", radius="20 arcmin",
    ...                            missions=['Herschel', 'ISO-IR'],
    ...                            download_dir="/home/user/esasky")

Get maps
--------

You can also fetch images using :meth:`astroquery.esasky.ESASkyClass.get_maps`.
It works exactly as :meth:`astroquery.esasky.ESASkyClass.get_images` except that
it takes a `~astroquery.utils.TableList` instead of position, radius and missions.

.. code-block:: python

    >>> table_list = ESASky.query_region_maps("m51", radius="20 arcmin",
    ...                                       missions=['Herschel', 'ISO-IR'])
    >>> images = ESASky.get_maps(table_list, download_dir="/home/user/esasky")

This example is equivalent to:

.. code-block:: python

    >>> images = ESASky.get_images("m51", radius="20 arcmin",
    ...                            missions=['Herschel', 'ISO-IR'],
    ...                            download_dir="/home/user/esasky")


Get spectra
-----------
There are also two methods to download spectra:
:meth:`astroquery.esasky.ESASkyClass.get_spectra` and
:meth:`astroquery.esasky.ESASkyClass.get_spectra_from_table`.
These two methods use the same parameters as
:meth:`astroquery.esasky.ESASkyClass.get_maps`
and :meth:`astroquery.esasky.ESASkyClass.get_images` respectively.

The methods returns a `dict` to separate the different
missions. All mission except Herschel returns a list of
`~astropy.io.fits.HDUList`. Herschel returns a
three-level dictionary.

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> spectra = ESASky.get_spectra("m51", radius="20 arcmin",
    ...                            missions=['Herschel', 'XMM-NEWTON'])

or

.. code-block:: python

    >>> table_list = ESASky.query_region_spectra("m51", radius="20 arcmin",
    ...                                       missions=['Herschel', 'XMM-NEWTON'])
    >>> spectra = ESASky.get_spectra_from_table(table_list, download_dir="/home/user/esasky")

The response is structured in a dictionary like this:

.. code-block:: python

    dict: {
    'HERSCHEL': {'1342211195': {'red' : {'HPSTBRRS' : HDUList}, 'blue' : {'HPSTBRBS': HDUList},
        '1342180796': {'WBS' : {'WBS-H_LSB_5a' : HDUList}, 'HRS' : {'HRS-H_LSB_5a': HDUList},
        ...},
    'HST-IR':[HDUList, HDUList, HDUList, HDUList, HDUList, ...],
    'XMM-NEWTON' : [HDUList, HDUList, HDUList, HDUList, ...]
    ...
    }

Here is another example for Herschel, since it is a bit special:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> result = ESASky.query_region_spectra(position='M51', radius='1arcmin', missions=['HERSCHEL'])
    >>> herschel_result = result['HERSCHEL']
    >>> herschel_result['observation_id', 'target_name', 'instrument', 'observing_mode_name', 'band', 'duration'].pprint()
    >>> spectra = ESASky.get_spectra_from_table([('HERSCHEL', herschel_result)], download_dir='Spectra_new')
    >>> spectra['HERSCHEL']['1342211195']['red'].keys()
    >>> spectra['HERSCHEL']['1342211195']['red']['HPSTBRRS'].info()

Reference/API
=============

.. automodapi:: astroquery.esasky
    :no-inheritance-diagram:
