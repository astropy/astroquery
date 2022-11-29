.. doctest-skip-all

.. _astroquery.esasky:

************************************
ESASky Queries (`astroquery.esasky`)
************************************

Getting started
===============

This is a python interface for querying the `ESASky web service <http://www.cosmos.esa.int/web/esdc/esasky>`__.
This module supports cone searches and download of data products from all missions available in ESASky. You can also use
the ESASky Solar System Object crossmatch methods to get all observations (both targeted and serendipitous) of a solar
system object.

There are 4 categories of methods, based on the type of data: catalogs, observations, spectra, and SSO. `Documentation
on the ESASky web service can be found here. <http://www.cosmos.esa.int/web/esdc/esasky-help>`__

Get the available catalog names
-------------------------------

If you know the names of all the available catalogs you can use :meth:`~astroquery.esasky.ESASkyClass.list_catalogs`:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> catalog_list = ESASky.list_catalogs()
    >>> print(catalog_list)
    ['LAMOST_LRS', 'LAMOST_MRS', 'AllWise', 'Spitzer', 'AKARI-IRC-SC', 'TwoMASS', 'INTEGRAL', 'CHANDRA-SC2',
    'XMM-EPIC-STACK', 'XMM-EPIC', 'XMM-OM', 'XMM-SLEW', 'Tycho-2', 'Gaia-DR3', 'Hipparcos-2',
    'HSC', 'Herschel-HPPSC-070', 'Herschel-HPPSC-100', 'Herschel-HPPSC-160', 'Herschel-SPSC-250', 'Herschel-SPSC-350',
    'Herschel-SPSC-500', 'Planck-PGCC', 'Planck-PCCS2E-HFI', 'Planck-PCCS2-HFI', 'Planck-PCCS2-LFI', 'Planck-PSZ2',
    'Icecube', 'Fermi_4FGL-DR2', 'Fermi_3FHL', 'Fermi_4LAC-DR2', '2WHSP', '2RXS', 'OU_Blazars']

Get the available maps mission names
------------------------------------

If you know the names of all the available maps missions you can use :meth:`~astroquery.esasky.ESASkyClass.list_maps`:

.. code-block:: python

    >>> maps_list = ESASky.list_maps()
    >>> print(maps_list)
    ['INTEGRAL', 'XMM', 'Chandra', 'SUZAKU', 'XMM-OM-OPTICAL', 'XMM-OM-UV', 'HST-UV', 'HST-OPTICAL', 'HST-IR', 'ISO-IR',
    'Herschel', 'AKARI', 'JWST-MID-IR', 'JWST-NEAR-IR', 'Spitzer', 'ALMA']

Get the available spectra mission names
---------------------------------------

If you know the names of all the available spectra you can use :meth:`~astroquery.esasky.ESASkyClass.list_spectra`:

.. code-block:: python

    >>> spectra_list = ESASky.list_spectra()
    >>> print(spectra_list)
    ['XMM-NEWTON', 'Chandra', 'IUE', 'HST-UV', 'HST-OPTICAL', 'JWST-MID-IR', 'JWST-NEAR-IR', 'HST-IR', 'ISO-IR',
    'Herschel', 'LAMOST_LRS', 'LAMOST_MRS', 'CHEOPS']

Get the available SSO mission names
-----------------------------------

If you know the names of all the available missions with SSO cross match data, you can use
:meth:`~astroquery.esasky.ESASkyClass.list_sso`:

.. code-block:: python

    >>> sso_list = ESASky.list_sso()
    >>> print(sso_list)
    ['Herschel', 'HST', 'XMM']

Query an object
---------------

There are three very similar query objects methods in this module
:meth:`~astroquery.esasky.ESASkyClass.query_object_catalogs`, :meth:`~astroquery.esasky.ESASkyClass.query_object_maps`,
and :meth:`~astroquery.esasky.ESASkyClass.query_object_spectra`. There is also a method for querying SSO object
:meth:`~astroquery.esasky.ESASkyClass.query_sso` which is covered in its own section further down.

For catalogs, the query returns a maximum of 10000 sources per mission by default. However, this can be modified by the
row_limit parameter. You can set the parameter to -1, which will result in the maximum number of sources (currently 100
000). To account for observation errors, this method will search for any sources within 5 arcsec from the object.

For instance to query an object around M51 in the Hubble catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> result = ESASky.query_object_catalogs(position="M51", missions="HSC")

Note that the catalog may also be specified as a list.
So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_object_catalogs(position="M51", missions=["HSC", "XMM-OM"])

To search in all available catalogs you can write ``"all"`` instead of a catalog name. The same thing will happen if you
don't write any catalog name.

.. code-block:: python

    >>> result = ESASky.query_object_catalogs(position="M51", missions="all")
    >>> result = ESASky.query_object_catalogs(position="M51")

To see the result:

.. code-block:: python

    >>> print(result)
    TableList with 9 tables:
        '0:ALLWISE' with 25 column(s) and 1 row(s)
        '1:TWOMASS' with 14 column(s) and 3 row(s)
        '2:CHANDRA-SC2' with 41 column(s) and 9 row(s)
        '3:XMM-EPIC-STACK' with 347 column(s) and 1 row(s)
        '4:XMM-EPIC' with 223 column(s) and 12 row(s)
        '5:XMM-OM' with 122 column(s) and 5 row(s)
        '6:HSC' with 27 column(s) and 230 row(s)
        '7:HERSCHEL-HPPSC-070' with 21 column(s) and 1 row(s)
        '8:HERSCHEL-HPPSC-100' with 21 column(s) and 1 row(s)

All the results are returned as a `~astroquery.utils.TableList` object. This is a container for `~astropy.table.Table`
objects. It is basically an extension to `~collections.OrderedDict` for storing a `~astropy.table.Table` against its
name.

To access an individual table from the `~astroquery.utils.TableList` object

.. code-block:: python

    >>> interesting_table = result['ALLWISE']
    >>> print(interesting_table)
            name             ra        dec     ... w3mpro_error w4mpro w4mpro_error
                            deg        deg     ...     mag       mag       mag
    ------------------- ----------- ---------- ... ------------ ------ ------------
    J132952.72+471142.6 202.4696996 47.1951717 ...        0.023  3.386        0.036

To do some common processing to all the tables in the returned `~astroquery.utils.TableList` object, you can just use a
for loop:

.. code-block:: python

    >>> for table in result:
    ...     colnames = table.colnames
    ...     # table is now an `astropy.table.Table` object
    ...     # some code to apply on table

As mentioned earlier, :meth:`astroquery.esasky.ESASkyClass.query_object_maps` and
:meth:`astroquery.esasky.ESASkyClass.query_object_spectra` works extremely similar. It will return all maps or spectra
that contain the chosen object or coordinate. To execute the same command as above you write this:

.. code-block:: python

    >>> result = ESASky.query_object_maps(position="M51", missions="all")
    >>> result = ESASky.query_object_spectra(position="M51", missions="all")

The parameters are interchangeable in the same way as in :meth:`~astroquery.esasky.ESASkyClass.query_object_catalogs`.

Query a region
--------------
The region queries work in a similar way as query_object, except that you must choose a radius as well. There are three
query region methods in this module :meth:`astroquery.esasky.ESASkyClass.query_region_catalogs`,
:meth:`astroquery.esasky.ESASkyClass.query_region_maps`, and :meth:`astroquery.esasky.ESASkyClass.query_region_spectra`.
The row_limit parameter can be set to choose the maximum number of row to be selected. If this parameter is not set, the
method will return the first 10000 sources. You can set the parameter to -1, which will result in the maximum number of
sources (currently 100 000).

To query a region either the coordinates or the object name around which to query should be specified along with the
value for the radius of the region. For instance to query region around M51 in the HSC catalog:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> import astropy.units as u
    >>> result = ESASky.query_region_catalogs(position="M51", radius=10 * u.arcmin, catalogs="HSC")

Note that the catalog may also be specified as a list. So the above query may also be written as:

.. code-block:: python

    >>> result = ESASky.query_region_catalogs(position="M51", radius=10 * u.arcmin, catalogs=["HSC", "XMM-OM"])

To search in all available catalogs you can write ``"all"`` instead of a catalog name. The same thing will happen if you
don't write any catalog name.

.. code-block:: python

    >>> result = ESASky.query_region_catalogs(position="M51", radius=10 * u.arcmin, catalogs="all")
    >>> result = ESASky.query_region_catalogs(position="M51", radius=10 * u.arcmin)

In the same manner, the radius can be specified with either a string or any `~astropy.units.Quantity`

.. code-block:: python

    >>> result = ESASky.query_region_catalogs(position="M51", radius="10 arcmin")

To see the result:

.. code-block:: python

    >>> print(result)
    TableList with 18 tables:
        '0:LAMOST_LRS' with 43 column(s) and 37 row(s)
        '1:ALLWISE' with 25 column(s) and 1762 row(s)
        '2:SPITZER' with 146 column(s) and 1082 row(s)
        '3:AKARI-IRC-SC' with 29 column(s) and 1 row(s)
        '4:TWOMASS' with 14 column(s) and 188 row(s)
        '5:CHANDRA-SC2' with 41 column(s) and 430 row(s)
        '6:XMM-EPIC-STACK' with 347 column(s) and 225 row(s)
        '7:XMM-EPIC' with 223 column(s) and 941 row(s)
        '8:XMM-OM' with 122 column(s) and 4849 row(s)
        '9:XMM-SLEW' with 106 column(s) and 2 row(s)
        '10:GAIA-DR3' with 153 column(s) and 932 row(s)
        '11:HSC' with 27 column(s) and 10000 row(s)
        '12:HERSCHEL-HPPSC-070' with 21 column(s) and 93 row(s)
        '13:HERSCHEL-HPPSC-100' with 21 column(s) and 122 row(s)
        '14:HERSCHEL-HPPSC-160' with 21 column(s) and 93 row(s)
        '15:HERSCHEL-SPSC-250' with 36 column(s) and 59 row(s)
        '16:HERSCHEL-SPSC-350' with 36 column(s) and 24 row(s)
        '17:HERSCHEL-SPSC-500' with 36 column(s) and 7 row(s)
        '18:PLANCK-PCCS2-HFI' with 9 column(s) and 8 row(s)
        '19:2RXS' with 306 column(s) and 2 row(s)

You can use, :meth:`~astroquery.esasky.ESASkyClass.query_region_maps` and
:meth:`~astroquery.esasky.ESASkyClass.query_region_maps` with the same parameters. To execute the same command as above
you write this:

.. code-block:: python

    >>> result = ESASky.query_region_maps(position="M51", radius=10 * u.arcmin, missions="all")
    >>> result = ESASky.query_region_spectra(position="M51", radius=10 * u.arcmin, missions="all")

The parameters are interchangeable in the same way as in :meth:`~astroquery.esasky.ESASkyClass.query_region_catalogs`.

Get the metadata of specific observations or sources
----------------------------------------------------
If you already know the observation ID's or source names of interest, you can get their related metadata directly with
:meth:`~astroquery.esasky.ESASkyClass.query_ids_maps`, or :meth:`~astroquery.esasky.ESASkyClass.query_ids_catalogs`, or
:meth:`~astroquery.esasky.ESASkyClass.query_ids_spectra`

.. code-block:: python

    >>> maps = ESASky.query_ids_maps(observation_ids=["lbsk03vbq", "ieag90010"], missions="HST-UV")
    >>> catalogs = ESASky.query_ids_catalogs(source_ids=["2CXO J090341.1-322609", "2CXO J090353.8-322642",
                                                         "44899", "45057"], catalogs=["CHANDRA-SC2", "Hipparcos-2"])
    >>> spectra = ESASky.query_ids_spectra(observation_ids="0001730501")

If you already know which missions you are interested in, it is recommended to explicitly mention them in the mission
parameter. Otherwise, ESASky will search through all missions for the ID's, which also works, but is a little bit
slower.

Get images
----------

You can either fetch images around the specified target or coordinates, or fetch images from a list of observation ID's.
When a target name is used rather than the coordinates, this will be resolved to coordinates using astropy name
resolving methods that utilize online services like SESAME. Coordinates may be entered using the suitable object from
`astropy.coordinates`.

The method returns a `dict` to separate the different missions. All mission except Herschel returns a list of
`~astropy.io.fits.HDUList`. For Herschel each item in the list is a dictionary where the used filter is the key and the
HDUList is the value.

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> images = ESASky.get_images(position="V* HT Aqr", radius="15 arcmin", missions=['Herschel', 'ISO-IR'])

    Starting download of HERSCHEL data. (6 files)
    Downloading Observation ID: 1342220557 from http://archives.esac.esa.int/hsa/whsa-tap-server/data?RETRIEVAL_TYPE=STANDALONE&observation_oid=8628906&DATA_RETRIEVAL_ORIGIN=UI [Done]
    Downloading Observation ID: 1342221178 from http://archives.esac.esa.int/hsa/whsa-tap-server/data?RETRIEVAL_TYPE=STANDALONE&observation_oid=8628962&DATA_RETRIEVAL_ORIGIN=UI
    ...

    >>> print(images)
    {
    'HERSCHEL': [{'70': [HDUList], '160': HDUList}, {'70': HDUList, '160': HDUList}, ...],
    'ISO-IR' : [HDUList, HDUList, HDUList, HDUList, ...]
    ...
    }

As mentioned above, you can also download a images from a list of observation ID's. To do that you just have to use the
parameter observation_id instead of target and position.

.. code-block:: python

    >>> images = ESASky.get_images(observation_ids="100001010", missions="SUZAKU")
    >>> images = ESASky.get_images(observation_ids=["100001010", "01500403"], missions=["SUZAKU", "ISO-IR"])

Note that the fits files also are stored to disk. By default they are saved to the working directory but the location
can be chosen by the download_dir parameter:

Get maps
--------

You can also fetch images using :meth:`astroquery.esasky.ESASkyClass.get_maps`. It works exactly as
:meth:`astroquery.esasky.ESASkyClass.get_images` except that it takes a `~astroquery.utils.TableList` instead of
position, radius and missions.

.. code-block:: python

    >>> table_list = ESASky.query_region_maps(position="V* HT Aqr", radius="15 arcmin", missions=['Herschel', 'ISO-IR'])
    >>> images = ESASky.get_maps(query_table_list=table_list, download_dir="/home/user/esasky")

This example is equivalent to:

.. code-block:: python

    >>> images = ESASky.get_images(position="V* HT Aqr", radius="15 arcmin", missions=['Herschel', 'ISO-IR'],
                                   download_dir="/home/user/esasky")


Get spectra
-----------
There are also two methods to download spectra: :meth:`astroquery.esasky.ESASkyClass.get_spectra` and
:meth:`astroquery.esasky.ESASkyClass.get_spectra_from_table`. These two methods use the same parameters as
:meth:`astroquery.esasky.ESASkyClass.get_maps` and :meth:`astroquery.esasky.ESASkyClass.get_images` respectively.

The methods returns a `dict` to separate the different missions. All mission except Herschel returns a list of
`~astropy.io.fits.HDUList`. Herschel returns a three-level dictionary.

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> spectra = ESASky.get_spectra(position="Gaia DR3 4512810408088819712", radius="6.52 arcmin",
                                     missions=['Herschel', 'XMM-NEWTON'])
    >>> spectra = ESASky.get_spectra(observation_ids=["02101201", "z1ax0102t"], missions=["ISO-IR", "HST-UV"])

or

.. code-block:: python

    >>> table_list = ESASky.query_region_spectra(position="Gaia DR3 4512810408088819712", radius="6.52 arcmin",
                                                 missions=['Herschel', 'XMM-NEWTON'])
    >>> spectra = ESASky.get_spectra_from_table(query_table_list=table_list, download_dir="/home/user/esasky")

The return value is structured in a dictionary like this:

.. code-block:: python

    dict: {
    'HERSCHEL': {'1342244919': {'red' : {'HPSTBRRS' : HDUList}, 'blue' : {'HPSTBRBS': HDUList},
        '1342243607': {'SSW+SLW' : {'SPSS' : HDUList},
        ...},
    'XMM-NEWTON' : [HDUList, HDUList, HDUList, HDUList, ...]
    ...
    }

Here is another example for Herschel, since it is a bit special:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> result = ESASky.query_region_spectra(position='[SMB88] 6327', radius='1 arcmin', missions=['HERSCHEL'])
    >>> herschel_result = result['HERSCHEL']
    >>> herschel_result['observation_id', 'target_name', 'instrument', 'observing_mode_name', 'band', 'duration'].pprint()
    >>> spectra = ESASky.get_spectra_from_table(query_table_list=[('HERSCHEL', herschel_result)], download_dir='Spectra_new')
    >>> spectra['HERSCHEL']['1342249066']['SSW+SLW'].keys()
    >>> spectra['HERSCHEL']['1342249066']['SSW+SLW']['SPSS'].info()

Solar System Object Crossmatch
------------------------------
ESASky has a solar system object crossmatch feature which performs a crossmatch on the SSO orbits against the entire
mission archives to find observations in which the SSO fell within the imaging instrument's field of view during the
time the images were being taken. `Read more about the ESASky SSO feature
<https://www.cosmos.esa.int/web/esdc/esasky-interface#SSO>`__ You can access the results of this crossmatch by using
:meth:`astroquery.esasky.ESASkyClass.query_sso` which works like the other query methods, but it takes an SSO name as
input instead of a position.

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> result = ESASky.query_sso(sso_name="Pallas", missions=["XMM", "HST"])

In some cases an SSO name is ambiguous, in which case you may need to use a more precise SSO name or specify the SSO
type of the desired object. For example:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> ESASky.query_sso(sso_name="503")
    INFO: Found 4 SSO's with name: 503.
    Try narrowing your search by typing a more specific sso_name.
    You can also narrow your search by specifying the sso_type.
    Allowed values are ALL, ASTEROID, COMET, SATELLITE, PLANET, DWARF_PLANET, SPACECRAFT, SPACEJUNK, EXOPLANET, STAR.
    The following SSO's were found:
    {'aliases': ['503', 'J-3', 'J-III'], 'sso_name': 'Ganymede', 'sso_type': 'SATELLITE'}
    {'aliases': [], 'sso_name': 'TOI-503 b', 'sso_type': 'EXOPLANET'}
    {'aliases': [], 'sso_name': 'Wolf 503 b', 'sso_type': 'EXOPLANET'}
    {'aliases': ['00503', '1899 GA', '1903 BL', '1948 BA', '1948 DA', '2000503', '503', 'I99G00A', 'J03B00L', 'J48B00A', 'J48D00A'], 'sso_name': 'Evelyn', 'sso_type': 'ASTEROID'}


In this case, you can specify the sso_type

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> ESASky.query_sso(sso_name="503", sso_type="SATELLITE")


You can see the available missions with:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> ESASky.list_sso()


Other parameters and the return value are structured in the same manner as the other query methods.

You can also download the observation for a given SSO with :meth:`astroquery.esasky.ESASkyClass.get_images_sso`.
This function works very similar to :meth:`astroquery.esasky.ESASkyClass.get_images` and
:meth:`astroquery.esasky.ESASkyClass.get_maps`, as it structures the return values in the same way, and most parameters
are the same. You can for example, download a table list just like in get_maps by doing something like this:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> table_list_from_query_maps=ESASky.query_sso(sso_name="ganymede", missions="XMM")
    >>> table_list_from_query_maps['XMM'].remove_rows(list(range(0, 32)))
    >>> images=ESASky.get_images_sso(table_list=table_list_from_query_maps)

Or download everything on an SSO by something like this:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> images=ESASky.get_images_sso(sso_name="2017 RN65")


This module also offers access to IMCCE's SsODNet resolver, which allows you to find solar and extra solar system
objects with a given name. Here you can see all matches and there aliases and types. You can use this method to help you
specify which SSO you are after. Use :meth:`astroquery.esasky.ESASkyClass.find_sso` like this:

.. code-block:: python

    >>> from astroquery.esasky import ESASky
    >>> list_of_matches=ESASky.find_sso(sso_name="Io")


Reference/API
=============

.. automodapi:: astroquery.esasky
    :no-inheritance-diagram:
