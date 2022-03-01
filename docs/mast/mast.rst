.. _astroquery.mast:

********************************
MAST Queries (`astroquery.mast`)
********************************

Getting Started
===============

This module can be used to query the Barbara A. Mikulski Archive for Space
Telescopes (MAST). Below are examples of the types of queries that can be used,
and how to access data products.

Positional Queries
------------------

Positional queries can be based on a sky position or a target name.
The observation fields are documented
`here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_region("322.49324 12.16683")
   >>> print(obs_table[:10])  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... srcDen    obsid    distance
   ---------- -------------- --------------- ... ------ ----------- --------
      science          SWIFT              -- ... 5885.0 15000731855      0.0
      science          SWIFT              -- ... 5885.0 15000731856      0.0
      science          SWIFT              -- ... 5885.0 15000790494      0.0
      science          SWIFT              -- ... 5885.0 15000731857      0.0
      science          SWIFT              -- ... 5885.0 15000791686      0.0
      science          SWIFT              -- ... 5885.0 15000791687      0.0
      science          SWIFT              -- ... 5885.0 15000729841      0.0
      science          SWIFT              -- ... 5885.0 15000754475      0.0
      science          SWIFT              -- ... 5885.0 15000779206      0.0
      science          SWIFT              -- ... 5885.0 15000779204      0.0

Radius is an optional parameter and the default is 0.2 degrees.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_object("M8",radius=".02 deg")
   >>> print(obs_table[:10])  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... srcDen    obsid    distance
   ---------- -------------- --------------- ... ------ ----------- --------
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0
      science    SPITZER_SHA    SSC Pipeline ...    nan 19000016510      0.0


Observation Criteria Queries
----------------------------

To search for observations based on parameters other than position or target name,
use `~astroquery.mast.ObservationsClass.query_criteria`.
Criteria are supplied as keyword arguments, where valid criteria are "coordinates",
"objectname", "radius" (as in `~astroquery.mast.ObservationsClass.query_region` and
`~astroquery.mast.ObservationsClass.query_object`), and all observation fields listed
`here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

**Note:** The obstype keyword has been replaced by intentType, with valid values
"calibration" and "science." If the intentType keyword is not supplied, both
science and calibration observations will be returned.

Argument values are one or more acceptable values for the criterion,
except for fields with a float datatype where the argument should be in the form
[minVal, maxVal]. For non-float type criteria, wildcards (both * and %) may be used.
However, only one wildcarded value can be processed per criterion.

RA and Dec must be given in decimal degrees, and datetimes in MJD.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(dataproduct_type=["image"],
   ...                                         proposal_pi="Osten*",
   ...                                         s_dec=[43.5,45.5])
   >>> print(obs_table)  # doctest: +IGNORE_OUTPUT
   dataproduct_type calib_level obs_collection ... intentType   obsid      objID
   ---------------- ----------- -------------- ... ---------- ---------- ----------
              image           1            HST ...    science 2003520267 2023816094
              image           1            HST ...    science 2003520266 2023816134
              image           1            HST ...    science 2003520268 2025756935
   ...
   >>> obs_table = Observations.query_criteria(filters=["*UV","Kepler"],objectname="M101")
   >>> print(obs_table)  # doctest: +IGNORE_OUTPUT
   dataproduct_type calib_level obs_collection ...   objID1        distance
   ---------------- ----------- -------------- ... ---------- ------------------
              image           2          GALEX ... 1000045952                0.0
              image           2          GALEX ... 1000001327 371.71837196246395
              image           2          GALEX ... 1000016641                0.0
              image           2          GALEX ... 1000016644 229.81061601101433
              image           2          GALEX ... 1000001326                0.0
              image           2          GALEX ... 1000004203                0.0
              image           2          GALEX ... 1000004937 3.8329068532314046
              image           2          GALEX ... 1000045953 371.71837196246395
              image           2          GALEX ... 1000048357                0.0
              image           2          GALEX ... 1000048943 3.8329068532314046
              image           2          GALEX ... 1000055044                0.0
              image           2          GALEX ... 1000055047 229.81061601101433


Getting Observation Counts
--------------------------

To get the number of observations and not the observations themselves, query_counts functions are available.
This can be useful if trying to decide whether the available memory is sufficient for the number of observations.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> print(Observations.query_region_count("322.49324 12.16683"))  # doctest: +IGNORE_OUTPUT
   2364
   ...
   >>> print(Observations.query_object_count("M8",radius=".02 deg"))  # doctest: +IGNORE_OUTPUT
   469
   ...
   >>> print(Observations.query_criteria_count(dataproduct_type="image",
   ...                                         filters=["NUV","FUV"],
   ...                                         t_max=[52264.4586,54452.8914]))  # doctest: +IGNORE_OUTPUT
   59033



Metadata Queries
----------------

To list data missions archived by MAST and avaiable through `astroquery.mast`, use the `~astroquery.mast.ObservationsClass.list_missions` function.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> print(Observations.list_missions())  # doctest: +IGNORE_OUTPUT
   ['BEFS', 'EUVE', 'FUSE', 'GALEX', 'HLA', 'HLSP', 'HST', 'HUT',
   'IUE', 'JWST', 'K2', 'K2FFI', 'Kepler', 'KeplerFFI', 'PS1',
   'SPITZER_SHA', 'SWIFT', 'TESS', 'TUES', 'WUPPE']

To get a table of metadata associated with observation or product lists use the
`~astroquery.mast.ObservationsClass.get_metadata` function.

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



Mission Searches
================

Mission-Specific Search Queries
-------------------------------

These queries allow for searches based on mission-specific metadata for a given
data collection.  Currently it provides access to a broad set of Hubble Space
Telescope (HST) metadata, including header keywords, proposal information, and
observational parameters.  The available metadata includes all information that
was previously available in the original HST web search form, and are present in
the current Mission Search interface.

Currenlty, the API only includes the search functionality. The functionality to
download data products associated with search results is not currently supported.

An object of MastMissions class is instantiated with a default mission of 'hst' and
default service set to 'search'.

.. code-block:: python

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions()
   >>> missions.mission
   'hst'
   >>> missions.service
   'search'

The missions object can be used to search metadata using region coordinates. the keywoed argumentss
can be used to specify output characteristics like selec_cols and sort_by and conditions that filter
on values like proposal id, pi last name etc. The available column names for a mission can be found out
by using the ~astroquery.mast.MastMissionsClass.get_column_list function.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions(mission='hst')
   >>> columns = missions.get_column_list()


For positional searches, the columns "ang_sep", "sci_data_set_name", "search_key" and "search_position"
will always be included, in addition to any columns specified using "select_cols". For non-positional
searches, "search_key" and "sci_data_set_name" will always be included, in addition to any columns
specified using "select_cols".

For a non positional search, select_cols would always include search_key and sci_data_set_name.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> from astropy.coordinates import SkyCoord
   >>> missions = MastMissions(mission='hst')
   >>> regionCoords = SkyCoord(210.80227, 54.34895, unit=('deg', 'deg'))
   >>> results = missions.query_region(regionCoords, 3, sci_pep_id=12556,
   ...                                 select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by=['sci_targname'])
   >>> results[:5]   # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    sci_status   sci_targname   sci_data_set_name       ang_sep        sci_pep_id     search_pos     sci_pi_last_name          search_key
       str6         str16              str9              str20           int64          str18              str6                  str27
    ---------- ---------------- ----------------- -------------------- ---------- ------------------ ---------------- ---------------------------
        PUBLIC NUCLEUS+HODGE602         OBQU010H0 0.017460048037303017      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU010H0
        PUBLIC NUCLEUS+HODGE602         OBQU01050 0.017460048037303017      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU01050
        PUBLIC NUCLEUS+HODGE602         OBQU01030 0.022143836477276503      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU01030
        PUBLIC NUCLEUS+HODGE602         OBQU010F0 0.022143836477276503      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU010F0
        PUBLIC NUCLEUS+HODGE602         OBQU010J0  0.04381046755938432      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU010J0


for paging through the results, offset and limit can be used to specify the starting record and the number
of returned records. the default values for offset and limit is 0 and 5000 respectively.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> from astropy.coordinates import SkyCoord
   >>> missions = MastMissions()
   >>> results = missions.query_criteria(sci_start_time=">=2021-01-01 00:00:00",
   ...                                   select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status", "sci_pep_id"],
   ...                                   sort_by=['sci_pep_id'], limit=1000, offset=1000)
   >>> len(results)
   1000

Metadata queries can also be performed using object names with the
~astroquery.mast.MastMissionsClass.query_object function.

.. doctest-remote-data::

   >>> results = missions.query_object('M101', 3, select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by=['sci_targname'])
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
        ang_sep           search_pos     sci_status          search_key               sci_stop_time        sci_targname       sci_start_time       sci_data_set_name
        str20              str18           str6               str27                      str26               str16               str26                   str9
   ------------------ ------------------ ---------- --------------------------- -------------------------- ------------ -------------------------- -----------------
   2.751140575012458  210.80227 54.34895     PUBLIC 210.80227 54.34895LDJI01010 2019-02-19T05:52:40.020000   +164.6+9.9 2019-02-19T00:49:58.010000         LDJI01010
   0.8000626246647815 210.80227 54.34895     PUBLIC 210.80227 54.34895J8OB02011 2003-08-27T08:27:34.513000   ANY        2003-08-27T07:44:47.417000         J8OB02011
   1.1261718338567348 210.80227 54.34895     PUBLIC 210.80227 54.34895J8D711J1Q 2003-01-17T00:50:22.250000   ANY        2003-01-17T00:42:06.993000         J8D711J1Q
   1.1454431087675097 210.80227 54.34895     PUBLIC 210.80227 54.34895JD6V01012 2017-06-15T18:33:25.983000   ANY        2017-06-15T18:10:12.037000         JD6V01012
   1.1457795862361977 210.80227 54.34895     PUBLIC 210.80227 54.34895JD6V01013 2017-06-15T20:08:44.063000   ANY        2017-06-15T19:45:30.023000         JD6V01013

Metadata queries can also be performed using non-positional parameters with the
~astroquery.mast.MastMissionsClass.query_criteria function.

.. doctest-remote-data::

   >>> results = missions.query_criteria(sci_data_set_name="Z06G0101T", sci_pep_id="1455",
   ...                                   select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                   sort_by=['sci_targname'])
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
   search_key       sci_stop_time        sci_data_set_name       sci_start_time       sci_targname sci_status
   str9              str26      str9    str26               str19        str6
   ---------- -------------------------- ----------------- -------------------------- ------------ ----------
   Z06G0101T  1990-05-13T11:02:34.567000         Z06G0101T 1990-05-13T10:38:09.193000           --     PUBLIC



Downloading Data
================

Getting Product Lists
---------------------

Each observation returned from a MAST query can have one or more associated data products.
Given one or more observations or observation ids ("obsid")
`~astroquery.mast.ObservationsClass.get_product_list` will return
a `~astropy.table.Table` containing the associated data products.
The product fields are documented `here <https://mast.stsci.edu/api/v0/_productsfields.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_object("M8",radius=".02 deg")
   >>> data_products_by_obs = Observations.get_product_list(obs_table[0:2])
   >>> print(data_products_by_obs)  # doctest: +IGNORE_OUTPUT
      obsID    obs_collection dataproduct_type ...   size  parent_obsid
   ----------- -------------- ---------------- ... ------- ------------
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
           ...            ...              ... ...     ...          ...
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ... 8648640  19000016510
   Length = 1153 rows
   ...
   >>> obsids = obs_table[0:2]['obsid']
   >>> data_products_by_id = Observations.get_product_list(obsids)
   >>> print(data_products_by_id)  # doctest: +IGNORE_OUTPUT
      obsID    obs_collection dataproduct_type ...   size  parent_obsid
   ----------- -------------- ---------------- ... ------- ------------
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
   19000016510    SPITZER_SHA            image ...  316800  19000016510
           ...            ...              ... ...     ...          ...
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ...   57600  19000016510
   19000016510    SPITZER_SHA            image ... 8648640  19000016510
   Length = 1153 rows
   ...
   >>> print((data_products_by_obs == data_products_by_id).all())
   True


Filtering
---------

Filter keyword arguments can be applied to download only data products that meet the given criteria.
Available filters are "mrp_only" (Minimum Recommended Products), "extension" (file extension),
and all products fields listed `here <https://mast.stsci.edu/api/v0/_productsfields.html>`_.

The ‘AND' operation is performed for a list of filters, and the ‘OR' operation is performed within a filter set.
The below example illustrates downloading all product files with the extension "fits" that are either "RAW" or "UNCAL."

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> Observations.download_products('25119363',
   ...                                productType=["SCIENCE", "PREVIEW"],
   ...                                extension="fits")   # doctest: +IGNORE_OUTPUT
   <Table length=3>
                      Local Path                    Status  Message  URL
                        str47                        str8    object object
   ----------------------------------------------- -------- ------- ------
   ./mastDownload/HST/fa2f0101m/fa2f0101m_a1f.fits COMPLETE    None   None
   ./mastDownload/HST/fa2f0101m/fa2f0101m_a2f.fits COMPLETE    None   None
   ./mastDownload/HST/fa2f0101m/fa2f0101m_a3f.fits COMPLETE    None   None

Product filtering can also be applied directly to a table of products without proceeding to the download step.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> data_products = Observations.get_product_list('25588063')
   >>> print(len(data_products))
   27
   >>> products = Observations.filter_products(data_products,
   ...                                         productType=["SCIENCE", "PREVIEW"],
   ...                                         extension="fits")
   >>> print(len(products))
   8


Downloading Data Products
-------------------------

Products can be downloaded by using `~astroquery.mast.ObservationsClass.download_products`,
with a `~astropy.table.Table` of data products, or a list (or single) obsid as the argument.

.. doctest-skip::

   >>> from astroquery.mast import Observations
   ...
   >>> single_obs = Observations.query_criteria(obs_collection="IUE",obs_id="lwp13058")
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

​As an alternative to downloading the data files now, the ``curl_flag`` can be used instead to instead get a curl
script that can be used to download the files at a later time.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> single_obs = Observations.query_criteria(obs_collection="IUE", obs_id="lwp13058")
   >>> data_products = Observations.get_product_list(single_obs)
   ...
   >>> table = Observations.download_products(data_products, productType="SCIENCE", curl_flag=True)   # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/portal/Download/stage/anonymous/public/514cfaa9-fdc1-4799-b043-4488b811db4f/mastDownload_20170629162916.sh to ./mastDownload_20170629162916.sh ... [Done]


Downloading a Single File
-------------------------

You can download a single data product file using the `~astroquery.mast.ObservationsClass.download_file` method, and passing in
a MAST Data URI.  The default is to download the file the current working directory, which can be changed with
the ``local_path`` keyword argument.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> single_obs = Observations.query_criteria(obs_collection="IUE",obs_id="lwp13058")
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


Cloud Data Access
------------------
Public datasets from the Hubble, Kepler and TESS telescopes are also available for free on Amazon Web Services
in `public S3 buckets <https://registry.opendata.aws/collab/stsci/>`__.

Using AWS resources to process public data no longer requires an AWS account for all AWS regions. To enable
cloud data access for the Hubble, Kepler, TESS, and GALEX missions, follow the steps below:

You can enable cloud data access via the `~astroquery.mast.ObservationsClass.enable_cloud_dataset` function,
which sets AWS to become the preferred source for data access as opposed to on-premise MAST until it
is disabled with `~astroquery.mast.ObservationsClass.disable_cloud_dataset`.

To directly access a list of cloud URIs for a given dataset, use the `~astroquery.mast.ObservationsClass.get_cloud_uris`
function (Python will prompt you to enable cloud access if you haven't already).

When cloud access is enabled, the standard download function
`~astroquery.mast.ObservationsClass.download_products` preferentially pulls files from AWS when they are available.
When set to `True`, the ``cloud_only`` parameter in `~astroquery.mast.ObservationsClass.download_products`
skips all data products not available in the cloud.


Getting a list of S3 URIs:

.. doctest-skip::

   >>> import os
   >>> from astroquery.mast import Observations
   ...
   >>> # Simply call the `enable_cloud_dataset` method from `Observations`. The default provider is `AWS`, but we will write it in manually for this example:
   >>> Observations.enable_cloud_dataset(provider='AWS')
   INFO: Using the S3 STScI public dataset [astroquery.mast.core]
   ...
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
   >>> print(s3_uris)
   ['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']
   ...
   >>> Observations.disable_cloud_dataset()


Downloading data products from S3:

.. doctest-skip::

   >>> import os
   >>> from astroquery.mast import Observations
   ...
   >>> # Simply call the `enable_cloud_dataset` method from `Observations`. The default provider is `AWS`, but we will write it in manually for this example:
   >>> Observations.enable_cloud_dataset(provider='AWS')
   INFO: Using the S3 STScI public dataset [astroquery.mast.core]
   ...
   >>> # Downloading from the cloud
   >>> obs_table = Observations.query_criteria(obs_collection=['Kepler'],
   ...                                         objectname="Kepler 12b", radius=0)
   >>> products = Observations.get_product_list(obs_table[0])
   >>> manifest = Observations.download_products(products[:10], cloud_only=True)
   manifestDownloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465-01-20160209194854_dvs.pdf to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-01-20160209194854_dvs.pdf ...
   |==========================================| 1.5M/1.5M (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465-20160128150956_dvt.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-20160128150956_dvt.fits ...
   |==========================================|  17M/ 17M (100.00%)         1s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465-20160209194854_dvr.pdf to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-20160209194854_dvr.pdf ...
   |==========================================| 5.8M/5.8M (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/dv_files/0118/011804465/kplr011804465_q1_q17_dr25_obs_tcert.pdf to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465_q1_q17_dr25_obs_tcert.pdf ...
   |==========================================| 2.2M/2.2M (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/previews/0118/011804465/kplr011804465-2013011073258_llc_bw_large.png to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2013011073258_llc_bw_large.png ...
   |==========================================|  24k/ 24k (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/target_pixel_files/0118/011804465/kplr011804465_tpf_lc_Q111111110111011101.tar to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465_tpf_lc_Q111111110111011101.tar ...
   |==========================================|  43M/ 43M (100.00%)         4s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465_lc_Q111111110111011101.tar to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465_lc_Q111111110111011101.tar ...
   |==========================================| 5.9M/5.9M (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465-2009131105131_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009131105131_llc.fits ...
   |==========================================|  77k/ 77k (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465-2009166043257_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009166043257_llc.fits ...
   |==========================================| 192k/192k (100.00%)         0s
   Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:KEPLER/url/missions/kepler/lightcurves/0118/011804465/kplr011804465-2009259160929_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009259160929_llc.fits ...
   |==========================================| 466k/466k (100.00%)         0s
   ...
   >>> print(manifest["Status"])
   Status
   --------
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   COMPLETE
   ...
   >>> Observations.disable_cloud_dataset()

Catalog Queries
===============

The Catalogs class provides access to a subset of the astronomical catalogs stored at MAST.
The catalogs currently available through this interface are:

- The Hubble Source Catalog (HSC)
- The GALEX Catalog (V2 and V3)
- The Gaia (DR1 and DR2) and TGAS Catalogs
- The TESS Input Catalog (TIC)
- The TESS Candidate Target List (CTL)
- The Disk Detective Catalog
- The PanSTARRS Catalog (DR1 and DR2)
- The All-Sky PLATO Input Catalog (DR1)

Positional Queries
------------------

Positional queries can be based on a sky position or a target name.
The returned fields vary by catalog, find the field documentation for specific catalogs
`here <https://mast.stsci.edu/api/v0/pages.html>`__.
If no catalog is specified, the Hubble Source Catalog will be queried.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_object("158.47924 -7.30962", catalog="Galex")
   >>> print(catalog_data[:10])
    distance_arcmin          objID        survey ... fuv_flux_aper_7 fuv_artifact
   ------------------ ------------------- ------ ... --------------- ------------
   0.3493802506329695 6382034098673685038    AIS ...     0.047751952            0
   0.7615422488595471 6382034098672634783    AIS ...              --            0
   0.9243329366166956 6382034098672634656    AIS ...              --            0
    1.162615739258038 6382034098672634662    AIS ...              --            0
   1.2670891287503308 6382034098672634735    AIS ...              --            0
    1.492173395497916 6382034098674731780    AIS ...    0.0611195639            0
   1.6051235757244107 6382034098672634645    AIS ...              --            0
    1.705418541388336 6382034098672634716    AIS ...              --            0
   1.7463721100195875 6382034098672634619    AIS ...              --            0
   1.7524423152919317 6382034098672634846    AIS ...              --            0


Some catalogs have a maximum number of results they will return.
If a query results in this maximum number of results a warning will be displayed to alert the user that they might be getting a subset of the true result set.

.. doctest-skip::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_region("322.49324 12.16683", catalog="HSC", magtype=2)
   WARNING: InputWarning: Coordinate string is being interpreted as an ICRS coordinate
   provided in degrees. [astroquery.utils.commons]
   WARNING: MaxResultsWarning: Maximum catalog results returned, may not include all
   sources within radius. [astroquery.mast.core]
   ...
   >>> print(catalog_data[:10])
    MatchID        Distance            MatchRA       ... W3_F160W_MAD W3_F160W_N
   --------- -------------------- ------------------ ... ------------ ----------
    50180585 0.003984902849540913  322.4931746094701 ...          nan          0
     8150896 0.006357935819940561 322.49334740450234 ...          nan          0
   100906349  0.00808206428937523  322.4932839715549 ...          nan          0
   105434103 0.011947078376104195 322.49324000530777 ...          nan          0
   103116183  0.01274757103013683  322.4934207202404 ...          nan          0
    45593349 0.013026569623011767  322.4933878707698 ...          nan          0
   103700905  0.01306760650244682  322.4932769229944 ...          nan          0
   102470085 0.014611879195009472 322.49311034430366 ...          nan          0
    93722307  0.01476438046135455 322.49348351134466 ...          nan          0
    24781941 0.015234351867433582 322.49300148743345 ...          nan          0

Radius is an optional parameter and the default is 0.2 degrees.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_object("M10", radius=.02, catalog="TIC")
   >>> print(catalog_data[:10])   # doctest: +IGNORE_OUTPUT
       ID            ra               dec        ... wdflag     dstArcSec
   ---------- ---------------- ----------------- ... ------ ------------------
    510188144 254.287449269816 -4.09954224264168 ...     -1 0.7650443624931581
    510188143  254.28717785824 -4.09908635292493 ...     -1 1.3400566638148848
    189844423 254.287799703996  -4.0994998249247 ...      0 1.3644407138867785
   1305764031 254.287147439535 -4.09866105132406 ...     -1  2.656905409847388
   1305763882 254.286696117371 -4.09925522448626 ...     -1 2.7561196688252894
    510188145 254.287431890823 -4.10017293344746 ...     -1  3.036238557555728
   1305763844 254.286675148545 -4.09971617257086 ...      0 3.1424781549696217
   1305764030 254.287249718516 -4.09841883152995 ...     -1  3.365991083435227
   1305764097 254.287599269103 -4.09837925361712 ...     -1    3.4590276863989
   1305764215  254.28820865799 -4.09859677020253 ...     -1 3.7675526728257034


The Hubble Source Catalog, the Gaia Catalog, and the PanSTARRS Catalog have multiple versions.
An optional version parameter allows you to select which version you want, the default is the highest version.

.. doctest-remote-data::

   >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", radius=0.1,
   ...                                       catalog="Gaia", version=2)
   >>> print("Number of results:",len(catalog_data))
   Number of results: 111
   >>> print(catalog_data[:4])
       solution_id             designation          ...      distance
   ------------------- ---------------------------- ... ------------------
   1635721458409799680 Gaia DR2 3774902350511581696 ... 0.6326770410972467
   1635721458409799680 Gaia DR2 3774901427093274112 ... 0.8440033390947586
   1635721458409799680 Gaia DR2 3774902148648277248 ... 0.9199206487344911
   1635721458409799680 Gaia DR2 3774902453590798208 ... 1.3578181104319944

The PanSTARRS Catalog has multiple data releases as well as multiple queryable tables.
An optional data release parameter allows you to select which data release is desired, with the default being the latest version (dr2).
The table to query is a required parameter.

.. doctest-remote-data::

   >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", radius=0.1,
   ...                                       catalog="Panstarrs", data_release="dr1", table="mean")
   >>> print("Number of results:",len(catalog_data))
   Number of results: 7007
   >>> print(catalog_data[:10])     # doctest: +IGNORE_OUTPUT
            ObjName           objAltName1 ... yFlags       distance
   -------------------------- ----------- ... ------ --------------------
   PSO J103359.653-071622.382        -999 ...  16416  0.04140441098310487
   PSO J103359.605-071622.873        -999 ...      0  0.04121935961328582
   PSO J103359.691-071640.232        -999 ...      0  0.03718729257758985
   PSO J103400.268-071639.192        -999 ...      0  0.03870112803784765
   PSO J103400.073-071637.358        -999 ...      0  0.03867536827891155
   PSO J103359.789-071632.606        -999 ...      0  0.03921557769883566
   PSO J103359.192-071654.790        -999 ...      0  0.03266232705300051
   PSO J103359.959-071655.155        -999 ...      0 0.034361022297827955
   PSO J103359.847-071655.610        -999 ...      0 0.033986082329893995
   PSO J103400.586-071656.646        -999 ...      0 0.035645179491121386

Catalog Criteria Queries
------------------------

The TESS Input Catalog (TIC), Disk Detective Catalog, and PanSTARRS Catalog can also be queried based on non-positional criteria.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="Tic",Bmag=[30,50],objType="STAR")
   >>> print(catalog_data)  # doctest: +IGNORE_OUTPUT
       ID    version  HIP TYC ...     e_Dec_orig     raddflag wdflag   objID
   --------- -------- --- --- ... ------------------ -------- ------ ----------
   125413929 20190415  --  -- ...  0.293682765259495        1      0  579825059
   261459129 20190415  --  -- ...  0.200397148604244        1      0 1701625107
    64575709 20190415  --  -- ...   0.21969663115091        1      0  595775997
    94322581 20190415  --  -- ...  0.205286802302475        1      0  606092549
   125414201 20190415  --  -- ...   0.22398993783274        1      0  579825329
   463721073 20190415  --  -- ...  0.489828592248652       -1      1  710312391
    81609218 20190415  --  -- ...  0.146788572369267        1      0  630541794
   282024596 20190415  --  -- ...  0.548806522539047        1      0  573765450
    23868624 20190415  --  -- ...            355.949       --      0  916384285
   282391528 20190415  --  -- ...   0.47766300834538        0      0  574723760
   123585000 20190415  --  -- ...  0.618316068787371        0      0  574511442
   260216294 20190415  --  -- ...  0.187170498094167        1      0  683390717
   406300991 20190415  --  -- ... 0.0518318978617112        0      0 1411465651


.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="Ctl",
   ...                                        objectname='M101', radius=1, Tmag=[10.75,11])
   >>> print(catalog_data)
       ID    version  HIP     TYC      ... raddflag wdflag   objID
   --------- -------- --- ------------ ... -------- ------ ---------
   441639577 20190415  -- 3852-00429-1 ...        1      0 150070672
   441658179 20190415  -- 3855-00816-1 ...        1      0 150246482
   441658008 20190415  -- 3852-00116-1 ...        1      0 150246361
   154258521 20190415  -- 3852-01403-1 ...        1      0 150281963
   441659970 20190415  -- 3852-00505-1 ...        1      0 150296707
   441660006 20190415  -- 3852-00341-1 ...        1      0 150296738
   233458861 20190415  -- 3852-01407-1 ...        1      0 150390757
   441662028 20190415  -- 3855-00941-1 ...        1      0 150395533


.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="DiskDetective",
   ...                                        objectname="M10",radius=2,state="complete")
   >>> print(catalog_data)      # doctest: +IGNORE_OUTPUT
       designation     ...                    ZooniverseURL
   ------------------- ... ----------------------------------------------------
   J165628.40-054630.8 ... https://talk.diskdetective.org/#/subjects/AWI0005cka
   J165748.96-054915.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ckd
   J165427.11-022700.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ck5
   J165749.79-040315.1 ... https://talk.diskdetective.org/#/subjects/AWI0005cke
   J165327.01-042546.2 ... https://talk.diskdetective.org/#/subjects/AWI0005ck3
   J165949.90-054300.7 ... https://talk.diskdetective.org/#/subjects/AWI0005ckk
   J170314.11-035210.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ckv


The PanSTARRS catalog also accepts additional parameters to allow for query refinement. These options include column selection,
sorting, column criteria, page size and page number. Additional information on PanSTARRS queries may be found
`here <https://catalogs.mast.stsci.edu/docs/panstarrs.html>`__.

Columns returned from the query may be submitted with the columns parameter as a list of column names.

The query may be sorted  with the sort_by parameter composed of either a single column name (to sort ascending),
or a list of multiple column names and/or tuples of direction and column name (ASC/DESC, column name).

To filter the query, criteria per column name are accepted. The 'AND' operation is performed between all
column name criteria, and the 'OR' operation is performed within column name criteria. Per each column name
parameter, criteria may consist of either a value or a list. The list may consist of a mix of values and
tuples of criteria decorator (min, gte, gt, max, lte, lt, like, contains) and value.

.. doctest-remote-data::

   >>> catalog_data = Catalogs.query_criteria(coordinates="5.97754 32.53617", radius=0.01,
   ...                                        catalog="PANSTARRS", table="mean", data_release="dr2",
   ...                                        nStackDetections=[("gte", 2)],
   ...                                        columns=["objName", "objID", "nStackDetections", "distance"],
   ...                                        sort_by=[("desc", "distance")], pagesize=15)
   >>> print(catalog_data[:10])   # doctest: +IGNORE_OUTPUT
          objName              objID        nStackDetections        distance
   --------------------- ------------------ ---------------- ---------------------
   PSO J005.9812+32.5270 147030059812483022                5  0.009651200148871086
   PSO J005.9726+32.5278 147030059727583992                2    0.0093857181370567
   PSO J005.9787+32.5453 147050059787164914                4  0.009179045509852305
   PSO J005.9722+32.5418 147050059721440704                4  0.007171813230776031
   PSO J005.9857+32.5377 147040059855825725                4  0.007058815429178634
   PSO J005.9810+32.5424 147050059809651427                2  0.006835678269917365
   PSO J005.9697+32.5368 147040059697224794                2  0.006654002479439699
   PSO J005.9712+32.5330 147040059711340087                4  0.006212461367287632
   PSO J005.9747+32.5413 147050059747400181                5 0.0056515210592035965
   PSO J005.9775+32.5314 147030059774678271                3  0.004739286624336443


Hubble Source Catalog (HSC) specific queries
--------------------------------------------

Given an HSC Match ID, return all catalog results.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_object("M10", radius=.02, catalog="HSC")
   >>> matchid = catalog_data[0]["MatchID"]
   >>> print(matchid)
   63980492
   >>> matches = Catalogs.query_hsc_matchid(matchid)
   >>> print(matches)
     CatID   MatchID  ...                       cd_matrix
   --------- -------- ... ------------------------------------------------------
   257195287 63980492 ... -1.38889e-005 -5.26157e-010 -5.26157e-010 1.38889e-005
   257440119 63980492 ... -1.38889e-005 -5.26157e-010 -5.26157e-010 1.38889e-005
   428373428 63980492 ...   -1.10056e-005 5.65193e-010 5.65193e-010 1.10056e-005
   428373427 63980492 ...   -1.10056e-005 5.65193e-010 5.65193e-010 1.10056e-005
   428373429 63980492 ...   -1.10056e-005 5.65193e-010 5.65193e-010 1.10056e-005
   410574499 63980492 ...   -1.10056e-005 1.56577e-009 1.56577e-009 1.10056e-005
   410574498 63980492 ...   -1.10056e-005 1.56577e-009 1.56577e-009 1.10056e-005
   410574497 63980492 ...   -1.10056e-005 1.56577e-009 1.56577e-009 1.10056e-005

HSC spectra accessed through this class as well. `~astroquery.mast.CatalogsClass.get_hsc_spectra`
does not take any arguments, and simply loads all HSC spectra.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> all_spectra = Catalogs.get_hsc_spectra()
   >>> print(all_spectra[:10])
   ObjID                 DatasetName                  MatchID  ... PropID HSCMatch
   ----- -------------------------------------------- -------- ... ------ --------
   20010 HAG_J072655.67+691648.9_J8HPAXAEQ_V01.SPEC1D 19657846 ...   9482        Y
   20011 HAG_J072655.69+691648.9_J8HPAOZMQ_V01.SPEC1D 19657846 ...   9482        Y
   20012 HAG_J072655.76+691729.7_J8HPAOZMQ_V01.SPEC1D 19659745 ...   9482        Y
   20013 HAG_J072655.82+691620.0_J8HPAOZMQ_V01.SPEC1D 19659417 ...   9482        Y
   20014 HAG_J072656.34+691704.7_J8HPAXAEQ_V01.SPEC1D 19660230 ...   9482        Y
   20015 HAG_J072656.36+691704.7_J8HPAOZMQ_V01.SPEC1D 19660230 ...   9482        Y
   20016 HAG_J072656.36+691744.9_J8HPAOZMQ_V01.SPEC1D 19658847 ...   9482        Y
   20017 HAG_J072656.37+691630.2_J8HPAXAEQ_V01.SPEC1D 19660827 ...   9482        Y
   20018 HAG_J072656.39+691630.2_J8HPAOZMQ_V01.SPEC1D 19660827 ...   9482        Y
   20019 HAG_J072656.41+691734.9_J8HPAOZMQ_V01.SPEC1D 19656620 ...   9482        Y


Individual or ranges of spectra can be downloaded using the `~astroquery.mast.CatalogsClass.download_hsc_spectra` function.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> all_spectra = Catalogs.get_hsc_spectra()
   >>> manifest = Catalogs.download_hsc_spectra(all_spectra[100:104])   # doctest: +IGNORE_OUTPUT
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   ...
   >>> print(manifest)     # doctest: +IGNORE_OUTPUT
                                Local Path                              ... URL
   -------------------------------------------------------------------- ... ----
   ./mastDownload/HSC/HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits ... None
   ./mastDownload/HSC/HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits ... None
   ./mastDownload/HSC/HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits ... None
   ./mastDownload/HSC/HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits ... None


TESSCut
=======

TESSCut is MAST's tool to provide full-frame image (FFI) cutouts from the Transiting
Exoplanet Survey Satellite (TESS). The cutouts are returned in the form of target pixel
files that follow the same format as TESS pipeline target pixel files. This tool can
be accessed in Astroquery by using the Tesscut class.

**Note:** TESScut limits each user to no more than 10 simultaneous calls to the service.
After the user has reached this limit TESScut will return a
``503 Service Temporarily Unavailable Error``.

If you use TESSCut for your work, please cite Brasseur et al. 2019
https://ui.adsabs.harvard.edu/abs/2019ascl.soft05007B/abstract


Cutouts
-------

The `~astroquery.mast.TesscutClass.get_cutouts` function takes a coordinate, object name
(i.e. "M104" or "TIC 32449963"), or moving target (i.e. "Eleonora") and cutout size
(in pixels or an angular quantity) and returns the cutout target pixel file(s) as a
list of `~astropy.io.fits.HDUList` objects.

If the given coordinate/object location appears in more than one TESS sector a target pixel
file will be produced for each sector.  If the cutout area overlaps more than one camera or
ccd a target pixel file will be produced for each one.

Requesting a cutout by coordinate or objectname accesses the
`MAST TESScut API <https://mast.stsci.edu/tesscut/docs/getting_started.html#requesting-a-cutout>`__
and returns a target pixel file, with format described `here <https://astrocut.readthedocs.io/en/latest/astrocut/file_formats.html#target-pixel-files>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> hdulist = Tesscut.get_cutouts(coordinates=cutout_coord, size=5)
   >>> hdulist[0].info()  # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
     0  PRIMARY       1 PrimaryHDU      56   ()
     1  PIXELS        1 BinTableHDU    280   1060R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
     2  APERTURE      1 ImageHDU        81   (5, 5)   int32


.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> hdulist = Tesscut.get_cutouts(objectname="TIC 32449963", size=5)
   >>> hdulist[0].info()  # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
     0  PRIMARY       1 PrimaryHDU      56   ()
     1  PIXELS        1 BinTableHDU    280   3477R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
     2  APERTURE      1 ImageHDU        81   (5, 5)   int32


Requesting a cutout by moving_target accesses the
`MAST Moving Target TESScut API <https://mast.stsci.edu/tesscut/docs/getting_started.html#moving-target-cutouts>`__
and returns a target pixel file, with format described
`here <https://astrocut.readthedocs.io/en/latest/astrocut/file_formats.html#path-focused-target-pixel-files>`__.
The moving_target is an optional bool argument where `True` signifies that the accompanying ``objectname`` input is
the object name or ID understood by the `JPL Horizon ephemerades interface <https://ssd.jpl.nasa.gov/horizons.cgi>`__.
The default value for ``moving_target`` is set to `False`. Therefore, a non-moving target can be input simply with either the objectname or coordinates.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> hdulist = Tesscut.get_cutouts(objectname="Eleonora", moving_target=True, size=5, sector=6)
   >>> hdulist[0].info()
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
     0  PRIMARY       1 PrimaryHDU      54   ()
     1  PIXELS        1 BinTableHDU    150   355R x 16C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A, D, D, D, D]
     2  APERTURE      1 ImageHDU        97   (2136, 2078)   int32


The `~astroquery.mast.TesscutClass.download_cutouts` function takes a coordinate, cutout size
(in pixels or an angular quantity), or object name
(i.e. "M104" or "TIC 32449963") and moving target (True or False). It uses these parameters to download the cutout target pixel file(s).

If a given coordinate/object/moving target appears in more than one TESS sector, a target pixel file will be produced for each sector.
If the cutout area overlaps more than one camera or ccd, a target pixel file will be produced for each one.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   >>> import astropy.units as u
   ...
   >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
   >>> manifest = Tesscut.download_cutouts(coordinates=cutout_coord, size=[5, 7]*u.arcmin, sector=9) # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra=107.18696&dec=-70.50919&y=0.08333333333333333&x=0.11666666666666667&units=d&sector=9 to ./tesscut_20210716150026.zip ... [Done]
   Inflating...
   ...
   >>> print(manifest)  # doctest: +IGNORE_OUTPUT
                        Local Path
   ----------------------------------------------------------
   ./tess-s0009-4-1_107.186960_-70.509190_21x15_astrocut.fits


Sector information
------------------

To access sector information for a particular coordinate, object, or moving target there is
`~astroquery.mast.TesscutClass.get_sectors`.

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> coord = SkyCoord(324.24368, -27.01029,unit="deg")
   >>> sector_table = Tesscut.get_sectors(coordinates=coord)
   >>> print(sector_table)   # doctest: +IGNORE_OUTPUT
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0028-1-4     28      1   4

.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> sector_table = Tesscut.get_sectors(objectname="TIC 32449963")
   >>> print(sector_table)     # doctest: +IGNORE_OUTPUT
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0010-1-4     10      1   4


.. doctest-remote-data::

   >>> from astroquery.mast import Tesscut
   ...
   >>> sector_table = Tesscut.get_sectors(objectname="Ceres", moving_target=True)
   >>> print(sector_table)
     sectorName   sector camera ccd
   -------------- ------ ------ ---
   tess-s0029-1-4     29      1   4
   tess-s0043-3-3     43      3   3
   tess-s0044-2-4     44      2   4


Zcut
====


Zcut for MAST allows users to request cutouts from various Hubble deep field surveys. The cutouts can
be returned as either fits or image files (jpg and png are supported). This tool can be accessed in
Astroquery by using the Zcut class. The list of supported deep field surveys can be found here:
https://mast.stsci.edu/zcut/


Cutouts
-------

The `~astroquery.mast.ZcutClass.get_cutouts` function takes a coordinate and cutout size (in pixels or
an angular quantity) and returns the cutout FITS file(s) as a list of ~astropy.io.fits.HDUList objects.

If the given coordinate appears in more than one Zcut survey, a FITS file will be produced for each survey.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> hdulist = Zcut.get_cutouts(coordinates=cutout_coord, size=5)
   >>> hdulist[0].info()    # doctest: +IGNORE_OUTPUT
   Filename: <class '_io.BytesIO'>
   No.    Name      Ver    Type      Cards   Dimensions   Format
   0  PRIMARY       1 PrimaryHDU      11   ()
   1  CUTOUT        1 ImageHDU       177   (5, 5)   float32
   2  CUTOUT        1 ImageHDU       177   (5, 5)   float32
   3  CUTOUT        1 ImageHDU       177   (5, 5)   float32


The `~astroquery.mast.ZcutClass.download_cutouts` function takes a coordinate and cutout size (in pixels or
an angular quantity) and downloads the cutout fits file(s) as either fits files or image (png/jpg)
files.

If a given coordinate appears in more than one Zcut survey, a cutout will be produced for each survey.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> manifest = Zcut.download_cutouts(coordinates=cutout_coord, size=[200, 300], units="px")    # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/zcut/api/v0.1/astrocut?ra=189.49206&dec=62.20615&y=200&x=300&units=px&format=fits to ./zcut_20210125155545.zip ... [Done]
   Inflating...
   ...
   >>> print(manifest)    # doctest: +IGNORE_OUTPUT
                                 Local Path
   -------------------------------------------------------------------------
   ./candels_gn_30mas_189.492060_62.206150_300.0pix-x-200.0pix_astrocut.fits


.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> cutout_coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> manifest = Zcut.download_cutouts(coordinates=cutout_coord, size=[200, 300], units="px", form="jpg")    # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/zcut/api/v0.1/astrocut?ra=189.49206&dec=62.20615&y=200&x=300&units=px&format=jpg to ./zcut_20201202132453.zip ... [Done]
   ...
   >>> print(manifest)        # doctest: +IGNORE_OUTPUT
                                                   Local Path
   ---------------------------------------------------------------------------------------------------------
    ./hlsp_candels_hst_acs_gn-tot-30mas_f606w_v1.0_drz_189.492060_62.206150_300.0pix-x-200.0pix_astrocut.jpg
    ./hlsp_candels_hst_acs_gn-tot-30mas_f814w_v1.0_drz_189.492060_62.206150_300.0pix-x-200.0pix_astrocut.jpg
   ./hlsp_candels_hst_acs_gn-tot-30mas_f850lp_v1.0_drz_189.492060_62.206150_300.0pix-x-200.0pix_astrocut.jpg


Survey information
------------------

To list the available deep field surveys at a particular location there is `~astroquery.mast.ZcutClass.get_surveys`.

.. doctest-remote-data::

   >>> from astroquery.mast import Zcut
   >>> from astropy.coordinates import SkyCoord
   ...
   >>> coord = SkyCoord(189.49206, 62.20615, unit="deg")
   >>> survey_list = Zcut.get_surveys(coordinates=coord)
   >>> print(survey_list)    # doctest: +IGNORE_OUTPUT
   ['candels_gn_60mas', 'candels_gn_30mas', 'goods_north']


Accessing Proprietary Data
==========================

To access data that is not publicly available users may log into their
`MyST Account <https://archive.stsci.edu/registration/index.html>`_.
This can be done by using the `~astroquery.mast.MastClass.login` function,
or by initializing a class instance with credentials.

If a token is not supplied, the user will be prompted to enter one.

To view tokens accessible through your account, visit https://auth.mast.stsci.edu

.. doctest-skip::

   >>> from astroquery.mast import Observations
   ...
   >>> Observations.login(token="12348r9w0sa2392ff94as841")
   INFO: MAST API token accepted, welcome User Name [astroquery.mast.core]
   ...
   >>> sessioninfo = Observations.session_info()
   eppn: user_name@stsci.edu
   ezid: uname
   ...

.. doctest-skip::

   >>> from astroquery.mast import Observations
   ...
   >>> my_session = Observations(token="12348r9w0sa2392ff94as841")
   INFO: MAST API token accepted, welcome User Name [astroquery.mast.core]
   ...
   >>> sessioninfo = Observations.session_info()
   eppn: user_name@stsci.edu
   ezid: uname
                ...

\* For security tokens should not be typed into a terminal or Jupyter notebook
but instead input using a more secure method such as `~getpass.getpass`.


MAST tokens expire after 10 days of inactivity, at which point the user must generate a new token.  If
the key is used within that time, the token's expiration pushed back to 10 days.  A token's max
age is 60 days, afterward the user must generate a token.
The ``store_token`` argument can be used to store the token securely in the user's keyring.
This token can be overwritten using the ``reenter_token`` argument.
To logout before a session expires, the `~astroquery.mast.MastClass.logout` method may be used.



Direct Mast Queries
===================

The Mast class provides more direct access to the MAST interface.  It requires
more knowledge of the inner workings of the MAST API, and should be rarely
needed.  However in the case of new functionality not yet implemented in
astroquery, this class does allow access.  See the `MAST api documentation
<https://mast.stsci.edu/api>`_ for more information.

The basic MAST query function returns query results as an `~astropy.table.Table`.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> service = 'Mast.Caom.Cone'
   >>> params = {'ra':184.3,
   ...           'dec':54.5,
   ...           'radius':0.2}
   >>> observations = Mast.service_request(service, params)
   >>> print(observations)    # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ...    obsid         distance
   ---------- -------------- --------------- ... ----------- ------------------
      science           TESS            SPOC ... 17001016097                0.0
      science           TESS            SPOC ... 17000855562                0.0
      science           TESS            SPOC ... 17000815577 203.70471189751947
      science           TESS            SPOC ... 17000981417  325.4085155315165
      science           TESS            SPOC ... 17000821493  325.4085155315165
      science            PS1             3PI ... 16000864847                0.0
      science            PS1             3PI ... 16000864848                0.0
      science            PS1             3PI ... 16000864849                0.0
      science            PS1             3PI ... 16000864850                0.0
      science            PS1             3PI ... 16000864851                0.0
          ...            ...             ... ...         ...                ...
      science           HLSP             QLP ... 18013987996   637.806560287869
      science           HLSP             QLP ... 18007518640   637.806560287869
      science           HLSP       TESS-SPOC ... 18013510950   637.806560287869
      science           HLSP       TESS-SPOC ... 18007364076   637.806560287869
      science          GALEX             MIS ...  1000007123                0.0
      science          GALEX             AIS ...  1000016562                0.0
      science          GALEX             AIS ...  1000016562                0.0
      science          GALEX             AIS ...  1000016563                0.0
      science          GALEX             AIS ...  1000016563                0.0
      science          GALEX             AIS ...  1000016556  302.4058357983673
      science          GALEX             AIS ...  1000016556  302.4058357983673
   Length = 77 rows


If the output is not the MAST json result type it cannot be properly parsed into a `~astropy.table.Table`.
In this case, the async method should be used to get the raw http response, which can then be manually parsed.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> service = 'Mast.Name.Lookup'
   >>> params ={'input':"M8",
   ...          'format':'json'}
   ...
   >>> response = Mast.service_request_async(service,params)
   >>> result = response[0].json()
   >>> print(result)     # doctest: +IGNORE_OUTPUT
   {'resolvedCoordinate': [{'cacheDate': 'Apr 12, 2017 9:28:24 PM',
                            'cached': True,
                            'canonicalName': 'MESSIER 008',
                            'decl': -24.38017,
                            'objectType': 'Neb',
                            'ra': 270.92194,
                            'resolver': 'NED',
                            'resolverTime': 113,
                            'searchRadius': -1.0,
                            'searchString': 'm8'}],
    'status': ''}



Additional Resources
====================

`Accessing MAST Holdings with Astroquery, <https://stsci.app.box.com/s/4no7430kswla4gsg8bt2avs72k9agpne>`_ slides from an introductory MAST Astroquery talk.

The Space Telescope Science Institute `Notebooks Repository <https://github.com/spacetelescope/notebooks>`_ includes many examples that use Astroquery.


Reference/API
=============

.. automodapi:: astroquery.mast
    :no-inheritance-diagram:
    :inherited-members:
