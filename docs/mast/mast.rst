.. doctest-skip-all

.. _astroquery.mast:

********************************
MAST Queries (`astroquery.mast`)
********************************

.. raw:: html

         <div class="service-status mast-survey" id="survey-banner" style="background-color: #C75109; border-color: #C75109; color: white; padding-top: 1rem; padding-bottom: 1rem; line-height: 30px; font-size: x-large; display: flex; margin-left: 0rem; margin-right: 0rem; margin-bottom: 1rem; margin-top: 1rem;"><span class="status-message" style="margin-left: 2rem; margin-right: 2rem;">The MAST team wants your feedback on the <a href="https://www.surveymonkey.com/r/mastportal" target="_blank" style="color: white; text-decoration: underline;">MAST Portal</a> and <a href="https://www.surveymonkey.com/r/mastcatalogs" target="_blank" style="color: white; text-decoration: underline;">MAST catalogs</a>. If you use either of these, please take five to ten minutes to fill out the linked survey(s). Thank you!</span></div>


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

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> obs_table = Observations.query_region("322.49324 12.16683")
                >>> print(obs_table[:10])

                dataproduct_type obs_collection instrument_name ... distance
                ---------------- -------------- --------------- ... --------
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0
                            cube          SWIFT            UVOT ...      0.0

Radius is an optional parameter and the default is 0.2 degrees.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> obs_table = Observations.query_object("M8",radius=".02 deg")
                >>> print(obs_table[:10])

                dataproduct_type obs_collection instrument_name ...    distance
                ---------------- -------------- --------------- ... -------------
                            cube             K2          Kepler ... 39.4914065162
                        spectrum            IUE             LWP ...           0.0
                        spectrum            IUE             LWP ...           0.0
                        spectrum            IUE             LWP ...           0.0
                        spectrum            IUE             LWR ...           0.0
                        spectrum            IUE             LWR ...           0.0
                        spectrum            IUE             LWR ...           0.0
                        spectrum            IUE             LWR ...           0.0
                        spectrum            IUE             LWR ...           0.0
                        spectrum            IUE             LWR ...           0.0



Observation Criteria Queries
----------------------------

To search for observations based on parameters other than position or target name,
use `~astroquery.mast.ObservationsClass.query_criteria`.
Criteria are supplied as keyword arguments, where valid criteria are "coordinates",
"objectname", "radius" (as in `~astroquery.mast.ObservationsClass.query_region` and
`~astroquery.mast.ObservationsClass.query_object`), and all observation fields listed
`here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
**Note:** The obstype keyword has been replaced by intentType, with valid values "calibration" and "science." If the intentType keyword is not supplied, both science and calibration observations will be returned.

Argument values are one or more acceptable values for the criterion,
except for fields with a float datatype where the argument should be in the form
[minVal, maxVal]. For non-float type criteria, wildcards (both * and %) may be used.
However, only one wildcarded value can be processed per criterion.

RA and Dec must be given in decimal degrees, and datetimes in MJD.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> obs_table = Observations.query_criteria(dataproduct_type=["image"],
                ...                                         proposal_pi="Osten*",
                ...                                         s_dec=[43.5,45.5])
                >>> print(obs_table)

                dataproduct_type calib_level obs_collection ... dataURL   obsid      objID
                ---------------- ----------- -------------- ... ------- ---------- ----------
                           image           1            HST ...    None 2003520266 2011133418
                           image           1            HST ...    None 2003520267 2011133419
                           image           1            HST ...    None 2003520268 2011133420

                >>> obs_table = Observations.query_criteria(filters=["*UV","Kepler"],objectname="M101")
                >>> print(obs_table)

                dataproduct_type calib_level obs_collection ...   objID1      distance
                ---------------- ----------- -------------- ... ---------- -------------
                           image           2          GALEX ... 1000055044           0.0
                           image           2          GALEX ... 1000004937 3.83290685323
                           image           2          GALEX ... 1000045953 371.718371962
                           image           2          GALEX ... 1000055047 229.810616011
                           image           2          GALEX ... 1000016644 229.810616011
                           image           2          GALEX ... 1000045952           0.0
                           image           2          GALEX ... 1000048357           0.0
                           image           2          GALEX ... 1000001326           0.0
                           image           2          GALEX ... 1000001327 371.718371962
                           image           2          GALEX ... 1000004203           0.0
                           image           2          GALEX ... 1000016641           0.0
                           image           2          GALEX ... 1000048943 3.83290685323


Getting Observation Counts
--------------------------

To get the number of observations and not the observations themselves, query_counts functions are available.
This can be useful if trying to decide whether the available memory is sufficient for the number of observations.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> print(Observations.query_region_count("322.49324 12.16683"))
                1804

                >>> print(Observations.query_object_count("M8",radius=".02 deg"))
                196

                >>> print(Observations.query_criteria_count(dataproduct_type="image",
                ...                                         filters=["NUV","FUV"],
                ...                                         t_max=[52264.4586,54452.8914]))
                59033



Metadata Queries
----------------

To list data missions archived by MAST and avaiable through `astroquery.mast`, use the `~astroquery.mast.ObservationsClass.list_missions` function.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> print(Observations.list_missions())
                ['IUE', 'Kepler', 'K2FFI', 'EUVE', 'HLA', 'KeplerFFI','FUSE',
                'K2', 'HST', 'WUPPE', 'BEFS', 'GALEX', 'TUES','HUT', 'SWIFT']


To get a table of metadata associated with observation or product lists use the
`~astroquery.mast.ObservationsClass.get_metadata` function.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> meta_table = Observations.get_metadata("observations")
                >>> print(meta_table[:5])
                   Column Name    Column Label ...       Examples/Valid Values
                ----------------- ------------ ... ---------------------------------
                   obs_collection      Mission ...         E.g. SWIFT, PS1, HST, IUE
                  instrument_name   Instrument ...    E.g. WFPC2/WFC, UVOT, STIS/CCD
                          project      Project ...   E.g. HST, HLA, EUVE, hlsp_legus
                          filters      Filters ... F469N, NUV, FUV, LOW DISP, MIRROR
                wavelength_region     Waveband ...                EUV, XRAY, OPTICAL

                >>> meta_table = Observations.get_metadata("products")
                >>> print(meta_table[:3])

                 Column Name     Column Label   ...         Examples/Valid Values
                -------------- ---------------- ... -------------------------------------
                        obs_id   Observation ID ...                  U24Z0101T, N4QF18030
                         obsID Product Group ID ...         Long integer, e.g. 2007590987
                obs_collection          Mission ... HST, HLA, SWIFT, GALEX, Kepler, K2...



Downloading Data
================

Getting Product Lists
---------------------

Each observation returned from a MAST query can have one or more associated data products.
Given one or more observations or observation ids ("obsid")
`~astroquery.mast.ObservationsClass.get_product_list` will return
a `~astropy.table.Table` containing the associated data products.
The product fields are documented `here <https://mast.stsci.edu/api/v0/_productsfields.html>`__.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> obs_table = Observations.query_object("M8",radius=".02 deg")
                >>> data_products_by_obs = Observations.get_product_list(obs_table[0:2])
                >>> print(data_products_by_obs)

                  obsID    obs_collection ...          productFilename             size
                ---------- -------------- ... ---------------------------------- --------
                3000007760            IUE ...                  lwp13058.elbll.gz   185727
                3000007760            IUE ...                  lwp13058.elbls.gz   183350
                3000007760            IUE ...                   lwp13058.lilo.gz   612715
                3000007760            IUE ...                  lwp13058.melol.gz    12416
                3000007760            IUE ...                  lwp13058.melos.gz    12064
                3000007760            IUE ...                    lwp13058.raw.gz   410846
                3000007760            IUE ...                   lwp13058.rilo.gz   416435
                3000007760            IUE ...                   lwp13058.silo.gz   100682
                3000007760            IUE ...                       lwp13058.gif     8971
                3000007760            IUE ...                   lwp13058.mxlo.gz    18206
                3000007760            IUE ...               lwp13058mxlo_vo.fits    48960
                3000007760            IUE ...                       lwp13058.gif     3967
                9500243833             K2 ...    k2-tpf-only-target_bw_large.png     9009
                9500243833             K2 ... ktwo200071160-c91_lpd-targ.fits.gz 39930404
                9500243833             K2 ... ktwo200071160-c92_lpd-targ.fits.gz 62213068
                9500243833             K2 ...    k2-tpf-only-target_bw_thumb.png     1301

                >>> obsids = obs_table[0:2]['obsid']
                >>> data_products_by_id = Observations.get_product_list(obsids)
                >>> print(data_products_by_id)

                  obsID    obs_collection ...          productFilename             size
                ---------- -------------- ... ---------------------------------- --------
                3000007760            IUE ...                  lwp13058.elbll.gz   185727
                3000007760            IUE ...                  lwp13058.elbls.gz   183350
                3000007760            IUE ...                   lwp13058.lilo.gz   612715
                3000007760            IUE ...                  lwp13058.melol.gz    12416
                3000007760            IUE ...                  lwp13058.melos.gz    12064
                3000007760            IUE ...                    lwp13058.raw.gz   410846
                3000007760            IUE ...                   lwp13058.rilo.gz   416435
                3000007760            IUE ...                   lwp13058.silo.gz   100682
                3000007760            IUE ...                       lwp13058.gif     8971
                3000007760            IUE ...                   lwp13058.mxlo.gz    18206
                3000007760            IUE ...               lwp13058mxlo_vo.fits    48960
                3000007760            IUE ...                       lwp13058.gif     3967
                9500243833             K2 ...    k2-tpf-only-target_bw_large.png     9009
                9500243833             K2 ... ktwo200071160-c91_lpd-targ.fits.gz 39930404
                9500243833             K2 ... ktwo200071160-c92_lpd-targ.fits.gz 62213068
                9500243833             K2 ...    k2-tpf-only-target_bw_thumb.png     1301

                >>> print((data_products_by_obs == data_products_by_id).all())
                True





Downloading Data Products
-------------------------

Products can be downloaded by using `~astroquery.mast.ObservationsClass.download_products`,
with a `~astropy.table.Table` of data products, or a list (or single) obsid as the argument.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> obsid = '3000007760'
                >>> data_products = Observations.get_product_list(obsid)
                >>> manifest = Observations.download_products(data_products)
                Downloading URL http://archive.stsci.edu/pub/iue/data/lwp/13000/lwp13058.mxlo.gz to ./mastDownload/IUE/lwp13058/lwp13058.mxlo.gz ... [Done]
                Downloading URL http://archive.stsci.edu/pub/vospectra/iue2/lwp13058mxlo_vo.fits to ./mastDownload/IUE/lwp13058/lwp13058mxlo_vo.fits ... [Done]
                >>> print(manifest)

                                   Local Path                     Status  Message URL
                ------------------------------------------------ -------- ------- ----
                    ./mastDownload/IUE/lwp13058/lwp13058.mxlo.gz COMPLETE    None None
                ./mastDownload/IUE/lwp13058/lwp13058mxlo_vo.fits COMPLETE    None None

​As an alternative to downloading the data files now, the curl_flag can be used instead to instead get a curl script that can be used to download the files at a later time.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> Observations.download_products('2003839997',
                ...                                productType="SCIENCE",
                ...                                curl_flag=True)

                Downloading URL https://mast.stsci.edu/portal/Download/stage/anonymous/public/514cfaa9-fdc1-4799-b043-4488b811db4f/mastDownload_20170629162916.sh to ./mastDownload_20170629162916.sh ... [Done]


Filtering
---------

Filter keyword arguments can be applied to download only data products that meet the given criteria.
Available filters are "mrp_only" (Minimum Recommended Products), "extension" (file extension),
and all products fields listed `here <https://mast.stsci.edu/api/v0/_productsfields.html>`_.

The ‘AND' operation is performed for a list of filters, and the ‘OR' operation is performed within a filter set.
The below example illustrates downloading all product files with the extension "fits" that are either "RAW" or "UNCAL."

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> Observations.download_products('2003839997',
                ...                                productSubGroupDescription=["RAW", "UNCAL"],
                ...                                extension="fits")
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11p7q_raw.fits to ./mastDownload/HST/IB3P11P7Q/ib3p11p7q_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11p8q_raw.fits to ./mastDownload/HST/IB3P11P8Q/ib3p11p8q_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11phq_raw.fits to ./mastDownload/HST/IB3P11PHQ/ib3p11phq_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11q9q_raw.fits to ./mastDownload/HST/IB3P11Q9Q/ib3p11q9q_raw.fits ... [Done]


Product filtering can also be applied directly to a table of products without proceeding to the download step.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> products = Observations.get_product_list('2003839997')
                >>> print(len(products))
                31

                >>> products = Observations.filter_products(data_products,
                ...                                         productSubGroupDescription=["RAW", "UNCAL"],
                ...                                         extension="fits")
                >>> print(len(products))
                4

Downloading a Single File
-------------------------

You can download a single data product file using the `~astroquery.mast.ObservationsClass.download_file` method, and passing in
a MAST dataURL.  The default is to download the file the current working directory, which can be changed with
the *local_path* keyword argument.

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> product = 'mast:IUE/url/pub/iue/data/lwp/13000/lwp13058.elbll.gz'
                >>> result = Observations.download_file(product)
                Downloading URL https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:IUE/url/pub/iue/data/lwp/13000/lwp13058.elbll.gz to ./lwp13058.elbll.gz ... [Done]
                >>> print(result)
                ('COMPLETE', None, None)

Cloud Data Access
------------------
Public datasets from the Hubble, Kepler and TESS telescopes are also available on Amazon Web Services
in `public S3 buckets <https://registry.opendata.aws/collab/stsci/>`__.

Using AWS resources to process public data requires an `AWS account <https://aws.amazon.com/>`__ and associated
`credentials file <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html>`__. The `boto3
<https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`__ library is also required as it handles
connections to the AWS servers. Instructions for creating AWS credentials are available `here
<https://stackoverflow.com/questions/21440709/how-do-i-get-aws-access-key-id-for-amazon>`__. Data transfer charges
are the responsibility of the requester  (see `request pricing <https://aws.amazon.com/s3/pricing/>`__), however
transfers are free within the US-East AWS region.

Cload data access is enabled using the `~astroquery.mast.ObservationsClass.enable_cloud_dataset` function, which
will cause AWS to become the prefered source for data access until it is disabled
(`~astroquery.mast.ObservationsClass.disable_cloud_dataset`).

To directly access a list of cloud URIs for a given dataset, use the `~astroquery.mast.ObservationsClass.get_cloud_uris`
function, however when cloud access is enabled, the standatd download function
`~astroquery.mast.ObservationsClass.download_products` will preferentially pull files from AWS when they are avilable.
There is also a ``cloud_only`` flag, which when set to True will cause all data products not available in the
cloud to be skipped.


Getting a list of S3 URIs:

.. code-block:: python

                >>> import os
                >>> from astroquery.mast import Observations

                >>> # If credential environment are not already set, we can set them within python.
                >>> os.environ['AWS_ACCESS_KEY_ID'] = 'myaccesskeyid'
                >>> os.environ['AWS_SECRET_ACCESS_KEY'] = 'mysecretaccesskey'

                >>> # If your profile is not called [default], update the next line:
                >>> Observations.enable_cloud_dataset(provider='AWS', profile='default')
                INFO: Using the S3 STScI public dataset [astroquery.mast.core]
                INFO: See Request Pricing in https://aws.amazon.com/s3/pricing/ for details [astroquery.mast.core]
                INFO: If you have not configured boto3, follow the instructions here: https://boto3.readthedocs.io/en/latest/guide/configuration.html [astroquery.mast.core]

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
                ['s3://stpubdata/hst/public/jbev/jbeveo010/jbeveo010_drz.fits',
                 's3://stpubdata/hst/public/jbev/jbevet010/jbevet010_drz.fits']

                >>> Observations.disable_cloud_dataset()


Downloading data products from S3:

.. code-block:: python

                >>> import os
                >>> from astroquery.mast import Observations

                >>> # If credential environment are not already set, we can set them within python.
                >>> os.environ['AWS_ACCESS_KEY_ID'] = 'myaccesskeyid'
                >>> os.environ['AWS_SECRET_ACCESS_KEY'] = 'mysecretaccesskey'

                >>> # If your profile is not called [default], update the next line:
                >>> Observations.enable_cloud_dataset(provider='AWS', profile='default')
                INFO: Using the S3 STScI public dataset [astroquery.mast.core]
                INFO: See Request Pricing in https://aws.amazon.com/s3/pricing/ for details [astroquery.mast.core]
                INFO: If you have not configured boto3, follow the instructions here: https://boto3.readthedocs.io/en/latest/guide/configuration.html [astroquery.mast.core]

                >>> # Downloading from the cloud
                >>> obs_table = Observations.query_criteria(obs_collection=['Kepler'],
                ...                                         objectname="Kepler 12b", radius=0)
                >>> products = Observations.get_product_list(obs_table[0])
                >>> manifest = Observations.download_products(products[:10], cloud_only=True)
                ERROR: Error pulling from S3 bucket: Parameter validation failed: Invalid type for parameter Key, value: None, type: <class 'NoneType'>, valid types: <class 'str'> [astroquery.mast.core]
                WARNING: Skipping file... [astroquery.mast.core]
                ERROR: Error pulling from S3 bucket: Parameter validation failed: Invalid type for parameter Key, value: None, type: <class 'NoneType'>, valid types: <class 'str'> [astroquery.mast.core]
                WARNING: Skipping file... [astroquery.mast.core]
                ERROR: Error pulling from S3 bucket: Parameter validation failed: Invalid type for parameter Key, value: None, type: <class 'NoneType'>, valid types: <class 'str'> [astroquery.mast.core]
                WARNING: Skipping file... [astroquery.mast.core]
                ERROR: Error pulling from S3 bucket: Parameter validation failed: Invalid type for parameter Key, value: None, type: <class 'NoneType'>, valid types: <class 'str'> [astroquery.mast.core]
                WARNING: Skipping file... [astroquery.mast.core]
                ERROR: Error pulling from S3 bucket: Parameter validation failed: Invalid type for parameter Key, value: None, type: <class 'NoneType'>, valid types: <class 'str'> [astroquery.mast.core]
                WARNING: Skipping file... [astroquery.mast.core]
                Downloading URL s3://stpubdata/kepler/public/lightcurves/0118/011804465/kplr011804465-2009131105131_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009131105131_llc.fits ... [Done]
                Downloading URL s3://stpubdata/kepler/public/lightcurves/0118/011804465/kplr011804465-2009166043257_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009166043257_llc.fits ... [Done]
                Downloading URL s3://stpubdata/kepler/public/lightcurves/0118/011804465/kplr011804465-2009259160929_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009259160929_llc.fits ... [Done]
                Downloading URL s3://stpubdata/kepler/public/lightcurves/0118/011804465/kplr011804465-2009350155506_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2009350155506_llc.fits ... [Done]
                Downloading URL s3://stpubdata/kepler/public/lightcurves/0118/011804465/kplr011804465-2010009091648_llc.fits to ./mastDownload/Kepler/kplr011804465_lc_Q111111110111011101/kplr011804465-2010009091648_llc.fits ... [Done]

                >>> print(manifest["Status"])
                 Status
                --------
                 SKIPPED
                 SKIPPED
                 SKIPPED
                 SKIPPED
                 SKIPPED
                COMPLETE
                COMPLETE
                COMPLETE
                COMPLETE
                COMPLETE

                >>> Observations.disable_cloud_dataset()

Catalog Queries
===============

The Catalogs class provides access to a subset of the astronomical catalogs stored at MAST.  The catalogs currently available through this interface are:

- The Hubble Source Catalog (HSC)
- The GALEX Catalog (V2 and V3)
- The Gaia (DR1 and DR2) and TGAS Catalogs
- The TESS Input Catalog (TIC)
- The TESS Candidate Target List (CTL)
- The Disk Detective Catalog
- PanSTARRS (DR1, DR2)

Positional Queries
------------------

Positional queries can be based on a sky position or a target name.
The returned fields vary by catalog, find the field documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.html>`__. If no catalog is specified, the Hubble Source Catalog will be queried.

.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_object("158.47924 -7.30962", catalog="Galex")
                >>> print(catalog_data[:10])

                distance_arcmin        objID        survey ... fuv_flux_aper_7 fuv_artifact
                --------------- ------------------- ------ ... --------------- ------------
                 0.349380250633 6382034098673685038    AIS ...     0.047751952            0
                  0.76154224886 6382034098672634783    AIS ...              --            0
                 0.924332936617 6382034098672634656    AIS ...              --            0
                  1.16261573926 6382034098672634662    AIS ...              --            0
                  1.26708912875 6382034098672634735    AIS ...              --            0
                   1.4921733955 6382034098674731780    AIS ...    0.0611195639            0
                  1.60512357572 6382034098672634645    AIS ...              --            0
                  1.70541854139 6382034098672634716    AIS ...              --            0
                  1.74637211002 6382034098672634619    AIS ...              --            0
                  1.75244231529 6382034098672634846    AIS ...              --            0


Some catalogs have a maximum number of results they will return.
If a query results in this maximum number of results a warning will be displayed to alert the user that they might be getting a subset of the true result set.

.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_region("322.49324 12.16683", catalog="HSC", magtype=2)

                WARNING: MaxResultsWarning: Maximum catalog results returned, may not include all
                sources within radius. [astroquery.mast.core]

                >>> print(catalog_data[:10])

                MatchID      Distance        MatchRA    ... W3_F160W W3_F160W_Sigma W3_F160W_N
                -------- ---------------- ------------- ... -------- -------------- ----------
                82371983 0.00445549943203 322.493181974 ...       --             --          0
                82603024   0.006890683763 322.493352058 ...       --             --          0
                82374767 0.00838818765315  322.49337203 ...       --             --          0
                82368728  0.0088064912074 322.493272691 ...       --             --          0
                82371509  0.0104348577531 322.493354352 ...       --             --          0
                82372543  0.0106808683543 322.493397455 ...       --             --          0
                82371076  0.0126535758873 322.493089416 ...       --             --          0
                82367288  0.0130150558411 322.493247548 ...       --             --          0
                82371086  0.0135993945732 322.493248703 ...       --             --          0
                82368622  0.0140289292301 322.493101406 ...       --             --          0


Radius is an optional parameter and the default is 0.2 degrees.

.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_object("M10", radius=.02, catalog="TIC")
                >>> print(catalog_data[:10])

                    ID          ra           dec       ... duplicate_id priority   dstArcSec
                --------- ------------- -------------- ... ------------ -------- -------------
                189844423    254.287989      -4.099644 ...           --       -- 2.21043178558
                189844434 254.286301884 -4.09872352783 ...           --       -- 4.69684511346
                189844449    254.288157      -4.097959 ...           --       -- 5.53390173242
                189844403    254.286864      -4.101237 ...           --       -- 7.19103845641
                189844459 254.286798163  -4.0973143956 ...           --       -- 7.63543964382
                189844400    254.285379      -4.100856 ...           --       -- 9.27452417927
                189844461 254.285647884 -4.09722647575 ...           --       -- 9.98427869106
                189844385 254.289725042 -4.10156744653 ...           --       -- 11.4468393777
                189844419    254.290767      -4.099757 ...           --       -- 11.9738216615
                189844454 254.290349435 -4.09754191392 ...           --       -- 12.2100186781


The Hubble Source Catalog, the Gaia Catalog, and the PanSTARRS Catalog have multiple versions.
An optional version parameter allows you to select which version you want, the default is the highest version.

.. code-block:: python

                >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", radius=0.1,
                ...                                       catalog="Gaia", version=2)
                >>> print("Number of results:",len(catalog_data))
                >>> print(catalog_data[:4])

                Number of results: 111
                    solution_id             designation          ...      distance
                ------------------- ---------------------------- ... ------------------
                1635721458409799680 Gaia DR2 3774902350511581696 ... 0.6327882551927051
                1635721458409799680 Gaia DR2 3774901427093274112 ... 0.8438875783827048
                1635721458409799680 Gaia DR2 3774902148648277248 ... 0.9198397322382648
                1635721458409799680 Gaia DR2 3774902453590798208 ... 1.3578882400285217

The PanSTARRS Catalog has multiple data releases as well as multiple queryable tables.
An optional data release parameter allows you to select which data release is desired, with the default being the latest version (dr2).
The table to query is a required parameter.

.. code-block:: python

                >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", radius=0.1,
                >>>                                       catalog="Panstarrs", data_release="dr1", table="mean")
                >>> print("Number of results:",len(catalog_data))
                >>> print(catalog_data[:10])

                Number of results: 7007
                       objName        objAltName1 objAltName2 ... yMeanApMagNpt yFlags distance
                --------------------- ----------- ----------- ... ------------- ------ --------
                PSO J158.4130-07.2557        -999        -999 ...             0      0        0
                PSO J158.4133-07.2564        -999        -999 ...             0      0        0
                PSO J158.4136-07.2571        -999        -999 ...             0 114720        0
                PSO J158.4156-07.2530        -999        -999 ...             0      0        0
                PSO J158.4157-07.2511        -999        -999 ...             0      0        0
                PSO J158.4159-07.2535        -999        -999 ...             0      0        0
                PSO J158.4159-07.2554        -999        -999 ...             0 114720        0
                PSO J158.4160-07.2534        -999        -999 ...             0 114720        0
                PSO J158.4164-07.2568        -999        -999 ...             0      0        0
                PSO J158.4175-07.2574        -999        -999 ...             0  16416        0

Catalog Criteria Queries
------------------------

The TESS Input Catalog (TIC), Disk Detective Catalog, and PanSTARRS Catalog can also be queried based on non-positional criteria.

.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_criteria(catalog="Tic",Bmag=[30,50],objType="STAR")
                >>> print(catalog_data)

                    ID    version  HIP TYC ... disposition duplicate_id priority   objID
                --------- -------- --- --- ... ----------- ------------ -------- ---------
                 81609218 20171221  --  -- ...          --           --       -- 217917514
                 23868624 20171221  --  -- ...          --           --       -- 296973171
                406300991 20171221  --  -- ...          --           --       -- 400575018


.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_criteria(catalog="Ctl",
                ...                                        objectname='M101', radius=1, Tmag=[10.75,11])
                >>> print(catalog_data)
                    ID    version  HIP     TYC      ... wdflag     ctlPriority        objID
                --------- -------- --- ------------ ... ------ -------------------- ---------
                441639577 20190415  -- 3852-00429-1 ...      0  0.00138923974233085 150848150
                441662028 20190415  -- 3855-00941-1 ...      0  0.00100773800289492 151174508
                233458861 20190415  -- 3852-01407-1 ...      0 0.000843468567169446 151169732
                441658008 20190415  -- 3852-00116-1 ...      0 0.000337697695047815 151025336
                154258521 20190415  -- 3852-01403-1 ...      0 0.000791883530388075 151060938
                441658179 20190415  -- 3855-00816-1 ...      0 0.000933466312394693 151025457
                441659970 20190415  -- 3852-00505-1 ...      0 0.000894696498704202 151075682
                441660006 20190415  -- 3852-00341-1 ...      0 0.000600037898043061 151075713


.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_criteria(catalog="DiskDetective",
                ...                                        objectname="M10",radius=2,state="complete")
                >>> print(catalog_data)

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

.. code-block:: python

                >>> catalog_data = Catalogs.query_criteria(coordinates="5.97754 32.53617", radius=0.01,
                ...                                        catalog="PANSTARRS", table="mean", data_release="dr2",
                ...                                        nStackDetections=[("gte", 2)],
                ...                                        columns=["objName", "objID", "nStackDetections", "distance"],
                ...                                        sort_by=[("desc", "distance")], pagesize=15)
                >>> print(catalog_data[:10])

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

.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> catalog_data = Catalogs.query_object("M10", radius=.02, catalog="HSC")
                >>> matchid = catalog_data[0]["MatchID"]
                >>> print(matchid)

                17554326

                >>> matches = Catalogs.query_hsc_matchid(matchid)
                >>> print(matches)

                  CatID   MatchID  ...                       cd_matrix
                --------- -------- ... ------------------------------------------------------
                303940283 17554326 ...   -1.10059e-005 6.90694e-010 6.90694e-010 1.10059e-005
                303936256 17554326 ...   -1.10059e-005 6.90694e-010 6.90694e-010 1.10059e-005
                303938261 17554326 ...   -1.10059e-005 6.90694e-010 6.90694e-010 1.10059e-005
                301986299 17554326 ...   -1.10049e-005 -1.6278e-010 -1.6278e-010 1.10049e-005
                301988274 17554326 ...   -1.10049e-005 -1.6278e-010 -1.6278e-010 1.10049e-005
                301990418 17554326 ...   -1.10049e-005 -1.6278e-010 -1.6278e-010 1.10049e-005
                206511399 17554326 ... -1.38889e-005 -1.36001e-009 -1.36001e-009 1.38889e-005
                206507082 17554326 ... -1.38889e-005 -1.36001e-009 -1.36001e-009 1.38889e-005


HSC spectra accessed through this class as well. `~astroquery.mast.CatalogsClass.get_hsc_spectra` does not take any arguments, and simply loads all HSC spectra.

.. code-block:: python

                >>> from astroquery.mast import Catalogs

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

.. code-block:: python

                >>> from astroquery.mast import Catalogs

                >>> all_spectra = Catalogs.get_hsc_spectra()
                >>> manifest = Catalogs.download_hsc_spectra(all_spectra[100:104])

                Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
                Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
                Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
                Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]

                >>> print(manifest)

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


Cutouts
-------

The `~astroquery.mast.TesscutClass.get_cutouts` function takes a coordinate or object name
(such as "M104" or "TIC 32449963") and cutout size (in pixels or an angular quantity) and
returns the cutout target pixel file(s) as a list of `~astropy.io.fits.HDUList` objects.

If the given coordinate/object location appears in more than one TESS sector a target pixel
file will be produced for each sector.  If the cutout area overlaps more than one camera or
ccd a target pixel file will be produced for each one.

.. code-block:: python

                >>> from astroquery.mast import Tesscut
                >>> from astropy.coordinates import SkyCoord

                >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
                >>> hdulist = Tesscut.get_cutouts(coordinates=cutout_coord, size=5)
                >>> hdulist[0].info()
                Filename: <class '_io.BytesIO'>
                No.    Name      Ver    Type      Cards   Dimensions   Format
                  0  PRIMARY       1 PrimaryHDU      55   ()
                  1  PIXELS        1 BinTableHDU    279   1282R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
                  2  APERTURE      1 ImageHDU        79   (5, 5)   int32


.. code-block:: python

                >>> from astroquery.mast import Tesscut

                >>> hdulist = Tesscut.get_cutouts(objectname="TIC 32449963", size=5)
                >>> hdulist[0].info()
                Filename: <class '_io.BytesIO'>
                No.    Name      Ver    Type      Cards   Dimensions   Format
                  0  PRIMARY       1 PrimaryHDU      56   ()
                  1  PIXELS        1 BinTableHDU    280   1211R x 12C   [D, E, J, 25J, 25E, 25E, 25E, 25E, J, E, E, 38A]
                  2  APERTURE      1 ImageHDU        80   (5, 5)   int32


The `~astroquery.mast.TesscutClass.download_cutouts` function takes a coordinate or object name
(such as "M104" or "TIC 32449963") and cutout size (in pixels or an angular quantity) and
downloads the cutout target pixel file(s).

If a given coordinate appears in more than one TESS sector a target pixel file will be
produced for each sector.  If the cutout area overlaps more than one camera or ccd
a target pixel file will be produced for each one.

.. code-block:: python

                >>> from astroquery.mast import Tesscut
                >>> from astropy.coordinates import SkyCoord
                >>> import astropy.units as u

                >>> cutout_coord = SkyCoord(107.18696, -70.50919, unit="deg")
                >>> manifest = Tesscut.download_cutouts(coordinates=cutout_coord, size=[5, 7]*u.arcmin)
                Downloading URL https://mast.stsci.edu/tesscut/api/v0.1/astrocut?ra=107.18696&dec=-70.50919&y=0.08333333333333333&x=0.11666666666666667&units=d&sector=1 to ./tesscut_20181102104719.zip ... [Done]
                Inflating...

                >>> print(manifest)
                                      local_file
                ------------------------------------------------------
                ./tess-s0001-4-3_107.18696_-70.50919_14x21_astrocut.fits

Sector information
------------------

To access sector information at a particular location there is  `~astroquery.mast.TesscutClass.get_sectors`.

.. code-block:: python

                >>> from astroquery.mast import Tesscut
                >>> from astropy.coordinates import SkyCoord

                >>> coord = SkyCoord(324.24368, -27.01029,unit="deg")
                >>> sector_table = Tesscut.get_sectors(coordinates=coord)
                >>> print(sector_table)
                  sectorName   sector camera ccd
                -------------- ------ ------ ---
                tess-s0001-1-3      1      1   3


.. code-block:: python

                >>> from astroquery.mast import Tesscut

                >>> sector_table = Tesscut.get_sectors(objectname="TIC 32449963")
                >>> print(sector_table)
                  sectorName   sector camera ccd
                -------------- ------ ------ ---
                tess-s0010-1-4     10      1   4


Accessing Proprietary Data
==========================

To access data that is not publicly available users may log into their
`MyST Account <https://archive.stsci.edu/registration/index.html>`_.
This can be done by using the `~astroquery.mast.MastClass.login` function,
or by initializing a class instance with credentials.

If a token is not supplied, the user will be prompted to enter one.

To view tokens accessible through your account, visit https://auth.mast.stsci.edu

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> Observations.login(token="12348r9w0sa2392ff94as841")

                INFO: MAST API token accepted, welcome User Name [astroquery.mast.core]

                >>> sessioninfo = Observations.session_info()

                eppn: user_name@stsci.edu
                ezid: uname
                ...

.. code-block:: python

                >>> from astroquery.mast import Observations

                >>> my_session = Observations(token="12348r9w0sa2392ff94as841")

                INFO: MAST API token accepted, welcome User Name [astroquery.mast.core]

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

.. code-block:: python

                >>> from astroquery.mast import Mast

                >>> service = 'Mast.Caom.Cone'
                >>> params = {'ra':184.3,
                ...           'dec':54.5,
                ...           'radius':0.2}

                >>> observations = Mast.service_request(service, params)
                >>> print(observations)

                dataproduct_type obs_collection instrument_name ...    distance   _selected_
                ---------------- -------------- --------------- ... ------------- ----------
                           image          GALEX           GALEX ...           0.0      False
                           image          GALEX           GALEX ...           0.0      False
                           image          GALEX           GALEX ...           0.0      False
                           image          GALEX           GALEX ...           0.0      False
                           image          GALEX           GALEX ...           0.0      False
                           image          GALEX           GALEX ... 302.405835798      False
                           image          GALEX           GALEX ... 302.405835798      False


If the output is not the MAST json result type it cannot be properly parsed into a `~astropy.table.Table`.
In this case, the async method should be used to get the raw http response, which can then be manually parsed.

.. code-block:: python

                >>> from astroquery.mast import Mast

                >>> service = 'Mast.Name.Lookup'
                >>> params ={'input':"M8",
                ...          'format':'json'}

                >>> response = Mast.service_request_async(service,params)
                >>> result = response[0].json()
                >>> print(result)

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


