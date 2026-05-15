
***************
Catalog Queries
***************

`~astroquery.mast.CatalogsClass` is a versatile tool for discovering and querying the wide range of astronomical catalogs hosted by the
[Mikulski Archive for Space Telescopes (MAST)](https://archive.stsci.edu/). `~astroquery.mast.CatalogsClass` is a Python wrapper
for our [MAST Table Access Protocol (TAP) Service](https://mast.stsci.edu/vo-tap/), which allows you to query for catalog
metadata and data. If you were querying the MAST TAP service directly, you would need to write your queries in
[Astronomical Data Query Language (ADQL)](https://www.ivoa.net/documents/latest/ADQL.html). With `~astroquery.mast.CatalogsClass`,
you can construct and execute these queries using a more intuitive Python interface, without needing to learn ADQL syntax.

The catalogs available through MAST are diverse, covering a wide range of astronomical objects and phenomena.
They include data from various missions and surveys, such as the Hubble Space Telescope, Kepler, TESS, Gaia, and many more.
These catalogs are organized into **collections**, each of which may contain one or more catalogs with distinct schemas and capabilities.
The `~astroquery.mast.CatalogsClass` interface is designed for flexible querying of catalog data, including both spatial and non-spatial queries,
as well as the ability to filter results based on specific criteria.

At a high level, querying MAST catalogs with `~astroquery.mast.CatalogsClass` involves the following steps:
1. **Discover** available collections and catalogs.
2. **Inspect** catalog metadata to understand available columns and data types, as well as the capabilities of each catalog.
3. **Query** the catalog using spatial and/or non-spatial criteria to retrieve relevant data.

Collections and Catalogs
========================

MAST catalogs are organized into **collections**, where each collection represents a set of related catalogs
with a shared scientific or mission context (e.g., Hubble source catalogs, Gaia data releases, etc.).
Within a collection, one or more **catalogs** may be available, each with its own set of columns and capabilities.

`~astroquery.mast.CatalogsClass` stores a ``collection`` and ``catalog`` as attributes. If no collection and/or catalog
is specified in a query, these attributes will be used as defaults. The ``collection`` attribute is an object
representing the current collection, and the ``catalog`` attribute is a string representing the name of the current
catalog within that collection.

The default value for the ``collection`` attribute is "hsc", referring to the [Hubble Source Catalog version 3](https://archive.stsci.edu/hst/hsc/).
The default value for ``catalog`` is "dbo.SumMagAper2CatView". This is a summary source catalog with data describing sources detected in Hubble images,
including their positions, magnitudes, and other properties.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> print("Default collection:", Catalogs.collection)
   Default collection: hsc
   >>> print("Default catalog:", Catalogs.catalog)
   Default catalog: dbo.SumMagAper2CatView

These attributes may be changed at any time to set new defaults. Both ``collection`` and ``catalog`` will be validated
when set. When changing the collection, the catalog will be reset to the default for the new collection.

These attributes can be set with parameters when instantiating a `~astroquery.mast.CatalogsClass` object, or they can be changed
at any time after instantiation to set new defaults for subsequent queries. Both ``collection`` and ``catalog`` will be validated when set.
``collection`` must be a valid collection name, and ``catalog`` must be a valid catalog within the specified collection. When changing the
collection, the catalog will be reset to the default catalog for the new collection.

Here, we'll change the value of ``collection`` to "ullyses", referring to the
[Hubble Ultraviolet Legacy Library of Young Stars as Essential Standards (ULLYSES)](https://ullyses.stsci.edu/) program. The default catalog
for this collection is "sciencemetadata", which contains metadata about the scientific exposures taken as part of the ULLYSES program,
including their coordinates, observation dates, instruments used, and other properties.

.. doctest-remote-data::

   >>> Catalogs.collection = "ullyses"  # set collection to ULLYSES
   >>> print("New collection:", Catalogs.collection)
   New collection: ullyses
   >>> print("New catalog:", Catalogs.catalog)
   New catalog: dbo.sciencemetadata

You can also create multiple instances of `~astroquery.mast.CatalogsClass` with different defaults, which can be useful for working with multiple catalogs
in the same script or notebook.

.. doctest-remote-data::

   >>> hsc_catalog = Catalogs(collection="hsc")
   >>> print("HSC collection:", hsc_catalog.collection)
   HSC collection: hsc
   >>> print("HSC catalog:", hsc_catalog.catalog)
   HSC catalog: dbo.SumMagAper2CatView
   >>>
   >>> ullyses_catalog = Catalogs(collection="ullyses")
   >>> print("ULLYSES collection:", ullyses_catalog.collection)
   ULLYSES collection: ullyses
   >>> print("ULLYSES catalog:", ullyses_catalog.catalog)
   ULLYSES catalog: dbo.sciencemetadata

Discovering Available Collections and Catalogs
===============================================

Discovering Available Collections
----------------------------------

To list all of the catalog collections that are accessible via the MAST TAP Service, use the `~astroquery.mast.CatalogsClass.get_collections` method.
This returns an `~astropy.table.Table` containing the names of all available collections.

Some historical collections are no longer supported for querying, and will not appear in this list. If a collection
has been renamed or deprecated, Astroquery will issue a warning and suggest the appropriate replacement where possible.

.. doctest-remote-data::

   >>> collections = Catalogs.get_collections()
   >>> print(collections)  # doctest: +IGNORE_OUTPUT
   collection_name
   ---------------
             3dhst
           candels
              caom
            classy
         deepspace
           gaiadr3
             goods
               hsc
             hscv2
       missionmast
           ps1_dr2
            ps1dr1
            ps1dr2
          registry
      skymapperdr4
               tic
           tic_v82
           ullyses

Discovering Catalogs Within a Collection
-----------------------------------------

Once a collection is selected, you can discover which catalogs are available within that collection using the
`~astroquery.mast.CatalogsClass.get_catalogs` method. This returns an `~astropy.table.Table` containing names and descriptions of the catalogs
within the currently selected collection. To query catalogs for a specific collection without changing the class state, you can pass the
collection name as an argument to the method.

.. doctest-remote-data::

   >>> catalogs = Catalogs.get_catalogs("hsc")
   >>> catalogs.pprint(max_width=-1)  # doctest: +IGNORE_OUTPUT
          catalog_name                              description
   -------------------------- -------------------------------------------------------
          dbo.detailedcatalog              Detailed list of source catalog parameters
          dbo.hcvdetailedview Detailed list of Hubble Catalog of Variables parameters
           dbo.hcvsummaryview  Summary list of Hubble Catalog of Variables parameters
        dbo.propermotionsview                       List of proper motion information
      dbo.sourcepositionsview                     List of source position information
       dbo.summagaper2catview    Summary list of source catalog with Aper2 magnitudes
        dbo.summagautocatview  Summary list of source catalog with MagAuto magnitudes
   dbo.catalog_image_metadata               Summary list of Image processing metadata

Inspecting Catalog Metadata
============================

Before querying a catalog, it's important to understand what data it contains and how that data is organized. Catalog metadata includes
information about the columns in the catalog (e.g., their names, data types, and descriptions) as well as the capabilities of the catalog
(e.g., what types of queries it supports). This information can help you construct effective queries and interpret the results correctly.

Inspecting Catalog Columns
---------------------------

Use the `~astroquery.mast.CatalogsClass.get_column_metadata` method to inspect the columns of a catalog. This returns an `~astropy.table.Table`
with information about each column, including its name, data type, unit, and a description. This metadata is crucial for constructing valid queries,
selecting columns of interest, and understanding which columns support different criteria syntax.

Again, you can specify the collection and catalog explicitly as inputs to the function, or you can rely on the default values stored in the class attributes.
If you only specify a collection, the default catalog for that collection will be used. If you only specify a catalog, the current collection will be used.

.. doctest-remote-data::

   >>> catalog_metadata = Catalogs.get_column_metadata(collection="ullyses", catalog="dbo.sciencemetadata")
   >>> catalog_metadata[:5].pprint(max_width=-1)
        column_name      datatype unit         ucd                      description
   --------------------- -------- ---- -------------------- -----------------------------------
               target_id      int         meta.id;meta.main                   ullyses target id
     target_name_ullyses     char             meta.id.assoc              ullyses name of target
      target_name_simbad     char             meta.id.assoc               simbad name of target
        target_name_hlsp     char             meta.id.assoc                 hlsp name of target
   target_classification     char      src.class.stargalaxy target type: lmc; smc; t tau; low z

Inspecting Catalog Capabilities
-------------------------------

Each catalog has different capabilities, which are important to understand when constructing your queries. For example, only certain catalogs
support spatial queries based on a sky position or region. Use the `~astroquery.mast.CatalogsClass.supports_spatial_queries()` method to check
if a catalog supports spatial queries.

.. doctest-remote-data::

   >>> supports_spatial_ullyses = Catalogs.supports_spatial_queries(collection="ullyses", catalog="dbo.sciencemetadata")
   >>> print("Supports spatial queries:", supports_spatial_ullyses)
   Supports spatial queries: False
   >>>
   >>> supports_spatial_hsc = Catalogs.supports_spatial_queries(collection="hsc", catalog="dbo.SumMagAper2CatView")
   >>> print("Supports spatial queries:", supports_spatial_hsc)
   Supports spatial queries: True

Querying Catalogs
==================

`~astroquery.mast.CatalogsClass` provides three main methods for querying catalogs:

- `~astroquery.mast.CatalogsClass.query_criteria` is the most flexible method. It supports purely column-based queries, purely spatial queries, or a combination of both.
- `~astroquery.mast.CatalogsClass.query_region` is a convenience method for spatial queries that use coordinates or a region on the sky.
- `~astroquery.mast.CatalogsClass.query_object` is a convenience method for spatial queries that use an object name resolved to coordinates.

All three methods ultimately construct and execute an ADQL query against the MAST TAP service. All three support column-based filtering, sorting, and
limiting of results. The primary difference between them is whether and how spatial criteria are specified.

Shared Query Parameters
------------------------

The following parameters are shared across all three query methods:

  - ``collection`` : The name of the catalog collection to query. If not specified, the ``collection`` class attribute will be used as the default.
  - ``collection``: The name of the catalog collection to query. If not specified, the ``collection`` class attribute will be used as the default.
  - ``catalog``: The name of the catalog to query within the specified collection. If not specified, the ``catalog`` class attribute will be used as the default.
  - ``limit``: An integer specifying the maximum number of results to return. The default is 5,000.
  - ``offset``: An integer specifying the number of results to skip before starting to return results. This is useful for paginating through large result sets. Default is 0.
  - ``count_only``: A boolean indicating whether to return only the count of matching results instead of the results themselves. Default is False.
  - ``select_cols``: A list of column names to include in the results. If not specified, all columns will be returned.
  - ``sort_by``: A string or list of strings specifying the column(s) to sort the results by. Default is None (no sorting).
  - ``sort_desc``: A boolean or list of booleans specifying whether to sort in descending order for each column specified in ``sort_by``.
    Default is False (ascending order).
  - ``filters``: Another parameter used to specify criteria filters as a dictionary. Use this option when the name of a column conflicts
    with a named parameter of this method.
  - ``run_async``: If True, run the query in asynchronous mode. This mode is more robust and preferable for long-running queries.
  - ``return_adql``: If True, return the ADQL query string instead of executing the query. This is useful for debugging or for users who want
    to run the query directly against the TAP service. When False, the ADQL query string is also returned in the metadata of the result table.

These parameters allow users to control the scope and format of their queries consistently across all three methods.

Criteria Syntax
----------------

All query methods also allow you to filter results based on column values. Users may specify criteria using keyword arguments, where the keyword
is the column name and the value is the filter condition. Multiple criteria are combined using a logical **AND**.

Criteria syntax supports a variety of operations for filtering results:

- A single value (e.g. ``column=value``) will filter for rows where the column is equal to the value.
- A list of values (e.g. ``column=[value1, value2]``) will filter for rows where the column is equal to any of the values in the list (logical OR).
- A value prefixed with ``!`` (e.g. ``column="!value"``) will filter for rows where the column is not equal to the value.
- For string columns, a string with a wildcard character ``*`` (e.g. ``column="NGC*"``) will filter for rows where the column value matches the pattern,
  where ``*`` can match any sequence of characters.
- For numeric columns, a string with a comparison operator (e.g. ``column=">value"``) will filter for rows where the column value satisfies the specified
  comparison. Supported operators include ``<``, ``>``, ``<=``, and ``>=``.
- For numeric columns, a string with a range (e.g. ``column="value1..value2"``) will filter for rows where the column value falls within the specified range
  (inclusive).
- For temporal columns, values can be specified as strings in a recognized date/time format (e.g. ``YYYY``, ``YYYY-MM-DD``, ``YYYY-MM-DD hh:mm:ss``, etc.),
  ``astropy.time.Time`` objects, or ``datetime`` objects. The same comparison operators and range syntax as numeric columns can be used to filter temporal
  columns based on date/time values.

We'll use the Ullyses science metadata catalog to demonstrate a column-based query, since it doesn't support spatial queries. Let's filter for the following:

- Targets with a name that starts with "NGC".
- Targets that belong to spectral class "O" or "B".
- Targets that are NOT known binaries.
- Targets that are NOT classified as "Galaxy" or "Late O Dwarf".
- Targets with Gaia parallax less than -0.01 or greater than or equal to 0.
- Targets with effective temperature between 30,000 and 50,000 K.

We will also select a subset of columns to return with the ``select_cols`` parameter.

.. doctest-remote-data::

   >>> result = Catalogs.query_criteria(
   ...     collection="ullyses",  # Query the 'ullyses' collection
   ...     catalog="sciencemetadata",  # Query the 'sciencemetadata' catalog
   ...     target_name_ullyses="NGC*",  # Query for targets names starting with 'NGC'
   ...     sp_class=["O", "B"],  # Query for targets with spectral class "O" or "B"
   ...     known_binary=False,  # Query for targets that are not known binaries
   ...     target_classification=["!Galaxy", "!Late O Dwarf"],  # Exclude targets classified as 'Galaxy' or 'Late O Dwarf'
   ...     gaia_parallax=["<-0.1", ">=0"],  # Query for targets with Gaia parallax less than -0.01 or greater than or equal to 0
   ...     star_teff="30000..50000",  # Query for targets with effective temperature between 30,000 and 50,000 K
   ...     select_cols=["target_name_ullyses", "target_classification", "known_binary", "sp_class", "gaia_parallax", "star_teff"]
   ... )
   >>> result[:5].pprint(max_width=-1)  #doctest: +IGNORE_OUTPUT
   target_name_ullyses target_classification known_binary sp_class gaia_parallax star_teff
                                                                        mas          K
   ------------------- --------------------- ------------ -------- ------------- ---------
        NGC346 ELS 043         Early B Dwarf        False        B     -0.111579   33000.0
        NGC346 ELS 026      Early B Subgiant        False        O     -0.047347   31000.0
        NGC346 ELS 028           Mid O Dwarf        False        O     -0.069206   39600.0
        NGC346 ELS 007         Early O Dwarf        False        O     -0.070696   42100.0
        NGC346 MPG 356           Mid O Dwarf        False        O     -0.051241   38200.0

Spatial Query Parameters
------------------------

If a catalog supports spatial queries, the following parameters can be used to specify the spatial region of interest:

- ``coordinates``: A string or `~astropy.coordinates.SkyCoord` object specifying the center of a cone search. This parameter is used in
  conjunction with ``radius``.
- ``object_name``: A string specifying the name of an astronomical object to resolve to coordinates for a cone search. This parameter is used in
  conjunction with ``radius``.
- ``resolver``: A string specifying the name of the resolver to use when resolving ``object_name`` to coordinates. This is only applicable when
  ``object_name`` is provided. Default is None.
- ``radius``: The radius of a cone search around ``coordinates`` or ``object_name``. Can be defined as a string with units (e.g., "10 arcsec"),
  a `~astropy.units.Quantity`, or a float in degrees. Default is 0.2 degrees.
- ``region``: Specifies the spatial region of interest for more complex spatial queries, such as polygon searches.
  Please see the [Specifying Spatial Regions](#specifying-spatial-regions) section below for details on how to use this parameter.

If no spatial parameters are provided, the query is purely column-based and will not filter results based on position. If they are supplied, the
spatial parameters are combined with any column-based criteria using a logical **AND**, meaning that only results that satisfy both the spatial and
column-based criteria will be returned.

We'll demonstrate a spatial query using the HSC summary source catalog, which supports spatial queries. Let's filter for the following:

- Sources within 2 arcseconds of the coordinates (322.49324, 12.16683).
- Sources with target names that are either "M-15" or start with "NGC".
- Sources with a start time between 2006 and 2013.

The query will sort results first by the number of images in ascending order, and then by start time in descending order. We'll also limit
the number of results returned to 10 and select a subset of columns to return with the ``select_cols`` parameter.

.. doctest-remote-data::

   >>> result = Catalogs.query_criteria(
   ...     collection="hsc",
   ...     coordinates="322.49324 12.16683",
   ...     radius="2 arcsec",  # Query for sources within 2 arcseconds of the specified coordinates
   ...     targetname=["M-15", "NGC*"],  # Query for targets with names 'M-15' or starting with 'NGC'
   ...     starttime="2006..2013",  # Query for observations with starttime between 2006 and 2013
   ...     sort_by=["numimages", "starttime"],  # Sort results by number of images and then by starttime
   ...     sort_desc=[False, True],  # Sort numimages in ascending order and starttime in descending order
   ...     limit=5,  # Limit to 5 results
   ...     select_cols=["matchid", "matchra", "matchdec", "numimages", "starttime", "targetname"]
   ... )
   >>> result.pprint(max_width=-1)
    matchid       matchra            matchdec      numimages         starttime          targetname
                    deg                deg
   --------- ------------------ ------------------ --------- -------------------------- ----------
    61895629   322.493715383149 12.166629788750484         1 2011-10-22 08:10:21.217000       M-15
    11562863 322.49294957070185 12.166668540816076         2 2006-05-02 01:13:43.920000    NGC7078
    16381110  322.4936372300021 12.166722963370844         3 2011-10-07 15:20:59.197000       M-15
   105452327  322.4933282596331  12.16732046125442         3 2011-10-07 15:20:59.197000       M-15
    49726591  322.4927927121447 12.166998250407733         3 2006-05-02 01:13:43.920000    NGC7078

The `~astroquery.mast.CatalogsClass.query_region` and `~astroquery.mast.CatalogsClass.query_object` methods are convenience methods for spatial queries.
`~astroquery.mast.CatalogsClass.query_region` allows you to specify a region on the sky using the ``coordinates``, ``radius``, and/or ``region`` parameters.
`~astroquery.mast.CatalogsClass.query_object` allows you to specify an ``object_name`` that will be resolved to coordinates and a ``radius`` for a cone search.
Both methods also support column-based criteria, sorting, and limiting of results, just like `~astroquery.mast.CatalogsClass.query_criteria`.

For these queries, we will use the ``tic_v82`` collection, which refers to the
[TESS Input Catalog version 8.2](https://ui.adsabs.harvard.edu/abs/2022yCat.4039....0P/abstract). We'll use the `~astroquery.mast.CatalogsClass.query_region`
method to perform a simple cone search for sources within 1 arcminute of the coordinates (158.47924, -7.30962).

.. doctest-remote-data::

   >>> result = Catalogs.query_region(
   ...     collection="tic_v82",
   ...     catalog="source",
   ...     coordinates="158.47924 -7.30962",
   ...     radius="1 arcmin",
   ...     select_cols=["id", "ra", "dec"]
   ...  )
   >>> result.pprint(max_width=-1)  #doctest: +IGNORE_OUTPUT
       id           ra               dec
                   deg               deg
   --------- ---------------- -----------------
   841736281 158.483019303286 -7.32320013067735
    56661355 158.467833401313 -7.31994230664877
   841736289 158.475246467012 -7.29984176473098

For this next query, we'll use the `~astroquery.mast.CatalogsClass.query_object` method to search for sources within 0.1 degrees of the object
["M11"](https://science.nasa.gov/mission/hubble/science/explore-the-night-sky/hubble-messier-catalog/messier-11/), which is an open star cluster
also known as the Wild Duck Cluster. We'll also filter for sources that are stars, sort results by the effective temperature of the source, and
limit the number of results to 10.

.. doctest-remote-data::

   >>> result = Catalogs.query_object(
   ...     collection="tic_v82",
   ...     object_name="M11",
   ...     radius=0.1,
   ...     objtype="STAR",
   ...     sort_by="teff",
   ...     select_cols=["id", "ra", "dec", "objtype", "teff"],
   ...     limit=10
   ... )
   >>> result.pprint(max_width=-1)
       id           ra               dec        objtype  teff
                   deg               deg                  K
   --------- ---------------- ----------------- ------- ------
   151449173  282.67863187603 -6.26184813416028    STAR 3025.0
   151456872 282.798899858481  -6.3102827609116    STAR 3093.0
   151455613 282.743580903863  -6.2188868480077    STAR 3260.0
    31821653 282.851911590723 -6.26914233254122    STAR 3265.0
   151456960 282.776343005483 -6.31830783055104    STAR 3281.0
   151457177 282.777039432654 -6.34079199389906    STAR 3285.0
   151457138 282.762562964854 -6.33622888690153    STAR 3290.0
   151455292 282.769687283022 -6.18834508004063    STAR 3311.0
   151455728 282.730778111903  -6.2287837491146    STAR 3325.0
   151456312 282.737426625799 -6.26956499623787    STAR 3372.0

.. _specifying-spatial-regions:

Specifying Spatial Regions
--------------------------

For catalogs that support spatial queries, there are several ways to specify the spatial region of interest. The simplest is a cone search,
defined by a center position and a radius. More complex regions, such as polygons, can also be specified using the ``region`` parameter.

Cone Search
^^^^^^^^^^^

Cone searches are the most common type of spatial query, defined by a center position and a radius. They may be specified using:

- The ``coordinates`` and ``radius`` parameters together.
- The ``object_name`` and ``radius`` parameters together, where the object name is resolved to coordinates.
- The ``region`` parameter as:
  - A `~regions.CircleSkyRegion` object from the `~regions` package.
  - A Space-Time Coordinate (STC) string in the format ``CIRCLE [frame] <ra> <dec> <radius>``, where ra, dec, and radius are in degrees.

Let's demonstrate this on the ``skymapperdr4`` collection, which contains catalogs from the
[SkyMapper Southern Survey: Data Release 4](https://skymapper.anu.edu.au/data-release/). The catalog we query will be "dr4.master", which is
a master catalog of sources detected in the SkyMapper DR4 survey, containing their positions, magnitudes, and other properties. Our cone
search will be centered on the coordinate (18.855, -6.945) with a radius of 0.01 degrees.

.. doctest-remote-data::
   >>> from regions import CircleSkyRegion
   >>> from astropy.coordinates import SkyCoord
   >>> import astropy.units as u
   >>>
   >>> circle_sky_region = CircleSkyRegion(center=SkyCoord(18.86, -6.95, unit='deg'), radius=0.01*u.deg)
   >>> circle_stc_string = "CIRCLE ICRS 18.855 -6.945 0.01"
   >>>
   >>> result = Catalogs.query_region(
   ...     collection="skymapperdr4",
   ...     catalog="dr4.master",
   ...     region=circle_sky_region,  # or use region=circle_stc_string
   ...     select_cols=["object_id", "raj2000", "dej2000"]
   ... )
   >>> result.pprint(max_width=-1)
   object_id   raj2000   dej2000
                 deg       deg
   ---------- --------- ---------
   2025217836 18.858273 -6.955493
   2025218117 18.867198 -6.950921
   2025218116 18.868135 -6.952049
   2025217835 18.861348 -6.958706
   1018207669 18.862164 -6.959528

Polygon Search
^^^^^^^^^^^^^^^

Polygon searches allow for more complex spatial queries by defining a polygonal region on the sky.
They may be specified using any of the following as the ``region`` parameter:

- An iterable of (RA, Dec) tuples representing the vertices of the polygon.
- A `~regions.PolygonSkyRegion` object from the `~regions` package.
- A Space-Time Coordinate (STC) string in the format ``POLYGON [frame] <ra_1> <dec_1> <ra_2> <dec_2> ... <ra_n> <dec_n>``, where (ra_i, dec_i)
  are the vertices of the polygon in degrees.

Keep in mind that at least three vertices are required to define a valid polygon, and the vertices should be ordered either clockwise or
counterclockwise. The polygon will be automatically closed by connecting the last vertex back to the first.

Let's search for sources in the Skymapper source catalog that fall within a four-sided polygon. The polygon has the same center as the
previous cone search, so the results may look similar!

.. doctest-remote-data::
   >>> from regions import PolygonSkyRegion
   >>>
   >>> polygon_iter = [(18.85, -6.96), (18.87, -6.96), (18.87, -6.94), (18.85, -6.94)]
   >>> polygon_sky_region = PolygonSkyRegion(vertices=SkyCoord(
   ...     [[18.85, -6.96], [18.87, -6.96], [18.87, -6.94], [18.85, -6.94]],
   ...     unit='deg'
   ... ))
   >>> polygon_stc_string = "POLYGON ICRS 18.85 -6.96 18.87 -6.96 18.87 -6.94 18.85 -6.94"
   >>>
   >>> result = Catalogs.query_region(
   ...     collection="skymapperdr4",
   ...     catalog="dr4.master",
   ...     region=polygon_sky_region,  # or use region=polygon_sky_region or region=polygon_stc_string
   ...     select_cols=["object_id", "raj2000", "dej2000"]
   ... )
   >>> result.pprint(max_width=-1)
   object_id   raj2000   dej2000
                 deg       deg
   ---------- --------- ---------
   2025217836 18.858273 -6.955493
   2025218117 18.867198 -6.950921
   2025218116 18.868135 -6.952049
   2025217835 18.861348 -6.958706
   1018207669 18.862164 -6.959528
     13693185 18.853648 -6.941675
   2025218118 18.851606 -6.942183
   1018207883 18.851708 -6.941662


Counting Results
-----------------

All query methods support a ``count_only=True`` option, which returns only the number of matching records:

Each of the three query methods supports a ``count_only`` parameter. When set to ``True``, it returns only the number of matching results.
This can be useful for quickly assessing the size of a result set without having to retrieve all the data.

Let's demonstrate this on the ``caom`` collection, which refers to the
[Common Archive Observation Model](https://www.ivoa.net/documents/CAOM/20240927/WD-CAOM-2.5-20240927.pdf), a data model used to
describe astronomical observations. We'll query the ``obspointing`` catalog, which contains metadata about scientific observations at MAST.
We'll perform a query to count the number of observations that are within 0.2 degrees of the exoplanet
[WASP-12b](https://science.nasa.gov/exoplanet-catalog/wasp-12-b/). You'll notice that this query takes several seconds to complete.
The ``obspointing`` catalog is huge, and if you were to run the same query without the ``count_only`` parameter, it would typically take
longer to return the full results, especially if there are many matching sources.

For very long-running queries, you can also run the query in asynchronous mode by setting ``run_async=True``. This will prevent the query from timing out.

.. doctest-remote-data::

   >>> count = Catalogs.query_criteria(
   ...     collection="caom",
   ...     catalog="obspointing",
   ...     object_name="WASP-12b",
   ...     radius=0.2,
   ...     count_only=True,
   ...     run_async=True
   ... )
   >>> print('Number of matching records:', count)
   Number of matching records: 6735

Deprecated Interfaces
======================

Several legacy methods related to the Hubble Source Catalog (HSC) remain available but are deprecated and will be removed
in a future release. These methods include:

- `~astroquery.mast.CatalogsClass.query_hsc_matchid`
- `~astroquery.mast.CatalogsClass.get_hsc_spectra`
- `~astroquery.mast.CatalogsClass.download_hsc_spectra`

New workflows should use the general `~astroquery.mast.CatalogsClass` interface described above.
