
*******************
Observation Queries
*******************

The `~astroquery.mast.ObservationsClass` class provides the primary interface for querying
observational metadata and data products archived at MAST. It enables users to search
across missions, instruments, and observing programs using positional constraints, object
names, and rich sets of metadata-based filters.

This class provides programmatic access to the `MAST Portal API <https://mast.stsci.edu/api/v0/>`__,
which is the same backend used by the `MAST Web Portal <https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html>`_ 
for data discovery and retrieval. It is designed to support a wide range of workflows, from simple cone 
searches to complex, multi-criteria queries. Query results are returned as `~astropy.table.Table` objects, 
making them easy to inspect, filter, and integrate into downstream analysis pipelines.

In addition to discovering observations, the `~astroquery.mast.ObservationsClass` interface supports retrieving
associated data products, filtering products based on scientific relevance, and downloading
files either directly from MAST or from cloud-hosted public datasets when available. These
capabilities make it the recommended starting point for most users who wish to search for and
retrieve archival data from MAST.

The sections below describe the different query modes supported by the `~astroquery.mast.ObservationsClass` class,
how to refine and interpret query results, and how to access the corresponding data products.

Metadata Queries
================

To return a list of missions with data archived at MAST, use the `~astroquery.mast.ObservationsClass.list_missions` method.
This can be useful for exploring the scope of the archive, validating mission names for use in query filters, or
programmatically discovering which missions are supported for observational searches.

.. doctest-remote-data::
   
   >>> from astroquery.mast import Observations
   ...
   >>> print(Observations.list_missions())  # doctest: +IGNORE_OUTPUT
   ['BEFS', 'EUVE', 'FIMS-SPEAR', 'FUSE', 'GALEX', 'HLA', 'HLSP', 'HST', 'HUT', 'IUE', 'JWST', 'K2', 'K2FFI', 'Kepler', 'KeplerFFI', 'OPO', 'PS1', 'SDSS', 'SPITZER_SHA', 'SWIFT', 'TESS', 'TUES', 'WUPPE']

Query results include a wide range of metadata fields describing each observation or data product. To get a table
of metadata associated with observation or product results, use the `~astroquery.mast.ObservationsClass.get_metadata` method.
The ``query_type`` parameter accepts either "observations" or "products" to return the corresponding metadata table.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> meta_table = Observations.get_metadata("observations")
   >>> print(meta_table[:5])  # doctest: +IGNORE_OUTPUT
     Column Name     Column Label   ...       Examples/Valid Values
   --------------- ---------------- ... ----------------------------------
        intentType Observation Type ... Valid values: science, calibration
    obs_collection          Mission ...          E.g. SWIFT, PS1, HST, IUE
   provenance_name  Provenance Name ...           E.g. TASOC, CALSTIS, PS1
   instrument_name       Instrument ...     E.g. WFPC2/WFC, UVOT, STIS/CCD
           project          Project ...    E.g. HST, HLA, EUVE, hlsp_legus
   ...
   >>> meta_table = Observations.get_metadata("products")
   >>> print(meta_table[:3])  # doctest: +IGNORE_OUTPUT
    Column Name     Column Label   ...         Examples/Valid Values
   -------------- ---------------- ... -------------------------------------
           obs_id   Observation ID ...                  U24Z0101T, N4QF18030
            obsID Product Group ID ...         Long integer, e.g. 2007590987
   obs_collection          Mission ... HST, HLA, SWIFT, GALEX, Kepler, K2...


Observation Queries
===================

The `~astroquery.mast.ObservationsClass` interface provides several complementary ways to search for observational
metadata archived at MAST. Queries may be based on **sky position, object name, or
arbitrary metadata criteria**, and all methods return results in a consistent tabular
format that can be further refined or used to retrieve data products.

All query methods return results as an `~astropy.table.Table`, where each row corresponds to a
single observation. The table includes metadata such as mission name, instrument, target name,
observation time, and identifiers needed to retrieve associated data products. The exact set of returned columns is defined by the
Common Archive Observation Model (CAOM). Users can inspect available columns and their meanings using
``Observations.get_metadata("observations")`` or by visiting the
`MAST CAOM Fields Descriptions <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

Positional Queries
------------------

Positional queries search for observations whose footprints intersect a circular region on
the sky. The search region is defined by a central position and a radius.

The ``radius`` parameter may be provided as:
- An `~astropy.units.Quantity` with angular units (recommended)
- A string parsable by `~astropy.coordinates.Angle` (e.g., "0.1 deg", "5 arcmin", "120 arcsec")
- A numeric value, which is interpreted as degrees

If not specified, a default radius of **0.2 degrees** is used. Choosing an appropriate radius
is important: small radii are useful for targeted searches around known sources, while larger
radii can be helpful for exploratory searches or extended targets but may return many more
results.

To search using explicit sky coordinates, use the
`~astroquery.mast.ObservationsClass.query_region` method. The ``coordinates`` parameter may be
provided as a string (e.g., "322.49324 12.16683") or as an
`~astropy.coordinates` object (e.g., `~astropy.coordinates.SkyCoord`).

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_region("322.49324 12.16683", radius="0.1 deg")
   >>> print(obs_table[:5])  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... srcDen   obsid   distance
   ---------- -------------- --------------- ... ------ --------- --------
      science           TESS            SPOC ...    nan  95133321      0.0
      science           TESS            SPOC ...    nan 232881350      0.0
      science           TESS            SPOC ...    nan  93770500      0.0
      science           TESS            SPOC ...    nan 232652269      0.0
      science           TESS            SPOC ...    nan 232652273      0.0

To search using a resolvable object name, use the `~astroquery.mast.ObservationsClass.query_object` method,
which resolves the name to sky coordinates and performs a positional search centered on the resolved location.

.. doctest-remote-data::

   >>> obs_table = Observations.query_object("M8", radius=".02 deg")
   >>> print(obs_table[:5])  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... srcDen    obsid    distance
   ---------- -------------- --------------- ... ------ ----------- --------
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0


Criteria-Based Queries
----------------------

In addition to positional searches, observations may be queried using metadata
criteria such as mission name, instrument, filters, proposal information, or observation
time. These queries are performed using the `~astroquery.mast.ObservationsClass.query_criteria` method.
Valid cr

Criteria are specified as keyword arguments corresponding to column names in the observation
metadata table, as returned by ``Observations.get_metadata("observations")``. 
At least one **non-positional** criterion must be supplied.

For criteria with discrete values (e.g., mission name, instrument), values may be provided as:
  - A single string or number
  - A list of strings or numbers (interpreted with OR logic)

Discrete values also accept wildcard characters (``*`` or ``%``) for pattern matching. Wildcards are special characters
used in search patterns to represent one or more unknown characters, allowing for flexible matching of strings. 
Each wildcard character replaces any number of characters preceding, following, or in between existing characters, depending on its placement.
However, only one wildcarded value can be processed per criterion.

For criteria with continuous values (e.g., observation time, exposure time), values should be in the form
``[minVal, maxVal]`` to specify a range. Datetime values must be provided in Modified Julian Date (MJD) format.

The following example demonstrates a crtieria-based query with list matching, a wildcard, and a range value:

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(dataproduct_type="image",  # Exact match on data product type
   ...                                         proposal_id=[11897, 12715],  # Match either proposal ID
   ...                                         proposal_pi="Osten*",  # Wildcard match on PI name
   ...                                         em_min=[100, 200])  # Range match on minimum wavelength
   >>> print(obs_table[:5])  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... srcDen  obsid     objID  
   ---------- -------------- --------------- ... ------ -------- ---------
      science            HST          CALCOS ...    nan 24139596 144540274
      science            HST          CALCOS ...    nan 24139591 144540276
      science            HST          CALCOS ...    nan 24139580 144540277
      science            HST          CALCOS ...    nan 24139597 144540280
      science            HST          CALCOS ...    nan 24139575 144540281

We encourage the use of wildcards particularly when querying for JWST observations
with the ``instrument_name`` criteria. This is because of the varying instrument names
for JWST science instruments, which you can read more about on the MAST page for
`JWST Instrument Names <https://outerspace.stsci.edu/display/MASTDOCS/JWST+Instrument+Names>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(proposal_pi="Espinoza, Nestor",
   ...                                         instrument_name="NIRISS*")
   >>> set(obs_table['instrument_name'])  # doctest: +IGNORE_OUTPUT
   {'NIRISS', 'NIRISS/IMAGE', 'NIRISS/SOSS'}

You can also perform positional queries with additional criteria by passing in ``objectname``, ``coordinates``,
and/or ``radius`` as keyword arguments.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(objectname="M10",
   ...                                         radius="0.1 deg",
   ...                                         filters=["*UV","Kepler"],
   ...                                         obs_collection="GALEX")
   >>> print(obs_table)  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... objID objID1 distance
   ---------- -------------- --------------- ... ----- ------ --------
      science          GALEX             AIS ... 61675  61675      0.0
      science          GALEX             GII ...  7022   7022      0.0
      science          GALEX             GII ... 78941  78941      0.0
      science          GALEX             AIS ... 61673  61673      0.0
      science          GALEX             GII ...  7023   7023      0.0
      science          GALEX             AIS ... 61676  61676      0.0
      science          GALEX             AIS ... 61674  61674      0.0


Getting Observation Counts
--------------------------

For cases where only the number of matching observations is needed, count-only variants of
the positional and criteria-based queries are available:

- `~astroquery.mast.ObservationsClass.query_region_count`
- `~astroquery.mast.ObservationsClass.query_object_count`
- `~astroquery.mast.ObservationsClass.query_criteria_count`

These methods return an integer count instead of a full metadata table and are useful for
quickly estimating result sizes before issuing a full query or iteratively adjusting search
parameters.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> print(Observations.query_region_count("322.49324 12.16683", radius=0.001))  # doctest: +IGNORE_OUTPUT
   6338
   ...
   >>> print(Observations.query_object_count("M8",radius=".02 deg"))  # doctest: +IGNORE_OUTPUT
   469
   ...
   >>> print(Observations.query_criteria_count(proposal_id=8880))  # doctest: +IGNORE_OUTPUT
   8

Retrieving Data Products
========================

Querying observations returns metadata describing *where* and *how* data were taken. To access
the actual data files associated with those observations, the `~astroquery.mast.ObservationsClass` interface
provides tools for discovering, filtering, and downloading data products. Each observation archived at MAST 
may be associated with one or more data products, such as images, spectra, time-series files, previews, or ancillary metadata.

Getting Product Lists
---------------------

Given one or more observations (or their corresponding MAST Product Group IDs, ``"obsid"``), the 
`~astroquery.mast.ObservationsClass.get_product_list` method returns a table of associated data products.

The returned results are in the form of an `~astropy.table.Table`, where each row corresponds to a single data product.
Available product metadata fields can be accessed using ``Observations.get_metadata("products")`` or by visiting the
`MAST Products Fields Descriptions <https://mast.stsci.edu/api/v0/_productsfields.html>`__.

The input to `~astroquery.mast.ObservationsClass.get_product_list` may be:
  - A table or row returned from an observation query method
  - A single ``obsid`` value
  - A list of ``obsid`` values

Note that the input to `~astroquery.mast.ObservationsClass.get_product_list` **must** be the MAST Product Group ID,
(``"obsid"``), and **not** the mission-specific observation identifier (``"obs_id"``). These identifiers are not interchangeable.
Attempting to use ``"obs_id"`` values will result in an error.

`~astroquery.mast.ObservationsClass.get_product_list` also includes an optional ``batch_size`` parameter, 
which controls how many observations are sent to the MAST service per request. This can be useful for managing 
memory usage or avoiding timeouts when requesting product lists for large numbers of observations. 
If not provided, batch_size defaults to 500.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(objectname="M8", obs_collection=["K2", "IUE"])
   >>> data_products_by_obs = Observations.get_product_list(obs_table[0:2], batch_size=500)
   >>> print(data_products_by_obs)  # doctest: +IGNORE_OUTPUT
   obsID  obs_collection dataproduct_type ... dataRights calib_level filters
   ------ -------------- ---------------- ... ---------- ----------- -------
   664784             K2       timeseries ...     PUBLIC           2  KEPLER
   664785             K2       timeseries ...     PUBLIC           2  KEPLER

Getting Unique Products
^^^^^^^^^^^^^^^^^^^^^^^

In many cases, multiple observations may reference the same underlying data product. To return a de-duplicated list
of products, use `~astroquery.mast.ObservationsClass.get_unique_product_list`.

This method behaves similarly to `~astroquery.mast.ObservationsClass.get_product_list`, but filters out duplicate products based on their
``"dataURI"`` values. This is particularly useful when querying large sets of observations that may share common data products. If 
duplicate products are found, an informational message is logged indicating how many unique products are being returned.

.. doctest-remote-data::
   >>> obs = Observations.query_criteria(obs_collection='HST',
   ...                                   filters='F606W',
   ...                                   instrument_name='ACS/WFC',
   ...                                   proposal_id=['12062'],
   ...                                   dataRights='PUBLIC')
   >>> unique_products = Observations.get_unique_product_list(obs)
   INFO: 180 of 370 products were duplicates. Only returning 190 unique product(s). [astroquery.mast.utils]
   INFO: To return all products, use `Observations.get_product_list` [astroquery.mast.observations]
   >>> print(unique_products[:10]['dataURI'])
                   dataURI                 
   ----------------------------------------
   mast:HST/product/jbeveoesq_flt_hlet.fits
      mast:HST/product/jbeveoesq_spt.fits
      mast:HST/product/jbeveoesq_trl.fits
         mast:HST/product/jbeveoesq_log.txt
         mast:HST/product/jbeveoesq_raw.jpg
         mast:HST/product/jbeveoesq_flc.jpg
         mast:HST/product/jbeveoesq_flt.jpg
      mast:HST/product/jbeveoesq_flc.fits
      mast:HST/product/jbeveoesq_flt.fits
      mast:HST/product/jbeveoesq_raw.fits

Filtering Data Products
-----------------------

Often, not all associated products are of interest for a given analysis. The 
`~astroquery.mast.ObservationsClass.filter_products` method allows users to filter product tables.

Products may be filtered by:
  - Minimum Recommended Products (``mrp_only=True``)
  - File extension (e.g., ``extension="fits"``)
  - Any other product metadata field (e.g., ``productType="SCIENCE"``)

Filters are combined using **AND** logic between different fields and **OR** logic within a single field,
except when negated values are present.

A filter value can be negated by prefiing it with ``!``, meaning that rows matching that value will be excluded from the results.
When any negated value is present in a filter set, any positive values in that set are combined with **OR** logic, and the negated 
values are combined with **AND** logic against the positives. 

For example:
  - ``productType=['A', 'B', '!C']`` → (productType != C) AND (productType == A OR productType == B)
  - ``size=['!14400', '<20000']`` → (size != 14400) AND (size < 20000)

For columns with numeric data types (``int`` or ``float``), filter values may be expressed as:
  - A single number: ``size=100``
  - A range in the form "start..end": ``size="100..1000"``
  - A comparison operator followed by a number: ``size=">=1000"``
  - A list of expressions: ``size=[100, "500..1000", ">=1500"]``

The filter below returns FITS products that have a calibration level of 2 or lower **and** are of type "SCIENCE" **or** "PREVIEW".

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> data_products = Observations.get_product_list('25588063')
   >>> filtered = Observations.filter_products(data_products,
   ...                                         extension="fits",
   ...                                         calib_level="<=2",
   ...                                         productType=["SCIENCE", "PREVIEW"])
   >>> print(filtered)  # doctest: +IGNORE_OUTPUT
    obsID   obs_collection dataproduct_type ... dataRights calib_level filters
   -------- -------------- ---------------- ... ---------- ----------- -------
   25167183            HLA            image ...     PUBLIC           2   F487N
   24556691            HST            image ...     PUBLIC           2   F487N
   24556691            HST            image ...     PUBLIC           2   F487N
   24556691            HST            image ...     PUBLIC           2   F487N
   24556691            HST            image ...     PUBLIC           2   F487N
   24556691            HST            image ...     PUBLIC           1   F487N
   24556691            HST            image ...     PUBLIC           1   F487N
   24556691            HST            image ...     PUBLIC           2   F487N

The filtered product table can then be passed to the download and cloud access methods, described below.

Downloading Data
================

Once you have identified the data products of interest, the `~astroquery.mast.ObservationsClass` interface
provides methods for downloading those files directly to your local machine. This workflow is suitable for
offline analysis or when working with small to moderate amounts of data.

Downloading Data Products
-------------------------

The primary method for downloading multiple files is `~astroquery.mast.ObservationsClass.download_products`.
This method accepts a table of data products such as those returned by
`~astroquery.mast.ObservationsClass.get_product_list` or `~astroquery.mast.ObservationsClass.get_unique_product_list`
and downloads the corresponding files.

By default, files are downloaded into a directory called ``mastDownload`` within the current working directory.
Within this directory, files are organized by mission and observation ID. The download location can be customized
using the ``download_dir`` keyword argument.

For convience, `~astroquery.mast.ObservationsClass.download_products` supports the same filtering options as
`~astroquery.mast.ObservationsClass.filter_products`. This allows users to select only a subset of files to download.

.. doctest-skip::

   >>> from astroquery.mast import Observations
   ...
   >>> single_obs = Observations.query_criteria(obs_collection="IUE", obs_id="lwp13058")
   >>> data_products = Observations.get_product_list(single_obs)
   ...
   >>> manifest = Observations.download_products(data_products, productType="SCIENCE")
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=http://archive.stsci.edu/pub/iue/data/lwp/13000/lwp13058.mxlo.gz to ./mastDownload/IUE/lwp13058/lwp13058.mxlo.gz ... [Done]
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=http://archive.stsci.edu/pub/vospectra/iue2/lwp13058mxlo_vo.fits to ./mastDownload/IUE/lwp13058/lwp13058mxlo_vo.fits ... [Done]
   ...
   >>> print(manifest)
                      Local Path                     Status  Message URL
   ------------------------------------------------ -------- ------- ----
       ./mastDownload/IUE/lwp13058/lwp13058.mxlo.gz COMPLETE    None None
   ./mastDownload/IUE/lwp13058/lwp13058mxlo_vo.fits COMPLETE    None None

The return value is an `~astropy.table.Table` manifest listing the local file paths, download status,
and any error messages for each requested product. This manifest can be used to verify successful downloads
or to programmatically access the downloaded files.

The ``curl_flag`` parameter may be used to generate a shell script containing ``curl`` commands that can be 
executed at a later time to download the files. This is useful for batch downloads, scheduling downloads, or
archiving download instructions. No files are downloaded when this flag is set; only the script is created.

.. doctest-remote-data::

   >>> manifest = Observations.download_products(data_products, 
   ...                                           productType="SCIENCE", 
   ...                                           curl_flag=True)   # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/portal/Download/stage/anonymous/public/514cfaa9-fdc1-4799-b043-4488b811db4f/mastDownload_20170629162916.sh to ./mastDownload_20170629162916.sh ... [Done]


Downloading a Single File
-------------------------

To download an individual data product, use the `~astroquery.mast.ObservationsClass.download_file` method and provide
a MAST data URI.

By default, the file is saved to the current working directory. A specific directory or
filename may be provided using the ``local_path`` argument.

The return value is a tuple containing the download status, an optional error message, and the
source URL.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> single_obs = Observations.query_criteria(obs_collection="IUE", obs_id="lwp13058")
   >>> data_products = Observations.get_product_list(single_obs)
   ...
   >>> product = data_products[0]["dataURI"]
   >>> print(product)
   mast:IUE/url/pub/iue/data/lwp/13000/lwp13058.elbll.gz
   >>> result = Observations.download_file(product)   # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:IUE/url/pub/iue/data/lwp/13000/lwp13058.elbll.gz to ./lwp13058.elbll.gz ... [Done]
   ...
   >>> print(result)
   ('COMPLETE', None, None)

The `~astroquery.mast.ObservationsClass.download_file` and `~astroquery.mast.ObservationsClass.download_products`
methods serve different purposes and are not interchangeable:

   - Use `~astroquery.mast.ObservationsClass.download_file` to download a **single file** by providing its MAST data URI.
   - Use `~astroquery.mast.ObservationsClass.download_products` to download **multiple files** by providing a table of data products or 
     a list of observation identifiers.

Using the incorrect method for a given input type will result in an error.


Cloud Data Access
==================

In addition to traditional file downloads from MAST, the `~astroquery.mast.ObservationsClass` interface
supports direct access to public MAST datasets hosted on Amazon Web Services (AWS). For many workflows,
cloud access can be significantly faster, more scalable, and more cost-effective than downloading files locally.

Cloud access integrates seamlessly with existing `~astroquery.mast.ObservationsClass` methods and allows users to
choose the most appropriate data access strategy for their needs without changing their code significantly.

Why Use Cloud Data Access?
---------------------------

Cloud-hosted MAST data are stored in public object storage (Amazon S3) alongside cloud computing resources.
Using cloud access allows users to:

  - **Avoid large downloads** by reading data directly from cloud storage.
  - **Reduce local storage needs** by processing data in the cloud without downloading files.
  - **Improve performance** by leveraging high-bandwidth connections between cloud compute and storage.
  - **Scale analyses** by utilizing cloud compute resources that can be adjusted to meet workload demands.
  - **Enable reproducible workflows** that operate in a consistent cloud environment.

Cloud access is particularly well-suited for:
  - Large surveys or multi-terabyte datasets.
  - Batch processing or pipeline workflows.
  - JupyterHub or notebook environments hosted in the cloud.
  - Situations where only a subset of files will be accessed.

Traditional downloads remain appropriate when:
  - Working with small datasets that fit comfortably on local storage.
  - Working offline or in environments without internet access.
  - Using software that requires local file access.

Enabling Cloud Data Access
--------------------------

Public datasets from several missions including Hubble, Kepler, TESS, GALEX, and Pan-STARRS are available
on AWS in `STScI's Open Data Bucket <https://registry.opendata.aws/collab/stsci/>`_.

Enable cloud access using the `~astroquery.mast.ObservationsClass.enable_cloud_dataset` method. Once enabled,
cloud storage becomes the **preferred source** for data access when available.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> Observations.enable_cloud_dataset(provider='AWS')
   INFO: Using the S3 STScI public dataset [astroquery.mast.cloud]

To revert to traditional, on-premise MAST data access, use the
`~astroquery.mast.ObservationsClass.disable_cloud_dataset` method.

.. doctest-remote-data::

   >>> Observations.disable_cloud_dataset()

Accessing Data via Cloud URIs
-----------------------------

Instead of downloading files, you can retrieve a list of cloud URIs (e.g., S3 URIs) that correspond to a set of 
data products using `~astroquery.mast.ObservationsClass.get_cloud_uris`. This method accepts either:

  - A table of data products (as returned by `~astroquery.mast.ObservationsClass.get_product_list`)
  - Observation query criteria (as keyword arguments) and optional product filters (through the ``mrp_only``, 
    ``extension``, and ``filter_products`` parameters)

Cloud URIs may be returned as:

  - Native cloud URIs (e.g., ``s3://stpubdata...``)
  - HTTP URLs suitable for streaming (set ``full_url=True`` and ``include_bucket=False``)
  - A mapping between MAST data URIs and cloud URIs (set ``return_uri_map=True``)

The following example demonstrates the extended workflow of querying observations, retrieving associated data products,
filtering for relevant products, and obtaining their S3 URIs.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> # The default provider is `AWS`, but we will write it in manually for this example:
   >>> Observations.enable_cloud_dataset(provider='AWS')
   INFO: Using the S3 STScI public dataset [astroquery.mast.cloud]
   >>> # Getting the cloud URIs
   >>> obs_table = Observations.query_criteria(obs_collection='HST',
   ...                                         filters='F606W',
   ...                                         instrument_name='ACS/WFC',
   ...                                         proposal_id=['12062'],
   ...                                         dataRights='PUBLIC')
   >>> products = Observations.get_product_list(obs_table)
   >>> filtered = Observations.filter_products(products,
   ...                                         productSubGroupDescription='DRZ')
   >>> s3_uris = Observations.get_cloud_uris(filtered)
   INFO: 2 of 4 products were duplicates. Only returning 2 unique product(s). [astroquery.mast.utils]
   >>> print(s3_uris)
   ['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']

This workflow can be streamlined by providing the query criteria directly to `~astroquery.mast.ObservationsClass.get_cloud_uris`.
This approach is recommended for code brevity and when you do not need to inspect intermediate results. Query criteria are supplied 
as keyword arguments, and filters are supplied through the ``filter_products`` parameter. If both ``data_products`` and query 
criteria are provided, ``data_products`` takes precedence.

Once the URIs are obtained, they can be used directly in cloud-based workflows or with cloud-enabled libraries such as
`Astropy <https://docs.astropy.org/en/stable/io/fits/usage/cloud.html>`__. To read a FITS file directly from S3 using Astropy,
use the `~astropy.io.fits.open` function with the S3 URI and appropriate ``fsspec`` keyword arguments.

.. doctest-remote-data::

   >>> from astropy.io import fits
   ...
   >>> s3_uri = 's3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits'
   >>> with fits.open(s3_uri, fsspec_kwargs={"anon": True}) as hdul:
   ...     hdul.info()
   Filename: <class 's3fs.core.S3File'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
   0  PRIMARY       1 PrimaryHDU     857   ()      
   1  SCI           1 ImageHDU        82   (4240, 4313)   float32   
   2  WHT           1 ImageHDU        44   (4240, 4313)   float32   
   3  CTX           1 ImageHDU        37   (4240, 4313)   int32   
   4  HDRTAB        1 BinTableHDU    595   10R x 293C   [9A, 3A, K, D, D, D, D, D, D, D, D, D, D, D, D, D, K, 3A, 9A, 7A, 18A, 4A, D, D, D, D, 3A, D, D, D, D, D, D, D, D, D, D, D, D, K, 8A, 23A, D, D, D, D, K, K, K, 8A, K, 23A, 9A, 20A, K, 4A, K, D, K, K, K, K, 23A, D, D, D, D, K, K, 3A, 3A, 4A, 4A, L, D, D, D, 3A, 1A, K, D, D, D, D, D, 4A, 4A, 12A, 12A, 23A, 8A, 23A, 10A, 10A, D, D, 3A, 3A, 23A, 4A, 8A, 7A, 23A, D, K, D, 6A, 9A, 8A, D, D, L, 9A, 18A, 3A, K, 5A, 7A, 3A, D, 13A, 8A, 4A, 3A, L, K, L, K, L, K, K, D, D, D, D, D, D, 3A, 1A, D, 23A, D, D, D, 3A, 23A, L, 1A, 3A, 6A, D, 3A, 6A, K, D, D, D, D, D, D, D, D, D, D, 23A, D, D, D, D, 3A, D, D, D, 1A, K, K, K, K, K, K, 23A, K, 5A, 7A, D, D, D, D, D, D, D, D, D, D, D, D, D, D, D, D, D, 12A, D, 24A, 23A, D, 1A, 1A, D, K, D, D, 1A, 1A, D, 4A, K, D, K, 7A, D, D, D, D, D, 23A, 23A, D, 8A, D, 29A, D, 3A, D, L, D, D, 4A, 6A, 5A, 2A, D, 3A, K, 1A, 1A, 1A, 1A, D, D, D, D, D, D, 4A, D, 4A, D, 4A, K, 4A, 3A, 1A, L, K, K, 37A, 1A, D, D, D, D, K, 3A, L, L, 6A, L, D, D, 3A, D, D, 3A, 8A, 1A, D, K, D, L, 30A, L, 5A]


Hybrid Workflows: Cloud-First Downloads
---------------------------------------

When cloud access is enabled, the standard download methods will **preferentially pull files from cloud storage** when available
and fall back to MAST servers as needed. 

To skip non-cloud products entirely, set the ``cloud_only`` parameter to `True`. This option is useful for workflows that must
remain fully cloud-based.

.. doctest-skip::

   >>> import os
   >>> from astroquery.mast import Observations
   ...
   >>> Observations.enable_cloud_dataset(provider='AWS')
   INFO: Using the S3 STScI public dataset [astroquery.mast.core]
   ...
   >>> # Downloading from the cloud
   >>> obs_table = Observations.query_criteria(obs_collection='HST',
   ...                                         filters='F606W',
   ...                                         instrument_name='ACS/WFC',
   ...                                         proposal_id=['12062'],
   ...                                         dataRights='PUBLIC')
   >>> products = Observations.get_product_list(obs_table[0])
   >>> manifest = Observations.download_products(products[:5], cloud_only=True)
   Downloading URL s3://stpubdata/hst/public/jbev/jbevetdqq/jbevetdqq_flt_hlet.fits to ./mastDownload/HST/jbevetdqq/jbevetdqq_flt_hlet.fits ... [Done]
   Downloading URL s3://stpubdata/hst/public/jbev/jbevetdqq/jbevetdqq_spt.fits to ./mastDownload/HST/jbevetdqq/jbevetdqq_spt.fits ... [Done]
   Downloading URL s3://stpubdata/hst/public/jbev/jbevetdqq/jbevetdqq_trl.fits to ./mastDownload/HST/jbevetdqq/jbevetdqq_trl.fits ... [Done]
   Downloading URL s3://stpubdata/hst/public/jbev/jbevetdqq/jbevetdqq_log.txt to ./mastDownload/HST/jbevetdqq/jbevetdqq_log.txt ... [Done]
   Downloading URL s3://stpubdata/hst/public/jbev/jbevetdqq/jbevetdqq_raw.jpg to ./mastDownload/HST/jbevetdqq/jbevetdqq_raw.jpg ... [Done]
   >>> print(manifest["Status"])
   Status
   --------
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
