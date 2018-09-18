.. doctest-skip-all

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

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> obsTable = Observations.query_region("322.49324 12.16683")
                >>> print(obsTable[:10])

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
                >>> obsTable = Observations.query_object("M8",radius=".02 deg")
                >>> print(obsTable[:10])
                
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
Additionally calibration data can be accessed by setting the obstype keyword to 'cal'
(calibration only) or 'all' (calibration and science). 

Argument values are one or more acceptable values for the criterion,
except for fields with a float datatype where the argument should be in the form
[minVal, maxVal]. For non-float type criteria, wildcards (both * and %) may be used.
However, only one wildcarded value can be processed per criterion.

RA and Dec must be given in decimal degrees, and datetimes in MJD.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> obsTable = Observations.query_criteria(dataproduct_type=["image"],
                                                           proposal_pi="Osten",
                                                           s_dec=[43.5,45.5])
                >>> print(obsTable)

                dataproduct_type calib_level obs_collection ... dataURL   obsid      objID   
                ---------------- ----------- -------------- ... ------- ---------- ----------
                           image           1            HST ...    None 2003520266 2011133418
                           image           1            HST ...    None 2003520267 2011133419
                           image           1            HST ...    None 2003520268 2011133420

                >>> obsTable = Observations.query_criteria(filters=["*UV","Kepler"],objectname="M101")
                >>> print(obsTable)

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
                                                            filters=["NUV","FUV"],
                                                            t_max=[52264.4586,54452.8914]))
                59033
                           

Listing Available Missions
--------------------------

To list data missions archived by MAST and avaiable through `astroquery.mast`, use the `~astroquery.mast.ObservationsClass.list_missions` function.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> print(Observations.list_missions())
                ['IUE', 'Kepler', 'K2FFI', 'EUVE', 'HLA', 'KeplerFFI','FUSE',
                'K2', 'HST', 'WUPPE', 'BEFS', 'GALEX', 'TUES','HUT', 'SWIFT']

                
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
                >>> obsTable = Observations.query_object("M8",radius=".02 deg")
                >>> dataProductsByObservation = Observations.get_product_list(obsTable[0:2])
                >>> print(dataProductsByObservation)
                
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
                
                >>> obsids = obsTable[0:2]['obsid']
                >>> dataProductsByID = Observations.get_product_list(obsids)
                >>> print(dataProductsByID)
                
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
                
                >>> print((dataProductsByObservation == dataProductsByID).all())
                True

                



Downloading Data Products
-------------------------

Products can be downloaded by using `~astroquery.mast.ObservationsClass.download_products`,
with a `~astropy.table.Table` of data products, or a list (or single) obsid as the argument.
**By default only Minimum Recommended Products will be downloaded.**

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> obsid = '3000007760'
                >>> dataProductsByID = Observations.get_product_list(obsid)
                >>> manifest = Observations.download_products(dataProductsByID)
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
                                                   productType="SCIENCE",
                                                   curl_flag=True)
                                                   
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
                                                   productSubGroupDescription=["RAW", "UNCAL"],
                                                   extension="fits")
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11p7q_raw.fits to ./mastDownload/HST/IB3P11P7Q/ib3p11p7q_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11p8q_raw.fits to ./mastDownload/HST/IB3P11P8Q/ib3p11p8q_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11phq_raw.fits to ./mastDownload/HST/IB3P11PHQ/ib3p11phq_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11q9q_raw.fits to ./mastDownload/HST/IB3P11Q9Q/ib3p11q9q_raw.fits ... [Done]


Product filtering can also be applied directly to a table of products without proceeding to the download step.

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> dataProductsByID = Observations.get_product_list('2003839997')
                >>> print(len(dataProductsByID))
                31
                
                >>> dataProductsByID = Observations.filter_products(dataProductsByID,
                                                                    productSubGroupDescription=["RAW", "UNCAL"],
                                                                    extenstion="fits")
                >>> print(len(dataProductsByID))
                4


Catalog Queries
===============

The Catalogs class provides access to a subset of the astronomical catalogs stored at MAST.  The catalogs currently available through this interface are:

- The Hubble Source Catalog (HSC)
- The GALEX Catalog (V2 and V3)
- The Gaia (DR1 and DR2) and TGAS Catalogs
- The TESS Input Catalog (TIC)
- The Disk Detective Catalog

Positional Queries
------------------

Positional queries can be based on a sky position or a target name.
The returned fields vary by catalog, find the field documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.html>`__. If no catalog is specified, the Hubble Source Catalog will be queried.

.. code-block:: python

                >>> from astroquery.mast import Catalogs
                >>> catalogData = Catalogs.query_object("158.47924 -7.30962", catalog="Galex")
                >>> print(catalogData[:10])

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
                >>> catTable = Catalogs.query_region("322.49324 12.16683", catalog="HSC", magtype=2)

                WARNING: MaxResultsWarning: Maximum catalog results returned, may not include all
                sources within radius. [astroquery.mast.core]

                >>> print(catTable[:10])

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
                >>> catalogData = Catalogs.query_object("M10", radius=.02, catalog="TIC")
                >>> print(catalogData[:10])

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

                
Both the Hubble Source Catalog and the Gaia Catalog have multiple versions.
An optional version parameter allows you to select which version you want, the default is the highest version.

.. code-block:: python

                >>> catalogData = Catalogs.query_region("158.47924 -7.30962", radius=0.1,
                >>>                                      catalog="Gaia", version=2)
                >>> print("Number of results:",len(catalogData))
                >>> print(catalogData[:4])

                Number of results: 111
                    solution_id             designation          ...      distance     
                ------------------- ---------------------------- ... ------------------
                1635721458409799680 Gaia DR2 3774902350511581696 ... 0.6327882551927051
                1635721458409799680 Gaia DR2 3774901427093274112 ... 0.8438875783827048
                1635721458409799680 Gaia DR2 3774902148648277248 ... 0.9198397322382648
                1635721458409799680 Gaia DR2 3774902453590798208 ... 1.3578882400285217


Catalog Criteria Queries
------------------------

The TESS Input Catalog (TIC, and Disk Detective Catalog can also be queried based on non-positional criteria.

.. code-block:: python

                >>> from astroquery.mast import Catalogs
                >>> catalogData = Catalogs.query_criteria(catalog="Tic",Bmag=[30,50],objType="STAR")
                >>> print(catalogData)

                    ID    version  HIP TYC ... disposition duplicate_id priority   objID  
                --------- -------- --- --- ... ----------- ------------ -------- ---------
                 81609218 20171221  --  -- ...          --           --       -- 217917514
                 23868624 20171221  --  -- ...          --           --       -- 296973171
                406300991 20171221  --  -- ...          --           --       -- 400575018


.. code-block:: python

                >>> from astroquery.mast import Catalogs
                >>> catalogTable = Catalogs.query_criteria(catalog="DiskDetective",
                                                           objectname="M10",radius=2,state="complete")
                >>> print(catalogTable)

                    designation     ...                    ZooniverseURL                    
                ------------------- ... ----------------------------------------------------
                J165628.40-054630.8 ... https://talk.diskdetective.org/#/subjects/AWI0005cka
                J165748.96-054915.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ckd
                J165427.11-022700.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ck5
                J165749.79-040315.1 ... https://talk.diskdetective.org/#/subjects/AWI0005cke
                J165327.01-042546.2 ... https://talk.diskdetective.org/#/subjects/AWI0005ck3
                J165949.90-054300.7 ... https://talk.diskdetective.org/#/subjects/AWI0005ckk
                J170314.11-035210.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ckv

                
Hubble Source Catalog (HSC) specific queries
--------------------------------------------

Given an HSC Match ID, return all catalog results.

.. code-block:: python

                >>> from astroquery.mast import Catalogs
                >>> catalogData = Catalogs.query_object("M10", radius=.02, catalog="HSC")
                >>> matchId = catalogData[0]["MatchID"]
                >>> print(matchId)

                17554326

                >>> matches = Catalogs.query_hsc_matchid(matchId)
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
                >>> allSpectra = Catalogs.get_hsc_spectra()
                >>> print(allSpectra[:10])

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
                >>> allSpectra = Catalogs.get_hsc_spectra()
                >>> manifest = Catalogs.download_hsc_spectra(allSpectra[100:104])

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
                


Accessing Proprietary Data
==========================

To access data that is not publicly available users may log into their
`MyST Account <https://archive.stsci.edu/registration/index.html>`_.
This can be done by using the `~astroquery.mast.MastClass.login` function,
or by initializing a class instance with a username/password.
If a password is not supplied, the user will be prompted to enter one.

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> Observations.login(username="testUser@stsci.edu",password="testPwd")

                Authentication successful!
                Session Expiration: 600 minute(s)

                >>> sessionInfo = Observations.session_info()

                Session Expiration: 559.0 min
                Username: testUser@stsci.edu
                First Name: Test
                Last Name: User

              
.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> mySession = Observations(username="testUser@stsci.edu",password="testPwd")

                Authentication successful!
                Session Expiration: 600 minute(s)

                >>> sessionInfo = mySession.session_info()

                Session Expiration: 559.0 min
                Username: testUser@stsci.edu
                First Name: Test
                Last Name: User

\* For security passwords should not be typed into a terminal or Jupyter notebook
but instead input using a more secure method such as `~getpass.getpass`.


MAST login can also be achieved with a "session token," from an existing valid MAST session.

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> from astroquery.mast import Mast
                >>> myObsSession = Observations(username="testUser@stsci.edu",password="testPwd")

                Authentication successful!
                Session Expiration: 600 minute(s)

                >>> myToken = myObsSession.get_token()
                >>> Mast.login(session_token=myToken)

                Authentication successful!
                Session Expiration: 599 minute(s)


MAST sessions expire after 600 minutes, at which point the user must login again.
The ``store_password`` argument can be used to store the username and password securely in the user's keyring.
If the username/password are thus stored, only the username need be entered to login.
This password can be overwritten using the ``reenter_password`` argument.
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
                              'dec':54.5,
                              'radius':0.2}
        
                >>> observations = Mast.mashup_request(service, params)
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
                             'format':'json'}
        
                >>> response = Mast.mashup_request_async(service,params)        
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


Reference/API
=============

.. automodapi:: astroquery.mast
    :no-inheritance-diagram:

