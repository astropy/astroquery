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
                >>> observations = Observations.query_object("M8",radius=".02 deg")
                >>> print(observations[:10])
                
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
                                                   mrp_only=False,
                                                   productType="SCIENCE",
                                                   curl_flag=True)
                                                   
                Downloading URL https://mast.stsci.edu/portal/Download/stage/anonymous/public/514cfaa9-fdc1-4799-b043-4488b811db4f/mastDownload_20170629162916.sh to ./mastDownload_20170629162916.sh ... [Done]

                
Filtering
^^^^^^^^^

Filter keyword arguments can be applied to download only data products that meet the given criteria.
Available filters are "mrp_only" (Minium Recommended Products), "extension" (file extension),
and all products fields listed `here <https://mast.stsci.edu/api/v0/_productsfields.html>`_.

**Important: mrp_only defaults to True.**

The ‘AND' operation is performed for a list of filters, and the ‘OR' operation is performed within a filter set.
The below example illustrates downloading all product files with the extension "fits" that are either "RAW" or "UNCAL."

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> Observations.download_products('2003839997',
                                                   mrp_only=False,
                                                   productSubGroupDescription=["RAW", "UNCAL"],
                                                   extension="fits")
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11p7q_raw.fits to ./mastDownload/HST/IB3P11P7Q/ib3p11p7q_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11p8q_raw.fits to ./mastDownload/HST/IB3P11P8Q/ib3p11p8q_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11phq_raw.fits to ./mastDownload/HST/IB3P11PHQ/ib3p11phq_raw.fits ... [Done]
                Downloading URL https://mast.stsci.edu/api/v0/download/file/HST/product/ib3p11q9q_raw.fits to ./mastDownload/HST/IB3P11Q9Q/ib3p11q9q_raw.fits ... [Done]


Product filtering can also be appllied directly to a table of products without proceeding to the download step. 

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> dataProductsByID = Observations.get_product_list('2003839997')
                >>> print(len(dataProductsByID))
                31
                
                >>> dataProductsByID = Observations.filter_products(dataProductsByID,
                                                                    mrp_only=False,
                                                                    productSubGroupDescription=["RAW", "UNCAL"],
                                                                    extenstion="fits")
                >>> print(len(dataProductsByID))
                4


               


   
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

