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

Positional queries can be based on a sky position or a target name.  The observation fields are documented `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`_.

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
                        




Direct Mast Queries
===================

The Mast class provides more direct access to the MAST interface.
It requres more knowledge of the inner workings of the MAST API, and should be rarely needed.
However in the case of new functionality not yet implemented in astroquery, this class does allow access.
See the `MAST api documentation <https://mast.stsci.edu/api>`_ for more information.

The basic mast query function returns query results as an `astropy.table.Table`.

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


If the output is not the MAST json result type it cannot be properly parsed into an `astropy.table.Table` so the async method shoudl be used to get the raw http response, which can then be manually parsed.

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

