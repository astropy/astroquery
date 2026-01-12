
************
MAST Queries
************

The `~astroquery.mast.MastClass` class provides low-level, direct access to the
`MAST Portal API <https://mast.stsci.edu/api/v0/>`__.
It is intended for advanced use cases and requires familiarity with the
structure and parameters of the MAST API. Most users will not need to interact
with this class directly. However, it can be useful when accessing new or
specialized functionality that has not yet been wrapped by higher-level
astroquery interfaces.

The `~astroquery.mast.MastClass.mast_query` method allows users to submit requests to the available
`MAST services <https://mast.stsci.edu/api/v0/_services.html>`__ by specifying
the appropriate service name and parameters. Query results are returned as an
`~astropy.table.Table`, enabling straightforward inspection and downstream
analysis.

Filtered Mast Queries
=====================

MAST filtered services (i.e. those with "filtered" in the service name) allow users to
query observational metadata using a combination of service-specific parameters, general
MashupRequest properties, and column-based filters. These queries return a table of
observations that match the specified criteria.

Valid keyword arguments fall into three broad categories:

1. **Service-specific Parameters**

   Each filtered service defines its own set of supported parameters, which correspond to
   mission- or instrument-specific metadata fields. The available parameters and their meanings
   are described in the `service documentation <https://mast.stsci.edu/api/v0/_services.html>`__ and, for JWST
   services specifically, the `JWST Field Documentation <https://mast.stsci.edu/api/v0/_jwst_inst_keywd.html>`__.

2. **MashupRequest Properties**

   General request options such as pagination, sorting, or formatting are handled through
   ``MashupRequest`` properties. A full list of supported properties is available in the
   `MashupRequest Class Reference <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`__.

3. **Column-based Filters**

   Any keyword argument that does not correspond to a positional constraint or a
   ``MashupRequest`` property is interpreted as a column filter. These filters restrict the query
   results based on the values in a specific metadata column.

   Filtering behavior depends on the type of column being queried:

   - **Discrete columns** (for example, instrument names or proposal categories)
     accept a single value or a list of values. Matches must be exact.
   - **Continuous columns** (for example, exposure time or wavelength)
     accept a single value, a list of values, or a range. Ranges are specified using a dictionary
     in the form ``{'min': minVal, 'max': maxVal}``.

The ``columns`` parameter controls which metadata fields are included in the response. It may
be provided as a comma-separated string or as a list of column names. By default, a standard
set of columns is returned.

The example below demonstrates a query against a JWST filtered service, using column names
and filters specific to JWST data products. For a complete list of valid parameters and
metadata fields, refer to the `JWST Field Documentation <https://mast.stsci.edu/api/v0/_jwst_inst_keywd.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Jwst.Filtered.Nirspec',
   ...                                targoopp='T',
   ...                                productLevel=['2a', '2b'],
   ...                                duration={'min': 810, 'max': 820},
   ...                                columns=['filename', 'targoopp', 'productLevel', 'duration'])
   >>> print(observations) # doctest: +IGNORE_OUTPUT
                     filename                   targoopp productLevel duration
   -------------------------------------------- -------- ------------ --------
       jw05324004001_03102_00004_nrs2_rate.fits        t           2a  816.978
   jw05324004001_03102_00004_nrs2_rateints.fits        t           2a  816.978
       jw05324004001_03102_00001_nrs2_rate.fits        t           2a  816.978
   jw05324004001_03102_00001_nrs2_rateints.fits        t           2a  816.978
       jw05324004001_03102_00005_nrs2_rate.fits        t           2a  816.978
                                            ...      ...          ...      ...
        jw05324004001_03102_00003_nrs1_s2d.fits        t           2b  816.978
        jw05324004001_03102_00003_nrs1_x1d.fits        t           2b  816.978
        jw05324004001_03102_00002_nrs1_cal.fits        t           2b  816.978
        jw05324004001_03102_00002_nrs1_s2d.fits        t           2b  816.978
        jw05324004001_03102_00002_nrs1_x1d.fits        t           2b  816.978
   Length = 25 rows


TESS Filtered Queries
---------------------

TESS queries have 2 types of filtered services. To output a table and specify
columns for a TESS query, use TIC or CTL services with '.Rows' on the end
(e.g. `Mast.Catalogs.Filtered.Tic.Rows
<https://mast.stsci.edu/api/v0/_services.html#MastCatalogsFilteredTicRows>`__).
Valid parameters for TIC and CTL services are detailed in the
`TIC Field Documentation <https://mast.stsci.edu/api/v0/_t_i_cfields.html>`__.

TESS filtered queries are available through two related service types: **TIC** (TESS Input
Catalog) and **CTL** (Candidate Target List). The TIC is a comprehensive catalog of known
stellar properties, while the CTL is a curated subset optimized for identifying promising
TESS targets. To return results as a table and to explicitly control which columns are
included in the response, users should query the corresponding ``.Rows`` services (for
example,
`Mast.Catalogs.Filtered.Tic.Rows <https://mast.stsci.edu/api/v0/_services.html#MastCatalogsFilteredTicRows>`__).

The TIC and CTL ``.Rows`` services support column-based filtering and return results as an
`~astropy.table.Table`. Valid query parameters and available metadata fields for these
services are described in the `TIC Field Documentation <https://mast.stsci.edu/api/v0/_t_i_cfields.html>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Catalogs.Filtered.Tic.Rows',
   ...                                columns='id',
   ...                                dec={'min': -90, 'max': -30},
   ...                                Teff={'min': 4250, 'max': 4500},
   ...                                logg={'min': 4.5, 'max': 5.0},
   ...                                Tmag={'min': 8, 'max': 10})
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

TESS filtered services without ``.Rows`` in the service name are intended for **count
queries** only. These services return the number of matching records and do not return tabular
results, so the ``columns`` parameter is ignored.

Conversely, ``.Rows`` services must be used when requesting tabular output. Attempting to use
a ``.Rows`` service for a count-only query will result in an error.

.. doctest-skip::

   >>> from astroquery.mast import Mast
   ...
   >>> observations = Mast.mast_query('Mast.Catalogs.Filtered.Tic.Rows',
   ...                                columns = 'COUNT_BIG(*)',
   ...                                dec={'min': -90, 'max': -30},
   ...                                Teff={'min': 4250, 'max': 4500},
   ...                                logg={'min': 4.5, 'max': 5.0},
   ...                                Tmag={'min': 8, 'max': 10})
   Traceback (most recent call last):
   ...
   astroquery.exceptions.RemoteServiceError: Incorrect syntax near '*'.


Cone Searches
=============

MAST's cone search services use the parameters 'ra', 'dec', and 'radius' and return
a table of observations with all columns present.

MAST cone search services perform **positional searches on the sky**, returning all records
within a circular region centered on a specified coordinate. These services are useful when
you want to find observations or catalog entries near a known sky position without applying
additional metadata filters.

Cone searches are defined by three required parameters:

- ``ra``: Right ascension of the search center, in decimal degrees
- ``dec``: Declination of the search center, in decimal degrees
- ``radius``: Search radius, in decimal degrees

Cone search services return a table of matching observations and **always include all
available columns** in the response. Unlike filtered services, cone searches **do not support
column selection or column-based filtering** through keyword arguments. Attempting to use
these parameters with a cone search service will either result in an error or warning.

Because cone searches operate purely on spatial constraints, they are often used as a
starting point for exploratory searches or for identifying nearby data products before
applying more restrictive filters through other MAST services.

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


Advanced Service Requests
=========================

Some MAST services, such as
`Mast.Name.Lookup <https://mast.stsci.edu/api/v0/_services.html#MastNameLookup>`__, return
response formats that are not compatible with `~astroquery.mast.MastClass.mast_query`.
The method expects results in a standard JSON format so that they can
be automatically parsed into an `~astropy.table.Table`. When a service returns a different
response type by default, this automatic conversion is not possible.

For these services, users should instead call
`~astroquery.mast.MastClass.service_request_async`, which returns the raw HTTP response from
the MAST Portal API. The response content can then be inspected and parsed manually according to the
service’s documented output format.

.. doctest-remote-data::

   >>> from astroquery.mast import Mast
   ...
   >>> service = 'Mast.Name.Lookup'
   >>> params = {'input': 'M8',
   ...           'format': 'json'}
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
