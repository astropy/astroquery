
****************
Mission Searches
****************

The `~astroquery.mast.MastMissionsClass` class allows for search queries based on mission-specific 
metadata for a given data collection. This metadata includes header keywords, proposal information, and observational parameters.
The following missions/products are currently available for search:

- `Hubble Space Telescope <https://www.stsci.edu/hst>`_ (``'hst'``)

- `James Webb Space Telescope <https://www.stsci.edu/jwst>`_ (``'jwst'``)

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

The ``missions`` object can be used to search metadata by sky position, object name, or other criteria.
When writing queries, keyword arguments can be used to specify output characteristics and filter on 
values like instrument, exposure type, and principal investigator. The available column names for a 
mission are returned by the `~astroquery.mast.MastMissionsClass.get_column_list` function.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions(mission='hst')
   >>> columns = missions.get_column_list()

Keyword arguments can also be used to refine results further. The following parameters are available:

- ``radius``: For positional searches only. Only return results within a certain distance from an object or set of coordinates. 
  Default is 3 arcminutes.

- ``limit``: The maximum number of results to return. Default is 5000.

- ``offset``: Skip the first ***n*** results. Useful for paging through results.

- ``sort_by``: A string or list of field names to sort by.

- ``sort_desc``: A boolean or list of booleans (one for each field specified in ``sort_by``),
  describing if each field should be sorted in descending order (``True``) or ascending order (``False``).

- ``select_cols``: A list of columns to be returned in the response.


Mission Positional Queries
===========================

Metadata queries can be performed on a particular region in the sky. Passing in a set of coordinates to the 
`~astroquery.mast.MastMissionsClass.query_region` function returns datasets that fall within a
certain radius value of that point. This type of search is also known as a cone search.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> from astropy.coordinates import SkyCoord
   >>> missions = MastMissions(mission='hst')
   >>> regionCoords = SkyCoord(210.80227, 54.34895, unit=('deg', 'deg'))
   >>> results = missions.query_region(regionCoords, 
   ...                                 radius=3,
   ...                                 sci_pep_id=12556,
   ...                                 select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by='sci_targname')
   >>> results[:5]   # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    search_pos     sci_data_set_name   sci_targname         sci_start_time             sci_stop_time              ang_sep        sci_status
   ------------------ ----------------- ---------------- -------------------------- -------------------------- -------------------- ----------
   210.80227 54.34895         OBQU01050 NUCLEUS+HODGE602 2012-05-24T07:51:40.553000 2012-05-24T07:54:46.553000 0.017460048037303017     PUBLIC
   210.80227 54.34895         OBQU010H0 NUCLEUS+HODGE602 2012-05-24T09:17:38.570000 2012-05-24T09:20:44.570000 0.017460048037303017     PUBLIC
   210.80227 54.34895         OBQU01030 NUCLEUS+HODGE602 2012-05-24T07:43:20.553000 2012-05-24T07:46:26.553000 0.022143836477276503     PUBLIC
   210.80227 54.34895         OBQU010F0 NUCLEUS+HODGE602 2012-05-24T09:09:18.570000 2012-05-24T09:12:24.570000 0.022143836477276503     PUBLIC
   210.80227 54.34895         OBQU01070 NUCLEUS+HODGE602 2012-05-24T08:00:00.553000 2012-05-24T08:03:06.553000  0.04381046755938432     PUBLIC

You may notice that the above query returned more columns than were specified in the ``select_cols``
argument. For each mission, certain columns are automatically returned.

- *HST*: For positional searches, the columns ``sci_data_set_name``, ``search_pos``, and ``ang_sep``
  are always included in the query results. For non-positional searches, ``sci_data_set_name`` is always 
  present.

- *JWST*: For every query, the ``ArchiveFileID`` column is always returned.

- *CLASSY*: For positional searches, the columns ``search_pos``, ``Target``, and ``ang_sep`` are always included.
  For non-positional searches, ``Target`` is always returned.

- *ULLYSES*: For positional searches, the columns ``search_pos``, ``target_id``, ``names_search``, ``target_name_hlsp``,
  ``simbad_link``, ``ang_sep``, and ``plot_preview`` are always included. For non-positional searches, ``target_id``, 
  ``target_name_hlsp``, ``simbad_link``, and ``observation_id`` are always returned.

Searches can also be run on target names with the `~astroquery.mast.MastMissionsClass.query_object` 
function.

.. doctest-remote-data::

   >>> results = missions.query_object('M101', 
   ...                                 radius=3, 
   ...                                 select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
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


Mission Criteria Queries
=========================

For non-positional metadata queries, use the `~astroquery.mast.MastMissionsClass.query_criteria` 
function.

.. doctest-remote-data::

   >>> results = missions.query_criteria(sci_start_time=">=2021-01-01 00:00:00",
   ...                                   select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status", "sci_pep_id"],
   ...                                   sort_by='sci_pep_id',
   ...                                   limit=1000,
   ...                                   offset=1000)  # doctest: +IGNORE_WARNINGS
   ... # MaxResultsWarning('Maximum results returned, may not include all sources within radius.')
   >>> len(results)
   1000

Here are some tips and tricks for writing more advanced queries:

- To exclude and filter out a certain value from the results, prepend the value with ``!``.

- To filter by multiple values for a single column, use a list of values or a string of values delimited by commas.

- For columns with numeric or date data types, filter using comparison values (``<``, ``>``, ``<=``, ``>=``).

  - ``<``: Return values less than or before the given number/date

  - ``>``: Return values greater than or after the given number/date

  - ``<=``: Return values less than or equal to the given number/date

  - ``>=``: Return values greater than or equal to the given number/date

- For columns with numeric or date data types, select a range with the syntax ``'#..#'``.

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
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
   sci_data_set_name       sci_targname      sci_spec_1234 sci_obs_type
   ----------------- ----------------------- ------------- ------------
        N9DB0C010       GAL-023031+002317         F110W        IMAGE
        N4A701010 GAL-CLUS-0026+1653-ARCA         F110W        IMAGE
        N4A704010 GAL-CLUS-0026+1653-ARCA         F110W        IMAGE
        N4A702010 GAL-CLUS-0026+1653-ARCC         F110W        IMAGE
        N4A705010 GAL-CLUS-0026+1653-ARCC         F110W        IMAGE

Downloding Data
===============

Getting Product Lists
----------------------

Each observation returned from a MAST query can have one or more associated data products. Given
one or more datasets or dataset IDs, the `~astroquery.mast.MastMissionsClass.get_product_list` function 
will return a `~astropy.table.Table` containing the associated data products.

.. doctest-remote-data::
   >>> datasets = missions.query_criteria(sci_pep_id=12451,
   ...                                    sci_instrume='ACS',
   ...                                    sci_hlsp='>1')
   >>> products = missions.get_product_list(datasets[:2])
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

The **AND** operation is performed for a list of filters, and the **OR** operation is performed within a filter set. 
For example, the filter below will return FITS products that are "science" type **and** have a ``file_suffix`` of "ASN" (association
files) **or** "JIF" (job information files).

.. doctest-remote-data::
   >>> filtered = missions.filter_products(products,
   ...                                     extension='fits',
   ...                                     type='science',
   ...                                     file_suffix=['ASN', 'JIF'])
   >>> print(filtered)  # doctest: +IGNORE_OUTPUT
         product_key          access  dataset  ...    category     size   type 
   ---------------------------- ------ --------- ... -------------- ----- -------
   JBTAA0010_jbtaa0010_asn.fits PUBLIC JBTAA0010 ...            AUX 11520 science
   JBTAA0010_jbtaa0010_jif.fits PUBLIC JBTAA0010 ... JITTER/SUPPORT 60480 science
   JBTAA0020_jbtaa0020_asn.fits PUBLIC JBTAA0020 ...            AUX 11520 science
   JBTAA0020_jbtaa0020_jif.fits PUBLIC JBTAA0020 ... JITTER/SUPPORT 60480 science

Downloading Data Products
-------------------------

The `~astroquery.mast.MastMissionsClass.download_products` function accepts a table of products like the one above 
and will download the products to your local machine.

By default, products will be downloaded into the current working directory, in a subdirectory called "mastDownload".
The full local filepaths will have the form "mastDownload/<mission>/<Dataset ID>/file." You can change the download 
directory using the ``download_dir`` parameter.

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
a MAST URI as input. The default is to download the file to the current working directory, but
you can specify the download directory or filepath with the ``local_path`` keyword argument.

.. doctest-remote-data::
   >>> result = missions.download_file('JBTAA0010/jbtaa0010_asn.fits')
   Downloading URL https://mast.stsci.edu/search/hst/api/v0.1/retrieve_product?product_name=JBTAA0010%2Fjbtaa0010_asn.fits to jbtaa0010_asn.fits ... [Done]
   >>> print(result)
   ('COMPLETE', None, None)
