
************
MAST Queries
************

The Mast class provides more direct access to the MAST interface.  It requires
more knowledge of the inner workings of the MAST API, and should be rarely
needed.  However in the case of new functionality not yet implemented in
astroquery, this class does allow access.  See the
`MAST api documentation <https://mast.stsci.edu/api/v0/>`__ for more
information.

The basic MAST query function allows users to query through the following
`MAST Services <https://mast.stsci.edu/api/v0/_services.html>`__ using
their corresponding parameters and returns query results as an
`~astropy.table.Table`.

Filtered Mast Queries
=====================

MAST's Filtered services use the parameters 'columns' and 'filters'. The 'columns'
parameter is a required string that specifies the columns to be returned as a
comma-separated list. The 'filters' parameter is a required list of filters to be
applied. The `~astroquery.mast.MastClass.mast_query` method accepts that list of
filters as keyword arguments paired with a list of values, similar to
`~astroquery.mast.ObservationsClass.query_criteria`.

The following example uses a JWST service with column names and filters specific to
JWST services. For the full list of valid parameters view the
`JWST Field Documentation <https://mast.stsci.edu/api/v0/_jwst_inst_keywd.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Jwst.Filtered.Nirspec',
   ...                                columns='title, instrume, targname',
   ...                                targoopp=['T'])
   >>> print(observations) # doctest: +IGNORE_OUTPUT
               title               instrume     targname
   ------------------------------- -------- ----------------
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
   De-Mystifying SPRITEs with JWST  NIRSPEC      SPIRITS18nu
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
                               ...      ...              ...
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
                         ToO Comet  NIRSPEC  ZTF (C/2022 E3)
   Length = 319 rows


TESS Queries
------------

TESS queries have 2 types of filtered services. To output a table and specify
columns for a TESS query, use TIC or CTL services with '.Rows' on the end
(e.g. `Mast.Catalogs.Filtered.Tic.Rows
<https://mast.stsci.edu/api/v0/_services.html#MastCatalogsFilteredTicRows>`__).
Valid parameters for TIC and CTL services are detailed in the
`TIC Field Documentation <https://mast.stsci.edu/api/v0/_t_i_cfields.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Catalogs.Filtered.Tic.Rows',
   ...                                columns='id',
   ...                                dec=[{'min': -90, 'max': -30}],
   ...                                Teff=[{'min': 4250, 'max': 4500}],
   ...                                logg=[{'min': 4.5, 'max': 5.0}],
   ...                                Tmag=[{'min': 8, 'max': 10}])
   >>> print(observations) # doctest: +IGNORE_OUTPUT
      ID
   ---------
   320274328
   408290683
   186485314
   395586623
   82007673
   299550797
   ...
   333372236
   394008846
   261525246
   240766734
   240849919
   219338557
   92131304
   Length = 814 rows

TESS services without '.Rows' in the title are used for count queries and will
not mask the output tables using the columns parameter. Additionally, using a
'.Rows' service for a count query will result in an error.

.. doctest-skip::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Catalogs.Filtered.Tic.Rows',
   ...                                columns = 'COUNT_BIG(*)',
   ...                                dec=[{'min': -90, 'max': -30}],
   ...                                Teff=[{'min': 4250, 'max': 4500}],
   ...                                logg=[{'min': 4.5, 'max': 5.0}],
   ...                                Tmag=[{'min': 8, 'max': 10}])
   Traceback (most recent call last):
   ...
   astroquery.exceptions.RemoteServiceError: Incorrect syntax near '*'.


Cone Searches
=============

MAST's cone search services use the parameters 'ra', 'dec', and 'radius' and return
a table of observations with all columns present.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Caom.Cone',
   ...                                ra=184.3,
   ...                                dec=54.5,
   ...                                radius=0.2)
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


Cone search services only require positional parameters. Using the wrong service
parameters will result in an error. Read the
`MAST API services documentation <https://mast.stsci.edu/api/v0/_services.html>`__
for more information on valid service parameters.

.. doctest-skip::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Caom.Cone',
   ...                                columns='ra',
   ...                                Teff=[{'min': 4250, 'max': 4500}],
   ...                                logg=[{'min': 4.5, 'max': 5.0}])
   Traceback (most recent call last):
   ...
   astroquery.exceptions.RemoteServiceError: Request Object is Missing Required Parameter : RA

Using the 'columns' parameter in addition to the required cone search parameters will
result in a warning.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Catalogs.GaiaDR1.Cone',
   ...                                columns="ra",
   ...                                ra=254.287,
   ...                                dec=-4.09933,
   ...                                radius=0.02) # doctest: +SHOW_WARNINGS
   InputWarning: 'columns' parameter will not mask non-filtered services

Advanced Service Request
========================

Certain MAST Services, such as `Mast.Name.Lookup
<https://mast.stsci.edu/api/v0/_services.html#MastNameLookup>`__ will not work with
`astroquery.mast.MastClass.mast_query` due to it's return type. If the output of a query
is not the MAST json result type it cannot be properly parsed into a `~astropy.table.Table`.
In this case, the `~astroquery.mast.MastClass.service_request_async` method should be used
to get the raw http response, which can then be manually parsed.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> service = 'Mast.Name.Lookup'
   >>> params ={'input':"M8",
   ...          'format':'json'}
   ...
   >>> response = Mast.service_request_async(service, params)
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
