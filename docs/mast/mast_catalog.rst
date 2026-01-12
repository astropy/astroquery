
***************
Catalog Queries
***************

The `~astroquery.mast.Catalogs` interface provides toold for discovering and querying the wide
range of astronomical catalogs hosted by MAST. These catalogs span multiple missions and surveys
and are organized into **collections**, each of which may contain one or more **catalogs** with
distinct schemas and capabilties. This interface is designed for **flexible, SQL-like querying** of 
catalog data, including spatial searches and column-based filtering.

At a high level, querying MAST catalogs follows three steps:
  1. Discover available collections and catalogs.
  2. Inspect catalog metadata to understand available fields and data types.
  3. Query the catalog using positional and/or criteria-based filters.

Collections and Catalogs
========================

MAST catalogs are organized into **collections**, where each collection represents a related set of catalogs
with a shared scientific or mission context (for example, Hubble source catalogs, Gaia data releases, etc).
Within a collection, one or more **catalogs** may be available, each with its own schema and data.

`~astroquery.mast.CatalogsClass` maintains a current collection and catalog as attributes. If no collection or catalog
is specified in a query, these attributes will be used as defaults. The ``collection`` attribute is a 
`~astroquery.mast.catalog_collection.CatalogCollection` instance representing the current collection,
and the ``catalog`` attribute is a string representing the name of the current catalog within that collection.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> print("Default collection:", Catalogs.collection.name)
   Default collection: hsc
   >>> print("Default catalog:", Catalogs.catalog)
   Default catalog: dbo.SumMagAper2CatView

These attributes may be changed at any time to set new defaults. Both ``collection`` and ``catalog`` will be validated
when set. When changing the collection, the catalog will be reset to the default for the new collection.

.. doctest-remote-data::

   >>> Catalogs.collection = "TIC"  # set collection to TESS Input Catalog
   >>> print("New collection:", Catalogs.collection.name)
   New collection: tic
   >>> print("New catalog:", Catalogs.catalog)
   New catalog: dbo.CatalogRecord

Discovering Available Collections
---------------------------------

To list all available catalog collections hosted at MAST, use the
`~astroquery.mast.CatalogsClass.get_collections` method.

This returns an `~astropy.table.Table` containing the names of all available collections.

Some historical collections are no longer supported for querying, and will not appear in this list. If a collection 
has been renamed or deprecated, Astroquery will issue a warning and suggest the appropriate replacement where possible.

.. doctest-remote-data::

   >>> collections = Catalogs.get_collections()
   >>> print(collections)  # doctest: +IGNORE_OUTPUT
   collection_name
   ---------------
              caom
            classy
           gaiadr3
               hsc
             hscv2
       missionmast
            ps1dr1
            ps1dr2
           ps1_dr2
          registry
      skymapperdr4
               tic
           ullyses
             goods
           candels
             3dhst
         deepspace

Discovering Catalogs in a Collection
-------------------------------------

Once a collection is selected, you can list the catalogs available within it using the
`~astroquery.mast.catalog_collection.CatalogCollection.get_catalogs` method.

To query catalogs for a specific collection without changing the class state, you can pass the 
collection name as an argument to the method.

.. doctest-remote-data::

   >>> catalogs = Catalogs.get_catalogs('hsc')
   >>> catalogs.pprint(max_width=-1)  # doctest: +IGNORE_OUTPUT
          catalog_name                              description                      
   -------------------------- -------------------------------------------------------
           tap_schema.schemas                  description of schemas in this dataset
            tap_schema.tables                   description of tables in this dataset
           tap_schema.columns                  description of columns in this dataset
              tap_schema.keys             description of foreign keys in this dataset
       tap_schema.key_columns      description of foreign key columns in this dataset
          dbo.detailedcatalog              Detailed list of source catalog parameters
          dbo.hcvdetailedview Detailed list of Hubble Catalog of Variables parameters
           dbo.hcvsummaryview  Summary list of Hubble Catalog of Variables parameters
        dbo.propermotionsview                       List of proper motion information
      dbo.sourcepositionsview                     List of source position information
       dbo.summagaper2catview    Summary list of source catalog with Aper2 magnitudes
        dbo.summagautocatview  Summary list of source catalog with MagAuto magnitudes
   dbo.catalog_image_metadata               Summary list of Image processing metadata

Inspecting Catalog Metadata
----------------------------

Before querying a catalog, it is often useful to inspect its metadata to understand the available columns,
data types, and supported query capabilties. The `~astroquery.mast.CatalogsClass.get_catalog_metadata` method returns
an `~astropy.table.Table` describing the catalog schema, including column names, data types, units, and descriptions.
This metadata can help you construct valid queries, select columns of interest, and understand which fields support
numeric comparions, string matching, or spatial queries.

Again, you can specify a collection and catalog explicitly as inputs to the function, or use the current defaults.
If you only specify a collection, the default catalog for that collection will be used.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_metadata = Catalogs.get_catalog_metadata('gaiadr3', 'dbo.gaia_source')
   >>> catalog_metadata[:5].pprint(max_width=-1)
   column_name  datatype unit        ucd                description         
   ------------ -------- ---- ----------------- ----------------------------
   solution_id     long           meta.version              catalog version
   designation     char      meta.id;meta.main                  designation
      source_id     long                meta.id                    source id
   random_index     long              meta.code                 random index
      ref_epoch   double   yr        time.epoch reference epoch julian years


Querying Catalogs
==================

The Catalogs interface provides three closely related query methods. All three methods return results from a MAST 
catalog as an `~astropy.table.Table` (or a scalar count, if requested), and all three support column-based filtering, 
sorting, and result limiting. The primary difference between them is how positional constraints are specified.

At a high level:
  - `~astroquery.mast.CatalogsClass.query_criteria` is the most flexible method. It supports purely column-based queries, 
    purely positional queries, or a combination of both.

  - `~astroquery.mast.CatalogsClass.query_region` is a convenience wrapper for positional queries using coordinates or an explicit region.

  - `~astroquery.mast.CatalogsClass.query_object` is a convenience wrapper for cone searches centered on a resolved object name.

All three methods ultimately construct and execute an ADQL query against the MAST TAP service.

Shared Query Parameters
------------------------

The following parameters are supported by all three query methods:
  - ``collection`` : The catalog collection to query. If not specified, the value of the instance's ``collection`` attribute is used.

  - ``catalog`` : The catalog within the collection to query. If not specified, the value of the instance's ``catalog`` attribute is used, or if ``collection`` is specified, the default catalog for that collection.

  - ``limit`` : Maximum number of rows to return (default: 5000).

  - ``offset`` : Number of rows to skip before returning results (default: 0).

  - ``count_only`` : If True, return only the number of matching records instead of the records themselves.

  - ``select_cols`` : A list of column names to include in the result. If omitted, all columns are returned.

  - ``sort_by``: One or more column names to sort by.

  - ``sort_desc`` : Whether to sort in descending order (either a single boolean applied to all ``sort_by`` columns or one per column).

These parameters allow users to control the scope and format of their queries consistently across all three methods.

Writing Queries
----------------

The `~astroquery.mast.CatalogsClass.query_criteria` method supports both positional parameters and column-based filters.
Positional constraints are optional. 

Supported positional parameters include:
  - ``coordinates`` : Sky coordinates around which to perform a cone search.
  - ``objectname`` : Name of the object around which to perform a cone search.
  - ``resolver`` : Resolver service to use for object name resolution.
  - ``radius`` : Radius of the cone search around the specified coordinates or object name. Can be defined as an `~astropy.units.Quantity`, a string with units (e.g., ``"10 arcsec"``), or a numeric value interpreted as degrees.
  - ``region`` : Explicit region specification for the search. See :ref:`specifying-spatial-regions` below for more details.

If no positional parameters are supplied, the query is purely criteria-based. If positional parameters are supplied, 
they are combined with any column-based criteria using logical **AND**.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> result = Catalogs.query_criteria(collection='hsc',
   ...                                  coordinates="322.49324 12.16683",
   ...                                  radius='2 arcsec',
   ...                                  sort_by=['numimages', 'starttime'],
   ...                                  sort_desc=[False, True],
   ...                                  limit=5,
   ...                                  select_cols=['matchid', 'matchra', 'matchdec', 'numimages', 'starttime'])
   >>> result.pprint(max_width=-1)
    matchid       matchra            matchdec      numimages         starttime         
                    deg                deg                                             
   --------- ------------------ ------------------ --------- --------------------------
   100906349  322.4932839715549 12.166957658789572         1 2013-09-01 14:42:57.487000
    37053748 322.49333237602906 12.167170257824768         1 2013-09-01 14:09:53.487000
    61895629   322.493715383149 12.166629788750484         1 2011-10-22 08:10:21.217000
    19779150 322.49277386636714 12.166728768957904         2 2013-09-01 14:09:53.487000
    11562863 322.49294957070185 12.166668540816076         2 2006-05-02 01:13:43.920000

To filter results based on column values, users may specify criteria as keyword arguments,
where the keyword is the column name and the value is the desired filter. Multiple criteria are combined
using logical **AND**.

Criteria syntax supports a variety of operations, including:

- Exact matches by specifying a value for a column.

- To filter by multiple values for a single column, use a list of values. This performs an **OR** operation between the values.

- A filter value can be negated by prefiing it with ``!``, meaning that rows matching that value will be excluded from the results.
  When a negated value is present in a list of filters, any positive values in that set are combined with **OR** logic, and any negated 
  values are combined with **AND** logic against the positives.

- For columns with a numeric data type, filter using comparison values (``<``, ``>``, ``<=``, ``>=``).

  - ``<``: Return values less than or before the given number/date

  - ``>``: Return values greater than or after the given number/date

  - ``<=``: Return values less than or equal to the given number/date

  - ``>=``: Return values greater than or equal to the given number/date

- For columns with a numeric data type, select an inclusive range with the syntax ``'#..#'``.

- Wildcards are special characters used in search patterns to represent one or more unknown characters, 
  allowing for flexible matching of strings. The wildcard characters are ``*`` and ``%`` and they replace any number
  of characters preceding, following, or in between existing characters, depending on their placement.

.. doctest-remote-data::

   >>> result = Catalogs.query_criteria(collection='ullyses',
   ...                                  catalog='sciencemetadata',
   ...                                  target_name_ullyses='NGC*',
   ...                                  target_classification='!Galaxy',
   ...                                  known_binary=False,
   ...                                  sp_class=['O', 'B'],
   ...                                  gaia_parallax=['<-0.1', '>=0'],
   ...                                  star_teff='30000..50000',
   ...                                  select_cols=['target_name_ullyses', 'target_classification', 'known_binary', 'sp_class', 'gaia_parallax', 'star_teff'])
   >>> result.pprint(max_width=-1)
   target_name_ullyses target_classification known_binary sp_class gaia_parallax star_teff
                                                                        mas          K    
   ------------------- --------------------- ------------ -------- ------------- ---------
        NGC346 ELS 043         Early B Dwarf        False        B     -0.111579   33000.0
        NGC346 MPG 487          Late O Dwarf        False        O     -0.389724   35800.0
       NGC 3109 EBU 20      Mid O Supergiant        False        O      0.876327   31150.0
       NGC 3109 EBU 34      Mid O Supergiant        False        O     -0.126069   33050.0


The `~astroquery.mast.CatalogsClass.query_region` and `~astroquery.mast.CatalogsClass.query_object` methods are 
convenience wrappers around `~astroquery.mast.CatalogsClass.query_criteria`:

  - `~astroquery.mast.CatalogsClass.query_region` requires a positional constraint (``coordinates`` or ``region``).

  - `~astroquery.mast.CatalogsClass.query_object` requires an ``objectname`` and performs a cone search.

Both methods also accept column-based criteria, which are applied in the same way as in `~astroquery.mast.CatalogsClass.query_criteria`.

.. doctest-remote-data::

   >>> result = Catalogs.query_region(collection='skymapperdr4',
   ...                                coordinates="158.47924 -7.30962", 
   ...                                radius='1 arcmin',
   ...                                select_cols=['object_id', 'raj2000', 'dej2000'])
   >>> result.pprint(max_width=-1)
   object_id   raj2000    dej2000 
                 deg        deg   
   ---------- ---------- ---------
   1116262239 158.475216  -7.29985
     92307496 158.483015 -7.323183
     92307428  158.46783 -7.319955
   2151499732 158.466411 -7.319867

.. doctest-remote-data::

   >>> result = Catalogs.query_object(collection='skymapperdr4',
   ...                                objectname='M11', 
   ...                                radius=0.01,
   ...                                catwise_id='2825m061*',
   ...                                sort_by='mean_epoch',
   ...                                select_cols=['object_id', 'raj2000', 'dej2000', 'catwise_id', 'mean_epoch'])
   >>> result[:5].pprint(max_width=-1)
   object_id   raj2000    dej2000      catwise_id     mean_epoch
                 deg        deg                           d     
   ---------- ---------- --------- ------------------ ----------
    277772662  282.75865 -6.273223 2825m061_b0-113841 56833.6242
    277772668 282.762729 -6.274544 2825m061_b0-010099 56834.1188
   2389914703 282.768791 -6.275556 2825m061_b0-045485 56834.6156
    277772658 282.758508 -6.276218 2825m061_b0-049457 56834.6167
    277772511 282.764593  -6.27897 2825m061_b0-046693 56895.2497

.. _specifying-spatial-regions:

Specifying Spatial Regions
--------------------------

Catalogs that support spatial queries allow regions to be specified in several ways.

Cone Searches
^^^^^^^^^^^^^

Cone searches are the most common type of spatial query, defined by a center position and a radius. They may be specifed using:
  - ``coordinates`` and ``radius``
  - ``objectname`` and ``radius``
  - A `~astropy.regions.CircleSkyRegion` object as the ``region`` parameter
  - A Space-Time Coordinate (STC) CIRCLE region string as the ``region`` parameter

An STC-S CIRCLE region string has the following format:

``CIRCLE [frame] <ra> <dec> <radius>``

For example: 

``CIRCLE ICRS 210.8 54.35 0.05``

This means:
  - ICRS: Coordinate frame (optional; defaults to ICRS if omitted)
  - 210.8: Right Ascension in degrees
  - 54.35: Declination in degrees
  - 0.05: Radius in degrees

.. doctest-remote-data::
   >>> result = Catalogs.query_region(collection='ps1_dr2',
   ...                                region='CIRCLE ICRS 18.895 -6.944 0.01',
   ...                                sort_by='objID',
   ...                                select_cols=['objName', 'objID', 'raMean', 'decMean'])
   >>> result[:5].pprint(max_width=-1)
           objName               objID             raMean           decMean      
                                                    deg               deg        
   ----------------------- ----------------- ----------------- ------------------
   PSX J011534.22-065706.1 99650188926188340       18.89261844        -6.95171552
   PSX J011534.90-065704.8 99650188954378784       18.89543744        -6.95134445
   PSX J011533.84-065651.9 99660188909803092 18.89100927680362 -6.947762708324004
   PSX J011533.97-065643.6 99660188915395866        18.8915527         -6.9454449
   PSX J011534.30-065636.0 99660188931668392       18.89294147        -6.94333417

Polygon Searches
^^^^^^^^^^^^^^^^^

Polygon searches allow for more complex spatial queries by defining a polygonal region on the sky.
They may be specified using any of the following as the ``region`` parameter:

  - An iterable of coordinate pairs
  - A `~astropy.regions.PolygonSkyRegion` object
  - A Space-Time Coordinate (STC) POLYGON region string

An STC-S POLYGON string has the form:

``POLYGON [frame] <ra1> <dec1> <ra2> <dec2> <ra3> <dec3> ...``

For example: 

``POLYGON ICRS 210.7 54.3 210.9 54.3 210.9 54.4 210.7 54.4``

This defines a four-vertex polygon with vertices given as (RA, Dec) pairs in degrees. At least three vertices (six numbers) are required.

.. doctest-remote-data::
   >>> result = Catalogs.query_criteria(collection='caom',
   ...                                  region='POLYGON ICRS 18.85 -6.95 18.86 -6.95 18.86 -6.94 18.85 -6.94',
   ...                                  limit=5,
   ...                                  select_cols=['target_name', 'obs_id', 's_ra', 's_dec'])
   >>> result.pprint(max_width=-1)
   target_name                                   obs_id                                         s_ra             s_dec       
                                                                                                deg               deg        
   ----------- ------------------------------------------------------------------------- ----------------- ------------------
     408084461 hlsp_tglc_tess_ffi_gaiaid-2475555794352572672-s0003-cam1-ccd3_tess_v1_llc 18.85365901920825 -6.941643227687541
     408084461           hlsp_t16_tess_ffi_s0003-cam1-ccd3-02475555794352572672_tess_v01     18.8536465402      -6.9416358523
     408084461         hlsp_tasoc_tess_ffi_tic00408084461-s0003-cam1-ccd3-c1800_tess_v05  18.8532579321195  -6.94140657784404
     408084461       hlsp_gsfc-eleanor-lite_tess_ffi_s0003-0000000408084461_tess_v1.0_lc  18.8532579321195 -6.941406577844042
     408084461                     hlsp_qlp_tess_ffi_s0097-0000000408084461_tess_v01_llc     18.8532579321     -6.94140657784


Counting Results
-----------------

All query methods support a ``count_only=True`` option, which returns only the number of matching records:

.. doctest-remote-data::

   >>> count = Catalogs.query_criteria(collection='skymapperdr4',
   ...                                 region=[(20, -5), (20, -6), (21, -6), (21, -5)],
   ...                                 count_only=True)
   >>> print('Number of matching records:', count)
   Number of matching records: 5479

This is useful for estimating result sizes before executing large queries.

Deprecated Interfaces
======================

Several legacy methods related to the Hubble Source Catalog (HSC) remain available but are deprecated and will be removed
in a future release. These methods include:

- `~astroquery.mast.CatalogsClass.query_hsc_matchid`
- `~astroquery.mast.CatalogsClass.get_hsc_spectra`
- `~astroquery.mast.CatalogsClass.download_hsc_spectra`

New workflows should use the general `~astroquery.mast.CatalogsClass` interface described above.
