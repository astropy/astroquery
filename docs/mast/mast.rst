.. doctest-skip-all

.. _astroquery.mast:

********************************
MAST Queries (`astroquery.mast`)
********************************

Getting Started
===============

This module can be used to query the Barbara A. Mikulski Archive for Space Telescopes (MAST). Below are examples of the types of queries that can be used, and how to access data products.

Positional Queries
------------------

Positional queries can be based on a sky position or an target name.  The observation fields are documented `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`_.

.. code-block:: python

                >>> from astroquery.mast import Mast
                >>> observations = Mast.query_region("322.49324 12.16683")
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

                >>> from astroquery.mast import Mast
                >>> observations = Mast.query_object("M8",radius=".02 deg")
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
                        

Getting Observation Counts
--------------------------

To get the number of observations in a particular region of the sky without being returned the observations themself (for example, to decide if the number of observations will fit comfortable in memory, or if the query shoudl be proken up) query_counts functions are available.

.. code-block:: python
                
                >>> from astroquery.mast import Mast
                >>> print(Mast.query_region_count("322.49324 12.16683"))
                1804
                
                >>> print(Mast.query_object_count("M8",radius=".02 deg"))
                196


Downloading Data
================

Getting Product Lists
---------------------

Each observation returned from a MAST query can have one or more associated data products.
Given a single observation or observation id (obsid) `get_product_list` will return
an `astropy.table.Table` containing the associated data products.
The product fields are documented `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`_.

.. code-block:: python
                
                >>> from astroquery.mast import Mast
                >>> observations = Mast.query_object("M8",radius=".02 deg")
                >>> dataProductsByObservation = Mast.get_product_list(observations[0])
                >>> print(dataProductsByObservation)
                
                  obsID    obs_collection dataproduct_type ...   size   
                ---------- -------------- ---------------- ... -------- 
                9500243833             K2             cube ...     9009 
                9500243833             K2             cube ... 39930404 
                9500243833             K2             cube ... 62213068 
                9500243833             K2             cube ...     1301
                
                >>> obsid = observations[0]['obsid']
                >>> dataProductsByID = Mast.get_product_list(obsid)
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
                
                >>> from astroquery.mast import Mast
                >>> manifest = Mast.download_products(dataProductsByID)
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

* mrp_only: **Defaults to True.** If true only download "Minimum Reccommended Products." 
* group: Product subgroup, e.g. Q2F, RAMP, RAW, UNCAL, TRM.
* extension: File extension, e.g. .fits or .tar.gz.
* product type: Data product type, e.g. image, cube.
* product category: Data product category, e.g. SCIENCE, AUXILIARY, CATALOG.

Filter behavior is AND between the filters and OR with a filter set.

.. code-block:: python
                >>> filters = {"mrp_only":False,
                               "group":["RAW", "UNCAL"],
                               "extenstion":"fits"}

Yields all product files with the extension "fits" that are either "RAW" or "UNCAL."

As an alternative to downloading the data files now, the curl_flag can be used to instead get a curl script that can be used to download the file at a later time.

.. code-block:: python
                
                >>> from astroquery.mast import Mast
                >>> manifest = Mast.download_products(dataProductsByID,
                                                      filters={"mrp_only":False, "product category":"SCIENCE"},
                                                      curl_flag=True)
                >>> print(manifest)
                
                Message            Local Path            URL   Status 
                ------- -------------------------------- ---- --------
                None    ./mastDownload_20170504141044.sh None COMPLETE



Reference/API
=============

.. automodapi:: astroquery.mast
    :no-inheritance-diagram:

