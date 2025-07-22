
*******************
Observation Queries
*******************

Observation Positional Queries
==============================

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
   >>> obs_table = Observations.query_object("M8", radius=".02 deg")
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

Optional parameters must be labeled. For example the query above will produce
an error if the "radius" field is not specified.

.. doctest-remote-data::

   >>> obs_table = Observations.query_object("M8", ".02 deg")
   Traceback (most recent call last):
   ...
   TypeError: ObservationsClass.query_object_async() takes 2 positional arguments but 3 were given


Observation Criteria Queries
============================

To search for observations based on parameters other than position or target name,
use `~astroquery.mast.ObservationsClass.query_criteria`.
Criteria are supplied as keyword arguments, where valid criteria are "coordinates",
"objectname", "radius" (as in `~astroquery.mast.ObservationsClass.query_region` and
`~astroquery.mast.ObservationsClass.query_object`), and all observation fields listed
`here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

**Note:** The obstype keyword has been replaced by intentType, with valid values
"calibration" and "science." If the intentType keyword is not supplied, both science
and calibration observations will be returned.

Argument values are one or more acceptable values for the criterion,
except for fields with a float datatype where the argument should be in the form
[minVal, maxVal]. For non-float type criteria, wildcards (both * and %) may be used.
However, only one wildcarded value can be processed per criterion.

RA and Dec must be given in decimal degrees, and datetimes in MJD.

`~astroquery.mast.ObservationsClass.query_criteria` can be used to perform non-positional criteria queries.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(dataproduct_type="image",
   ...                                         proposal_pi="Osten*")
   >>> print(obs_table[:5])  # doctest: +IGNORE_OUTPUT
   intentType obs_collection provenance_name ... srcDen  obsid     objID  
   ---------- -------------- --------------- ... ------ -------- ---------
      science            HST          CALCOS ...    nan 24139596 144540274
      science            HST          CALCOS ...    nan 24139591 144540276
      science            HST          CALCOS ...    nan 24139580 144540277
      science            HST          CALCOS ...    nan 24139597 144540280
      science            HST          CALCOS ...    nan 24139575 144540281
   ...

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

We encourage the use of wildcards particularly when querying for JWST instruments
with the instrument_name criteria. This is because of the varying instrument names
for JWST science instruments, which you can read more about on the MAST page for
`JWST Instrument Names <https://outerspace.stsci.edu/display/MASTDOCS/JWST+Instrument+Names>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(proposal_pi="Espinoza, Nestor",
   ...                                         instrument_name="NIRISS*")
   >>> set(obs_table['instrument_name'])  # doctest: +IGNORE_OUTPUT
   {'NIRISS', 'NIRISS/IMAGE', 'NIRISS/SOSS'}


Getting Observation Counts
--------------------------

To get the number of observations and not the observations themselves, query_counts functions are available.
This can be useful if trying to decide whether the available memory is sufficient for the number of observations.

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


Metadata Queries
================

To list data missions archived by MAST and avaiable through `astroquery.mast`,
use the `~astroquery.mast.ObservationsClass.list_missions` function.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> print(Observations.list_missions())
   ['BEFS', 'EUVE', 'FIMS-SPEAR', 'FUSE', 'GALEX', 'HLA', 'HLSP', 'HST', 'HUT', 'IUE', 'JWST', 'K2', 'K2FFI', 'Kepler', 'KeplerFFI', 'OPO', 'PS1', 'SDSS', 'SPITZER_SHA', 'SWIFT', 'TESS', 'TUES', 'WUPPE']

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

The `~astroquery.mast.ObservationsClass.get_metadata` function only accepts the strings
"observations" or "products" as a parameter. Any other string or spelling will result
in an error.

.. doctest-remote-data::

   >>> meta_table = Observations.get_metadata("observation")
   Traceback (most recent call last):
   ...
   astroquery.exceptions.InvalidQueryError: Unknown query type.


Downloading Data
================

Getting Product Lists
---------------------

Each observation returned from a MAST query can have one or more associated data products.
Given one or more observations or MAST Product Group IDs ("obsid")
`~astroquery.mast.ObservationsClass.get_product_list` will return
a `~astropy.table.Table` containing the associated data products.
The product fields are documented `here <https://mast.stsci.edu/api/v0/_productsfields.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> obs_table = Observations.query_criteria(objectname="M8", obs_collection=["K2", "IUE"])
   >>> data_products_by_obs = Observations.get_product_list(obs_table[0:2])
   >>> print(data_products_by_obs)  # doctest: +IGNORE_OUTPUT
   obsID  obs_collection dataproduct_type ... dataRights calib_level filters
   ------ -------------- ---------------- ... ---------- ----------- -------
   664784             K2       timeseries ...     PUBLIC           2  KEPLER
   664785             K2       timeseries ...     PUBLIC           2  KEPLER
   >>> obsids = obs_table[0:2]['obsid']
   >>> data_products_by_id = Observations.get_product_list(obsids)
   >>> print(data_products_by_id)  # doctest: +IGNORE_OUTPUT
   obsID  obs_collection dataproduct_type ... dataRights calib_level filters
   ------ -------------- ---------------- ... ---------- ----------- -------
   664784             K2       timeseries ...     PUBLIC           2  KEPLER
   664785             K2       timeseries ...     PUBLIC           2  KEPLER
   >>> print((data_products_by_obs == data_products_by_id).all())
   True

Note that the input to `~astroquery.mast.ObservationsClass.get_product_list` should be "obsid" and NOT "obs_id",
which is a mission-specific identifier for a given observation, and cannot be used for querying the MAST database
with `~astroquery.mast.ObservationsClass.get_product_list`
(see `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__ for more details).
Using "obs_id" instead of "obsid" from the previous example will result in the following error:

.. doctest-remote-data::
   >>> obs_ids = obs_table[0:2]['obs_id']
   >>> data_products_by_id = Observations.get_product_list(obs_ids)  # doctest: +IGNORE_OUTPUT
   Traceback (most recent call last):
   ...
   RemoteServiceError: Error converting data type varchar to bigint.

To return only unique data products for an observation, use `~astroquery.mast.ObservationsClass.get_unique_product_list`.

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

Filtering
---------

Filter keyword arguments can be applied to download only data products that meet the given criteria.
Available filters are "mrp_only" (Minimum Recommended Products), "extension" (file extension),
and all products fields listed `here <https://mast.stsci.edu/api/v0/_productsfields.html>`_.

The ‘AND' operation is performed for a list of filters, and the ‘OR' operation is performed within a
filter set. The below example illustrates downloading all product files with the extension "fits" that
are either "RAW" or "UNCAL."

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
   30
   >>> products = Observations.filter_products(data_products,
   ...                                         productType=["SCIENCE", "PREVIEW"],
   ...                                         extension="fits")
   >>> print(len(products))
   10


Downloading Data Products
-------------------------

Products can be downloaded by using `~astroquery.mast.ObservationsClass.download_products`,
with a `~astropy.table.Table` of data products, or a list (or single) obsid as the argument.

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

​As an alternative to downloading the data files now, the ``curl_flag`` can be used instead to instead get a
curl script that can be used to download the files at a later time.

.. doctest-remote-data::

   >>> from astroquery.mast import Observations
   ...
   >>> single_obs = Observations.query_criteria(obs_collection="IUE", obs_id="lwp13058")
   >>> data_products = Observations.get_product_list(single_obs)
   ...
   >>> table = Observations.download_products(data_products, 
   ...                                        productType="SCIENCE", 
   ...                                        curl_flag=True)   # doctest: +IGNORE_OUTPUT
   Downloading URL https://mast.stsci.edu/portal/Download/stage/anonymous/public/514cfaa9-fdc1-4799-b043-4488b811db4f/mastDownload_20170629162916.sh to ./mastDownload_20170629162916.sh ... [Done]


Downloading a Single File
-------------------------

You can download a single data product file by using the `~astroquery.mast.ObservationsClass.download_file`
method and passing in a MAST Data URI.  The default is to download the file to the current working directory, but
you can specify the download directory or filepath with the ``local_path`` keyword argument.

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

The `~astroquery.mast.ObservationsClass.download_file` and `~astroquery.mast.ObservationsClass.download_products`
methods are not interchangeable. Using the incorrect method for either single files or product lists will result
in an error.

.. doctest-remote-data::

   >>> result = Observations.download_products(product)   # doctest: +IGNORE_OUTPUT
   Traceback (most recent call last):
   ...
   RemoteServiceError: Error converting data type varchar to bigint.

.. doctest-remote-data::

   >>> result = Observations.download_file(data_products)
   Traceback (most recent call last):
   ...
   TypeError: can only concatenate str (not "Table") to str


Cloud Data Access
------------------
Public datasets from the Hubble, Kepler and TESS telescopes are also available for free on Amazon Web Services
in `public S3 buckets <https://registry.opendata.aws/collab/stsci/>`__.

Using AWS resources to process public data no longer requires an AWS account for all AWS regions.
To enable cloud data access for the Hubble, Kepler, TESS, GALEX, and Pan-STARRS missions, follow the steps below:

You can enable cloud data access via the `~astroquery.mast.ObservationsClass.enable_cloud_dataset`
function, which sets AWS to become the preferred source for data access as opposed to on-premise
MAST until it is disabled with `~astroquery.mast.ObservationsClass.disable_cloud_dataset`.

To directly access a list of cloud URIs for a given dataset, use the
`~astroquery.mast.ObservationsClass.get_cloud_uris`
function (Python will prompt you to enable cloud access if you haven't already).
With this function, users may specify a `~astropy.table.Table` of data products or 
query criteria. Query criteria are supplied as keyword arguments, and product filters 
may be supplied through the ``mrp_only``, ``extension``, and ``filter_products`` parameters.

When cloud access is enabled, the standard download function
`~astroquery.mast.ObservationsClass.download_products` preferentially pulls files from AWS when they
are available. When set to `True`, the ``cloud_only`` parameter in
`~astroquery.mast.ObservationsClass.download_products` skips all data products not available in the cloud.


To get a list of S3 URIs, use the following workflow:

.. doctest-skip::

   >>> import os
   >>> from astroquery.mast import Observations
   ...
   >>> # Simply call the `enable_cloud_dataset` method from `Observations`. 
   >>> # The default provider is `AWS`, but we will write it in manually for this example:
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
   ['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']
   ...
   >>> Observations.disable_cloud_dataset()

Alternatively, this workflow can be streamlined by providing the query criteria directly to `~astroquery.mast.ObservationsClass.get_cloud_uris`.
This approach is recommended for code brevity. Query criteria are supplied as keyword arguments, and filters are supplied through the 
``filter_products`` parameter. If both ``data_products`` and query criteria are provided, ``data_products`` takes precedence.

.. doctest-remote-data::

   >>> import os
   >>> from astroquery.mast import Observations
   ...
   >>> Observations.enable_cloud_dataset(provider='AWS')
   INFO: Using the S3 STScI public dataset [astroquery.mast.cloud]
   >>> # Getting the cloud URIs
   >>> s3_uris = Observations.get_cloud_uris(obs_collection='HST',
   ...                                       filters='F606W',
   ...                                       instrument_name='ACS/WFC',
   ...                                       proposal_id=['12062'],
   ...                                       dataRights='PUBLIC',
   ...                                       filter_products={'productSubGroupDescription': 'DRZ'})
   INFO: 2 of 4 products were duplicates. Only returning 2 unique product(s). [astroquery.mast.utils]
   >>> print(s3_uris)
   ['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits', 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']
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