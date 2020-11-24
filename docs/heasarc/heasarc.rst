.. doctest-skip-all

.. _astroquery.heasarc:

**************************************
HEASARC Queries (`astroquery.heasarc`)
**************************************

Getting started
===============

This is a python interface for querying the
`HEASARC <https://heasarc.gsfc.nasa.gov/>`__
archive web service.

The capabilities are currently very limited ... feature requests and contributions welcome!

Getting lists of available datasets
-----------------------------------

There are two ways to obtain a list of objects. The first is by querying around
an object by name:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> mission = 'rosmaster'
    >>> object_name = '3c273'
    >>> table = heasarc.query_object(object_name, mission=mission)
    >>> table[:3].pprint()
       SEQ_ID   INSTRUMENT EXPOSURE   RA    DEC           NAME         PUBLIC_DATE  SEARCH_OFFSET_
                              S     DEGREE DEGREE                          MJD
    ----------- ---------- -------- ------ ------ -------------------- ----------- ---------------
    RH701576N00 HRI           68154 187.28   2.05 3C 273                     50186  0.192 (3C273)
    RP600242A01 PSPCB         24822 186.93    1.6 GIOVANELLI-HAYNES CL       50437 34.236 (3C273)
    RH700234N00 HRI           17230 187.28   2.05 3C 273                     50312  0.192 (3C273)

Alternatively, a query can also be conducted around a specific set of sky
coordinates:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> heasarc = Heasarc()
    >>> mission = 'rosmaster'
    >>> coords = SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
    >>> table = heasarc.query_region(coords, mission=mission, radius='1 degree')
    >>> table[:3].pprint()
       SEQ_ID   INSTRUMENT EXPOSURE   RA   ...         NAME         PUBLIC_DATE                  SEARCH_OFFSET_
                              S     DEGREE ...                          MJD
    ----------- ---------- -------- ------ ... -------------------- ----------- -----------------------------------------------
    RH701576N00 HRI           68154 187.28 ... 3C 273                     50186  0.191 (187.27792281980047,2.0524148595265435)
    RP600242A01 PSPCB         24822 186.93 ... GIOVANELLI-HAYNES CL       50437 34.237 (187.27792281980047,2.0524148595265435)
    RH700234N00 HRI           17230 187.28 ... 3C 273                     50312  0.191 (187.27792281980047,2.0524148595265435)

Note that the :meth:`~astroquery.heasarc.HeasarcClass.query_region` converts 
the passed coordinates to the FK5 reference frame before submitting the query.

Modifying returned table columns
--------------------------------

Each table has a set of default columns that are returned when querying the
database. You can return all available columns for a given mission by specifying
the ``fields`` parameter in either of the above queries. For exampe:

.. code-block:: python

    >>> table = heasarc.query_object(object_name='3c273', mission='rosmaster', fields='All')

will return all available columns from the ``rosmaster`` mission table.
Alternatively, a comma-separated list of column names can also be provided to
specify which columns will be returned:

.. code-block:: python

    >>> table = heasarc.query_object(object_name='3c273', mission='rosmaster', fields='EXPOSURE,RA,DEC')
    >>> table[:3].pprint()
    EXPOSURE   RA    DEC    SEARCH_OFFSET_
       S     DEGREE DEGREE
    -------- ------ ------ ---------------
       68154 187.28   2.05  0.192 (3C273)
       24822 186.93    1.6 34.236 (3C273)
       17230 187.28   2.05  0.192 (3C273)

Note that the ``SEARCH_OFFSET_`` column will always be included in the results.
If a column name is passed to the ``fields`` parameter which does not exist in
the requested mission table, the query will fail. To obtain a list of available 
columns for a given mission table, do the following:

.. code-block:: python

    >>> cols = heasarc.query_mission_cols(mission='rosmaster')
    >>> print(cols)
    ['SEQ_ID', 'INSTRUMENT', 'EXPOSURE', 'RA', 'DEC', 'NAME', 'PUBLIC_DATE', 
    'BII', 'CLASS', 'DEC_1950', 'DIST_DATE', 'END_DATE','FILTER', 'FITS_TYPE', 
    'INDEX_ID', 'LII', 'PI_FNAME', 'PI_LNAME', 'PROC_REV', 'QA_NUMBER', 'RA_1950', 
    'REQUESTED_EXPOSURE', 'ROR', 'SITE', 'START_DATE', 'SUBJ_CAT', 'TITLE', 
    'SEARCH_OFFSET_']
    
Additional query parameters
---------------------------

By default, the :meth:`~astroquery.heasarc.HeasarcClass.query_object` method
returns all entries within approximately one degree of the specified object.
This can be modified by supplying the ``radius`` parameter. This parameter
takes a distance to look for objects. The following modifies the search radius
to 120 arcmin:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius='120 arcmin')

``radius`` takes an angular distance specified as an astropy Quantity object, 
or a string that can be parsed into one (e.g., '1 degree' or 1*u.degree). The
following are equivalent:

.. code-block:: python

    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius='120 arcmin')
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius='2 degree')
    >>> from astropy import units as u
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius=120*u.arcmin)
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius=2*u.degree)

As per the astroquery specifications, the :meth:`~astroquery.heasarc.HeasarcClass.query_region`
method requires the user to supply the radius parameter.

The results can also be sorted by the value in a given column using the ``sortvar``
parameter. The following sorts the results by the value in the 'EXPOSURE' column.

.. code-block:: python

    >>> table = heasarc.query_object(object_name, mission='rosmaster', sortvar='EXPOSURE')
    >>> table[:3].pprint()
       SEQ_ID   INSTRUMENT EXPOSURE   RA    DEC           NAME         PUBLIC_DATE  SEARCH_OFFSET_
                              S     DEGREE DEGREE                          MJD
    ----------- ---------- -------- ------ ------ -------------------- ----------- ---------------
    RH120001N00 HRI               0 187.27   2.05 XRT/HRI NORTH DUMMY        55844  0.495 (3C273)
    RH701979N00 HRI             354 187.28   2.05 3C273                      50137  0.192 (3C273)
    RP141520N00 PSPCB           485 187.27   2.05 3C273                      49987  0.495 (3C273)

Setting the ``resultmax`` parameter controls the maximum number of results to be
returned. The following will store only the first 10 results:

.. code-block:: python

    >>> table = heasarc.query_object(object_name, mission='rosmaster', resultmax=10)

All of the above parameters can be mixed and matched to refine the query results.

Getting list of available missions
----------------------------------

The ``query_mission_list()`` method will return a list of available missions 
that can be queried.

.. code-block:: python
    
    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_mission_list()
    >>> table.pprint()
    Archive    name               Table_Description
    ------- ---------- ----------------------------------------
    HEASARC         a1           HEAO 1 A1 X-Ray Source Catalog
    HEASARC    a1point                    HEAO 1 A1 Lightcurves
    HEASARC  a2lcpoint            HEAO 1 A2 Pointed Lightcurves
    HEASARC   a2lcscan            HEAO 1 A2 Scanned Lightcurves
    HEASARC      a2led                    HEAO 1 A2 LED Catalog
    HEASARC      a2pic             HEAO 1 A2 Piccinotti Catalog
    HEASARC    a2point               HEAO 1 A2 Pointing Catalog
    HEASARC    a2rtraw                      HEAO 1 A2 Raw Rates
        ...        ...                                      ...
    HEASARC  xteasscat          XTE All-Sky Slew Survey Catalog
    HEASARC   xteindex                 XTE Target Index Catalog
    HEASARC  xtemaster                       XTE Master Catalog
    HEASARC   xtemlcat          XTE Mission-Long Source Catalog
    HEASARC    xteslew            XTE Archived Public Slew Data
    HEASARC       xwas             XMM-Newton Wide Angle Survey
    HEASARC       zcat CfA Redshift Catalog (June 1995 Version)
    HEASARC zwclusters                          Zwicky Clusters
    HEASARC      zzbib             METADATA: Bibliography Codes
    Length = 956 rows

The returned table includes both the names and a short description of each 
mission table.

Downloading identified datasets
-------------------------------

Not implemented yet.

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
