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
`here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`_.

.. code-block:: python

                >>> from astroquery.mast import Observations
                >>> observations = Observations.query_region("322.49324 12.16683")
                >>> print(observations[:10])

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

Radius is an optional parameter, the default is 0.2 degrees.

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

To search for observations based on parameters other than position, use query_criteria.
The criteria dictionary has the format ``{"filterName":[value(s)]}``.
The columns that can be filtered on are described `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
Columns with datatype 'float' should be filtered by giving a min and max,
all other data types are filtered by giving a list of acceptable values.
RA and Dec must be given in decimal degrees, and datetimes in MJD.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> observations = Observations.query_criteria({"dataproduct_type":["image"],
                                                                "proposal_pi":"Osten",
                                                                "s_dec":[43.5,45.5]})
                >>> print(observations)

                dataproduct_type calib_level obs_collection ... dataURL   obsid      objID   
                ---------------- ----------- -------------- ... ------- ---------- ----------
                           image           1            HST ...    None 2003520266 2011133418
                           image           1            HST ...    None 2003520267 2011133419
                           image           1            HST ...    None 2003520268 2011133420

Criteria queries may also specify a sky position.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> observations = Observations.query_criteria({"filters":["NUV","FUV"]},objectname="M101")
                >>> print(observations)

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

To get the number of observations in a particular region of the sky without being returned
the observations themselves (for example, to decide if the number of observations will fit
comfortable in memory, or if the query should be broken up) query_counts functions are
available.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> print(Observations.query_region_count("322.49324 12.16683"))
                1804
                
                >>> print(Observations.query_object_count("M8",radius=".02 deg"))
                196

                >>> print(Observations.query_criteria_count({"dataproduct_type":"image",
                                                             "filters":["NUV","FUV"],
                                                             "t_max":[52264.4586,54452.8914]}))
                59033
                           


Downloading Data
================

Getting Product Lists
---------------------

Each observation returned from a MAST query can have one or more associated data products.
Given a single observation or observation id (obsid) `get_product_list` will return
an `astropy.table.Table` containing the associated data products.
The product fields are documented `here <https://mast.stsci.edu/api/v0/_productsfields.html>`_.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> observations = Observations.query_object("M8",radius=".02 deg")
                >>> dataProductsByObservation = Observations.get_product_list(observations[0])
                >>> print(dataProductsByObservation)
                
                  obsID    obs_collection dataproduct_type ...   size   
                ---------- -------------- ---------------- ... -------- 
                9500243833             K2             cube ...     9009 
                9500243833             K2             cube ... 39930404 
                9500243833             K2             cube ... 62213068 
                9500243833             K2             cube ...     1301
                
                >>> obsid = observations[0]['obsid']
                >>> dataProductsByID = Observations.get_product_list(obsid)
                >>> print(dataProductsByID)
                
                  obsID    obs_collection dataproduct_type ...   size   
                ---------- -------------- ---------------- ... -------- 
                9500243833             K2             cube ...     9009 
                9500243833             K2             cube ... 39930404 
                9500243833             K2             cube ... 62213068 
                9500243833             K2             cube ...     1301
                
                >>> print(dataProductsByObservation == dataProductsByID)
                True



Downloading Data Products
-------------------------

Products can be downloaded by giving `download_products` an `astropy.table.Table` of data products,
or a list (or single) obsid.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> manifest = Observations.download_products(dataProductsByID)
                >>> print(manifest)
                
                                                       Local Path                                         Status  ...
                ---------------------------------------------------------------------------------------- -------- ...
                   ./mastDownload_20170504125901/K2/ktwo200071160-c92_lc/k2-tpf-only-target_bw_large.png COMPLETE ...
                ./mastDownload_20170504125901/K2/ktwo200071160-c92_lc/ktwo200071160-c91_lpd-targ.fits.gz    ERROR ...
                ./mastDownload_20170504125901/K2/ktwo200071160-c92_lc/ktwo200071160-c92_lpd-targ.fits.gz COMPLETE ...
                   ./mastDownload_20170504125901/K2/ktwo200071160-c92_lc/k2-tpf-only-target_bw_thumb.png COMPLETE ...

​

Filters can be applied to download only certain types of data products.
Available filters are as follows:

* mrp_only: **Defaults to True.** If true only download "Minimum Recommended Products." 
* group: Product subgroup, e.g. Q2F, RAMP, RAW, UNCAL, TRM.
* extension: File extension, e.g. .fits or .tar.gz.
* product type: Data product type, e.g. image, cube.
* product category: Data product category, e.g. SCIENCE, AUXILIARY, CATALOG.

Filter behavior is AND between the filters and OR within a filter set.

.. code-block:: python
                
                >>> filters = {"mrp_only":False,
                               "group":["RAW", "UNCAL"],
                               "extenstion":"fits"}

Yields all product files with the extension "fits" that are either "RAW" or "UNCAL."

As an alternative to downloading the data files now, the curl_flag can be used to instead get a curl script that can be used to download the files at a later time.

.. code-block:: python
                
                >>> from astroquery.mast import Observations
                >>> manifest = Observations.download_products(dataProductsByID,
                                                              filters={"mrp_only":False, "product category":"SCIENCE"},
                                                              curl_flag=True)
                >>> print(manifest)
                
                Message            Local Path            URL   Status 
                ------- -------------------------------- ---- --------
                None    ./mastDownload_20170504141044.sh None COMPLETE


   
Direct Mast Queries
===================

The Mast class provides more direct access to the MAST interface.  It requires
more knowledge of the inner workings of the MAST API, and should be rarely
needed.  However in the case of new functionality not yet implemented in
astroquery, this class does allow access.  See the `MAST api documentation
<https://mast.stsci.edu/api>`_ for more information.

The basic MAST query function returns query results as an `astropy.table.Table`.

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


If the output is not the MAST json result type it cannot be properly parsed
into an `astropy.table.Table` so the async method should be used to get the raw
http response, which can then be manually parsed.

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

