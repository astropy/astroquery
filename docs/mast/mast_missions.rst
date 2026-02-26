
************************
Mission-Specific Queries
************************

The `~astroquery.mast.MastMissionsClass` class allows for search queries based on mission-specific 
metadata for a given data collection. This metadata includes header keywords, proposal information, and observational parameters.
The following missions/products are currently available for search:

- `Hubble Space Telescope <https://www.stsci.edu/hst>`_ (``'hst'``)

- `James Webb Space Telescope <https://www.stsci.edu/jwst>`_ (``'jwst'``)

- `International Ultraviolet Explorer <https://archive.stsci.edu/iue/>`_ (``'iue'``)

- `High Level Science Products <https://outerspace.stsci.edu/display/MASTDOCS/About+HLSPs>`_

  - `COS Legacy Archive Spectroscopic SurveY <https://archive.stsci.edu/hlsp/classy>`_ (``'classy'``)

  - `Hubble UV Legacy Library of Young Stars as Essential Standards <https://archive.stsci.edu/hlsp/ullyses>`_ (``'ullyses'``)

An object of the ``MastMissions`` class is instantiated with a default mission of ``'hst'`` and
default service set to ``'search'``. The searchable metadata for Hubble encompasses all information that
was previously accessible through the original HST web search form. The metadata for Hubble and all other
available missions is also available through the `MAST Search UI <https://mast.stsci.edu/search/ui/#/>`_.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions()
   >>> missions.mission
   'hst'
   >>> missions.service
   'search'

Each ``MastMissions`` object can only make queries and download products from a single mission at a time. This mission can
be modified with the ``mission`` class attribute. This allows users to make queries to multiple missions with the same object.
To search for JWST metadata, the ``mission`` attribute is reassigned to ``'JWST'``.

.. doctest-remote-data::
   >>> m = MastMissions()
   >>> print(m.mission)
   hst
   >>> m.mission = 'JWST'
   >>> print(m.mission)
   jwst


Querying Missions
==================

The MastMissions interface provides three closely related query methods. All three methods return results as an `~astropy.table.Table` 
and all three support column-based filtering, sorting, and result limiting. The primary difference between them is how positional 
constraints are specified.

At a high level:
  - `~astroquery.mast.MastMissionsClass.query_criteria` is the most flexible method. It supports purely column-based queries, 
    purely positional queries, or a combination of both.

  - `~astroquery.mast.MastMissionsClass.query_region` is a convenience wrapper for positional queries using coordinates.

  - `~astroquery.mast.MastMissionsClass.query_object` is a convenience wrapper for positional queries using object names.

Query Parameters
----------------

The ``missions`` object can be used to search mission metadata by sky position,
object name, or other criteria. Keyword arguments may be used to specify output
characteristics and filter on values such as instrument, exposure type, and
principal investigator. The available column names for a mission can be retrieved
using the `~astroquery.mast.MastMissionsClass.get_column_list` method.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions(mission='hst')
   >>> columns = missions.get_column_list()

Keyword arguments can also be used to refine results further. The following parameters are available:

- ``radius``: For positional searches only. Only return results within a certain distance from an object or set of coordinates. 
  Default is 3 arcminutes.

- ``limit``: The maximum number of results to return. Default is 5000.

- ``offset``: Skip the first *n* results. Useful for paging through results.

- ``sort_by``: A string or list of field names to sort by.

- ``sort_desc``: A boolean or list of booleans (one for each field specified in
  ``sort_by``) indicating whether each field should be sorted in descending
  (``True``) or ascending (``False``) order.

- ``select_cols``: Columns to include in the result table. If not specified, a default set of columns
  is returned. This parameter may be given as an iterable of column names, a comma-separated string, or the special
  values ``'all'`` or ``'*'`` to return all available columns.

Writing Queries
----------------

The `~astroquery.mast.MastMissionsClass.query_criteria` method supports both positional parameters and column-based filters.
Positional constraints are optional. 

Supported positional parameters include:

  - ``coordinates`` : Sky coordinates around which to perform a cone search.
  - ``objectname`` : Name(s) of the object(s) around which to perform a cone search.
  - ``resolver`` : Resolver service to use for object name resolution.
  - ``radius`` : Radius of the cone searches around the specified coordinates or object names. Can be defined as an `~astropy.units.Quantity`, 
    a string with units (e.g., ``"10 arcsec"``), or a numeric value interpreted as degrees.

Multiple coordinates or objects may be queried in a single request. The ``coordinates`` and ``object_names`` parameters 
accept a single value, an iterable of values, or a comma-separated string. When multiple values are provided for either parameter,
results matching *any* of the supplied positions are returned.

.. doctest-remote-data::

   >>> from astropy.coordinates import SkyCoord
   >>> select_cols = ["sci_targname", "sci_pep_id", "sci_status"]
   >>> results = missions.query_criteria(coordinates=[SkyCoord(245.89675, -26.52575, unit='deg'), "205.54842 28.37728"], 
   ...                                   object_names=["M2", "M9"],
   ...                                   radius=0.1,
   ...                                   select_cols=select_cols,
   ...                                   sort_by='search_pos')
   >>> results.pprint(max_width=-1)  +IGNORE_OUTPUT
        search_pos     sci_data_set_name  sci_targname sci_pep_id       ang_sep        sci_status
   ------------------- ----------------- ------------- ---------- -------------------- ----------
   205.54842 28.37728          O5GX13010 NGC5272-BSSV6       8226  0.09983625899279894     PUBLIC
   205.54842 28.37728          O5GX13020 NGC5272-BSSV6       8226  0.09983625899279894     PUBLIC
   205.54842 28.37728          O5GX13030 NGC5272-BSSV6       8226  0.09983625899279894     PUBLIC
   245.89675 -26.52575         W0FX0301T       NGC6121       3111  0.04464557414882169     PUBLIC
   245.89675 -26.52575         W0FX0302T       NGC6121       3111  0.04464557414882169     PUBLIC
   245.89675 -26.52575         OC4U5RFMQ          DARK      13131  0.06347519519464637     PUBLIC
   245.89675 -26.52575         JC5GE5011          BIAS      13154  0.06347519583709554     PUBLIC
   245.89675 -26.52575         IBKH03020       NGC6121      12193   0.0687421385505865     PUBLIC
   245.89675 -26.52575         IBKH03030       NGC6121      12193   0.0687421385505865     PUBLIC
   245.89675 -26.52575         IBKH03040       NGC6121      12193   0.0687421385505865     PUBLIC
   259.79908 -18.51625         J9D613011   MESSIER-009      10573 0.009682839438074332     PUBLIC
   259.79908 -18.51625         J9D613I1Q   MESSIER-009      10573 0.009682839438074332     PUBLIC
   259.79908 -18.51625         J9D613I3Q   MESSIER-009      10573 0.009682839438074332     PUBLIC
   323.36258 -0.82325          ICAU46020  NGC-7089-M-2      13297  0.07051422608168086     PUBLIC
   323.36258 -0.82325          ICAU45020  NGC-7089-M-2      13297  0.07087801874163793     PUBLIC

You may notice that the above query returned more columns than were specified in the ``select_cols``
argument. For each mission, certain columns are automatically returned.

To filter results based on column values, users may specify criteria as keyword arguments,
where the keyword is the column name and the value is the desired filter. Multiple criteria are combined
using logical **AND**.

Criteria syntax supports several operations:

- Exact matches by specifying a single value for a column (e.g., ``sci_instrume='ACS'``).

- To filter by multiple values for a single column, provide a list of values or a comma-separated string.
  This performs an **OR** operation between the values.

- A filter value can be negated by prefixing it with ``!``, excluding rows that
  match that value. When negated values appear in a list, positive values are
  combined using **OR**, while negated values are applied using **AND** logic.

- For numeric or data columns, filter using comparison values (``<``, ``>``, ``<=``, ``>=``).

  - ``<``: Return values less than or before the given number/date
  - ``>``: Return values greater than or after the given number/date
  - ``<=``: Return values less than or equal to the given number/date
  - ``>=``: Return values greater than or equal to the given number/date

- For numeric or date columns, select an inclusive range with the syntax ``'#..#'``.

- Wildcards are special characters used in search patterns to represent one or more unknown characters, 
  allowing for flexible matching of strings. The wildcard character is ``*`` and it replaces any number
  of characters preceding, following, or in between existing characters, depending on its placement.

.. doctest-remote-data::

   >>> results = missions.query_criteria(sci_obs_type="IMAGE",
   ...                                   sci_instrume="!COS",
   ...                                   sci_spec_1234=["F150W", "F105W", "F110W"],
   ...                                   sci_dec=">0",
   ...                                   sci_actual_duration="1000..2000",
   ...                                   sci_targname="*GAL*",
   ...                                   select_cols=["sci_obs_type", "sci_spec_1234"])
   >>> results[:5].pprint(max_width=-1)  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
   sci_data_set_name       sci_targname      sci_spec_1234 sci_obs_type
   ----------------- ----------------------- ------------- ------------
        N9DB0C010       GAL-023031+002317         F110W        IMAGE
        N4A701010 GAL-CLUS-0026+1653-ARCA         F110W        IMAGE
        N4A704010 GAL-CLUS-0026+1653-ARCA         F110W        IMAGE
        N4A702010 GAL-CLUS-0026+1653-ARCC         F110W        IMAGE
        N4A705010 GAL-CLUS-0026+1653-ARCC         F110W        IMAGE

The `~astroquery.mast.MastMissionsClass.query_region` and `~astroquery.mast.MastMissionsClass.query_object` methods are 
convenience wrappers around `~astroquery.mast.MastMissionsClass.query_criteria`:

  - `~astroquery.mast.MastMissionsClass.query_region` requires ``coordinates``.

  - `~astroquery.mast.MastMissionsClass.query_object` requires ``object_names`` and an optional ``resolver``.

Both methods also accept column-based criteria, which are applied in the same way as in `~astroquery.mast.MastMissionsClass.query_criteria`.

.. doctest-remote-data::

   >>> regionCoords = SkyCoord(210.80227, 54.34895, unit=('deg', 'deg'))
   >>> select_cols = ["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"]
   >>> results = missions.query_region(regionCoords, 
   ...                                 radius=3,
   ...                                 sci_pep_id=12556,
   ...                                 select_cols=select_cols,
   ...                                 sort_by='sci_targname')
   >>> results[:5].pprint(max_width=-1)   # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    search_pos     sci_data_set_name   sci_targname         sci_start_time             sci_stop_time              ang_sep        sci_status
   ------------------ ----------------- ---------------- -------------------------- -------------------------- -------------------- ----------
   210.80227 54.34895         OBQU01050 NUCLEUS+HODGE602 2012-05-24T07:51:40.553000 2012-05-24T07:54:46.553000 0.017460048037303017     PUBLIC
   210.80227 54.34895         OBQU010H0 NUCLEUS+HODGE602 2012-05-24T09:17:38.570000 2012-05-24T09:20:44.570000 0.017460048037303017     PUBLIC
   210.80227 54.34895         OBQU01030 NUCLEUS+HODGE602 2012-05-24T07:43:20.553000 2012-05-24T07:46:26.553000 0.022143836477276503     PUBLIC
   210.80227 54.34895         OBQU010F0 NUCLEUS+HODGE602 2012-05-24T09:09:18.570000 2012-05-24T09:12:24.570000 0.022143836477276503     PUBLIC
   210.80227 54.34895         OBQU01070 NUCLEUS+HODGE602 2012-05-24T08:00:00.553000 2012-05-24T08:03:06.553000  0.04381046755938432     PUBLIC

.. doctest-remote-data::

   >>> results = missions.query_object('M101', 
   ...                                 radius=3, 
   ...                                 select_cols=select_cols,
   ...                                 sort_by='sci_targname')
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    search_pos     sci_data_set_name sci_targname       sci_start_time             sci_stop_time             ang_sep       sci_status
   ------------------ ----------------- ------------ -------------------------- -------------------------- ------------------ ----------
   210.80243 54.34875         LDJI01010   +164.6+9.9 2019-02-19T00:49:58.010000 2019-02-19T05:52:40.020000 2.7469653000840397     PUBLIC
   210.80243 54.34875         J8OB02011          ANY 2003-08-27T07:44:47.417000 2003-08-27T08:27:34.513000 0.8111299061221189     PUBLIC
   210.80243 54.34875         J8D711J1Q          ANY 2003-01-17T00:42:06.993000 2003-01-17T00:50:22.250000 1.1297984178946574     PUBLIC
   210.80243 54.34875         JD6V01012          ANY 2017-06-15T18:10:12.037000 2017-06-15T18:33:25.983000 1.1541053362381077     PUBLIC
   210.80243 54.34875         JD6V01013          ANY 2017-06-15T19:45:30.023000 2017-06-15T20:08:44.063000   1.15442580192948     PUBLIC


Retrieving Data Products
========================

Getting Product Lists
----------------------

Each observation returned from a MAST query can have one or more associated data products. Given
one or more datasets or dataset IDs, the `~astroquery.mast.MastMissionsClass.get_product_list` function 
will return a `~astropy.table.Table` containing the associated data products.

`~astroquery.mast.MastMissionsClass.get_product_list` also includes an optional ``batch_size`` parameter, 
which controls how many datasets are sent to the MAST service per request. This can be useful for managing 
memory usage or avoiding timeouts when requesting product lists for large numbers of datasets.
If not provided, batch_size defaults to 1000.

.. doctest-remote-data::
   >>> datasets = missions.query_criteria(sci_pep_id=12451,
   ...                                    sci_instrume='ACS',
   ...                                    sci_hlsp='>1')
   >>> products = missions.get_product_list(datasets[:2], batch_size=1000)
   >>> print(products[:5])  # doctest: +IGNORE_OUTPUT
           product_key          access  dataset  ...  category     size     type 
   ---------------------------- ------ --------- ... ---------- --------- -------
   JBTAA0010_jbtaa0010_asn.fits PUBLIC JBTAA0010 ...        AUX     11520 science
   JBTAA0010_jbtaa0010_drz.fits PUBLIC JBTAA0010 ... CALIBRATED 214655040 science
   JBTAA0010_jbtaa0010_trl.fits PUBLIC JBTAA0010 ...        AUX    630720 science
   JBTAA0010_jbtaa0010_drc.fits PUBLIC JBTAA0010 ... CALIBRATED 214657920 science
   JBTAA0010_jbtaa0010_log.txt PUBLIC JBTAA0010 ...        AUX    204128 science

The keyword corresponding to the dataset ID varies between missions and can be returned with the
`~astroquery.mast.MastMissionsClass.get_dataset_kwd` method.

.. doctest-remote-data::
   >>> dataset_id_kwd = missions.get_dataset_kwd()
   >>> print(dataset_id_kwd)
   sci_data_set_name
   >>> products = missions.get_product_list(datasets[:2][dataset_id_kwd])

Some products may be associated with multiple datasets, and this table may contain duplicates.
To return a list of products with unique filenames, use the `~astroquery.mast.MastMissionsClass.get_unique_product_list`
function.

.. doctest-remote-data::
   >>> unique_products = missions.get_unique_product_list(datasets[:2])  # doctest: +IGNORE_OUTPUT
   INFO: 16 of 206 products were duplicates. Only returning 190 unique product(s). [astroquery.mast.utils]
   INFO: To return all products, use `MastMissions.get_product_list` [astroquery.mast.missions]

Filtering Data Products
-----------------------

In many cases, you will not need to download every product that is associated with a dataset. The
`~astroquery.mast.MastMissionsClass.filter_products` function allows for filtering based on file extension (``extension``)
and any other of the product fields.

The **AND** operation is applied between filters, and the **OR** operation is applied within each filter set, except in the case of negated values.

A filter value can be negated by prefiing it with ``!``, meaning that rows matching that value will be excluded from the results.
When any negated value is present in a filter set, any positive values in that set are combined with **OR** logic, and the negated 
values are combined with **AND** logic against the positives. 

For example:
  - ``file_suffix=['A', 'B', '!C']`` → (file_suffix != C) AND (file_suffix == A OR file_suffix == B)
  - ``size=['!14400', '<20000']`` → (size != 14400) AND (size < 20000)

For columns with numeric data types (``int`` or ``float``), filter values can be expressed in several ways:
  - A single number: ``size=100``
  - A range in the form "start..end": ``size="100..1000"``
  - A comparison operator followed by a number: ``size=">=1000"``
  - A list of expressions (OR logic): ``size=[100, "500..1000", ">=1500"]``

The filter below returns FITS products that are "science" type **and** less than or equal to 20,000 bytes in size
**and** have a ``file_suffix`` of "ASN" (association files) **or** "JIF" (job information files).

.. doctest-remote-data::
   >>> filtered = missions.filter_products(products,
   ...                                     extension='fits',
   ...                                     type='science',
   ...                                     size='<=20000',        
   ...                                     file_suffix=['ASN', 'JIF'])
   >>> print(filtered)  # doctest: +IGNORE_OUTPUT
         product_key          access  dataset  ...    category     size   type 
   ---------------------------- ------ --------- ... -------------- ----- -------
   JBTAA0010_jbtaa0010_asn.fits PUBLIC JBTAA0010 ...            AUX 11520 science
   JBTAA0020_jbtaa0020_asn.fits PUBLIC JBTAA0020 ...            AUX 11520 science


Downloding Data
===============

Downloading Data Products
-------------------------

The `~astroquery.mast.MastMissionsClass.download_products` function accepts a table of products like the one above 
and will download the products to your local machine. Products may also be provided as dataset IDs with product filters, 
or as JSON product metadata sent by the MAST subscription service (either as a local JSON file or as in-memory data).

By default, products will be downloaded into the current working directory, in a subdirectory called ``mastDownload``.
The full local filepaths will have the form ``mastDownload/<mission>/<Dataset ID>/file.`` You can change the download 
directory using the ``download_dir`` parameter. If ``flat=True`` is specified, all files will be downloaded directly into the 
``download_dir`` without any subdirectories.

.. doctest-remote-data::
   >>> manifest = missions.download_products(filtered)  # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0010%2Fjbtaa0010_asn.fits to mastDownload/hst/JBTAA0010/jbtaa0010_asn.fits ... [Done]
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0010%2Fjbtaa0010_jif.fits to mastDownload/hst/JBTAA0010/jbtaa0010_jif.fits ... [Done]
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0020%2Fjbtaa0020_asn.fits to mastDownload/hst/JBTAA0020/jbtaa0020_asn.fits ... [Done]
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0020%2Fjbtaa0020_jif.fits to mastDownload/hst/JBTAA0020/jbtaa0020_jif.fits ... [Done]
   >>> print(manifest)  # doctest: +IGNORE_OUTPUT
                     Local Path                   Status  Message URL 
   --------------------------------------------- -------- ------- ----
   mastDownload/hst/JBTAA0010/jbtaa0010_asn.fits COMPLETE    None None
   mastDownload/hst/JBTAA0010/jbtaa0010_jif.fits COMPLETE    None None
   mastDownload/hst/JBTAA0020/jbtaa0020_asn.fits COMPLETE    None None
   mastDownload/hst/JBTAA0020/jbtaa0020_jif.fits COMPLETE    None None

The function also accepts dataset IDs and product filters as input for a more streamlined workflow. 

.. doctest-remote-data::
   >>> missions.download_products(['JBTAA0010', 'JBTAA0020'],
   ...                            extension='fits',
   ...                            type='science',
   ...                            file_suffix=['ASN', 'JIF'])  # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0010%2Fjbtaa0010_asn.fits to mastDownload/hst/JBTAA0010/jbtaa0010_asn.fits ... [Done]
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0010%2Fjbtaa0010_jif.fits to mastDownload/hst/JBTAA0010/jbtaa0010_jif.fits ... [Done]
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0020%2Fjbtaa0020_asn.fits to mastDownload/hst/JBTAA0020/jbtaa0020_asn.fits ... [Done]
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0020%2Fjbtaa0020_jif.fits to mastDownload/hst/JBTAA0020/jbtaa0020_jif.fits ... [Done]

Downloading a Single File
-------------------------

To download a single data product file, use the `~astroquery.mast.MastMissionsClass.download_file` function with
a MAST URI as input. Some missions (e.g., HST, JWST) accept direct filenames as input, but others require a fully-qualified ``mast:`` URI.

The default is to download the file to the current working directory, but you can specify the download directory or filepath with 
the ``local_path`` keyword argument.

.. doctest-remote-data::
   >>> result = missions.download_file('JBTAA0010/jbtaa0010_asn.fits')
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0010%2Fjbtaa0010_asn.fits to jbtaa0010_asn.fits ... [Done]
   >>> print(result)
   ('COMPLETE', None, None)
