
************
MAST Queries
************

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


Many mast services, specifically JWST and Catalog services, require the two principal keywords, 'columns' and 'filters',
to list parameters. Positional services will also require right ascension and declination parameters, either in
addition to columns and filters or on their own. For example, the cone search service only requires the 'ra' and
'dec' parameters. Using the wrong service parameters will result in an error. Read the
`MAST API services documentation <https://mast.stsci.edu/api/v0/_services.html>`__ for more information on valid
service parameters.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> service = 'Mast.Caom.Cone'
   >>> params = {'columns': "*",
   ...           'filters': {}}
   >>> observations = Mast.service_request(service, params)
   Traceback (most recent call last):
   ...
   astroquery.exceptions.RemoteServiceError: Request Object is Missing Required Parameter : RA


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