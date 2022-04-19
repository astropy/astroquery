.. doctest-skip-all

.. _astroquery.jplhorizons:

***********************************************************************************
JPL Horizons Queries (`astroquery.jplhorizons`/astroquery.solarsystem.jpl.horizons)
***********************************************************************************

.. Warning::

   The default search behavior has changed.  In v0.4.3 and earlier, the default
   ``id_type`` was ``'smallbody'``.  With v0.4.4, the default is ``None``, which
   implements JPL Horizons's `default behavior
   <https://ssd.jpl.nasa.gov/horizons/manual.html#select>`_: search major bodies
   first, and if no major bodies are found, then search small bodies.

.. Note::

   Due to serverside changes the ``jplhorizons`` module requires astroquery v0.4.1 or newer.
   Previous versions are not expected to function, please upgrade the package if you observe any issues.

Overview
========


The :class:`~astroquery.jplhorizons.HorizonsClass` class provides an
interface to services provided by the `Solar System Dynamics group at
the Jet Propulation Laboratory`_.

Because of its relevance to Solar System science, this service can
also be accessed from the topical submodule
`astroquery.solarsystem.jpl`. The functionality of that service is
identical to the one presented here.

In order to query information for a specific Solar System body, a
``Horizons`` object has to be instantiated:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='Ceres', location='568', epochs=2458133.33546)
   >>> print(obj)
   JPLHorizons instance "Ceres"; location=568, epochs=[2458133.33546], id_type=None

``id`` refers to the target identifier and is mandatory; the exact
string will be used in the query to the Horizons system.

``location`` means either the observer's location (e.g., Horizons ephemerides
query) or the body relative to which orbital elements are provided (e.g.,
Horizons orbital elements or vectors query); the same codes as `used by Horizons
<https://ssd.jpl.nasa.gov/horizons/manual.html#center>`_ are used here, which
includes `MPC Observatory codes`_. The default is ``location=None``, which uses
a geocentric location for ephemerides queries and the Sun as central body for
orbital elements and state vector queries. User-defined topocentric locations
for ephemerides queries can be provided, too, in the form of a dictionary. The
dictionary has to be formatted as follows: {``'lon'``: longitude in degrees
(East positive, West negative), ``'lat'``: latitude in degrees (North positive,
South negative), ``'elevation'``: elevation in km above the reference
ellipsoid}. In addition, ``'body'`` can be set to the Horizons body ID of the
central body if different from Earth; by default, it is assumed that this
location is on Earth if it has not been specifically set. The following example
uses the coordinates of the `Statue of Liberty
<https://www.google.com/maps/place/Statue+of+Liberty+National+Monument/@40.6892534,-74.0466891,17z/data=!3m1!4b1!4m5!3m4!1s0x89c25090129c363d:0x40c6a5770d25022b!8m2!3d40.6892494!4d-74.0445004>`_
as the observer's location:

    >>> statue_of_liberty = {'lon': -74.0466891,
    ...                      'lat': 40.6892534,
    ...                      'elevation': 0.093}
    >>> obj = Horizons(id='Ceres',
    ...                location=statue_of_liberty,
    ...                epochs=2458133.33546)
    JPLHorizons instance "Ceres"; location={'lon': -74.0466891, 'lat': 40.6892534, 'elevation': 0.093}, epochs=[2458133.33546], id_type=None



``epochs`` is either a scalar or list of Julian dates (floats or strings) in the
case of discrete epochs, or, in the case of a range of epochs, a dictionary that
has to include the keywords ``start``, ``stop`` (both using the following format
"YYYY-MM-DD [HH:MM:SS]"), and ``step`` (e.g., ``'1m'`` for one minute,
``'3h'`` three hours, ``'10d'`` for ten days). Note that all input epochs, both
calendar dates/times and Julian Dates, refer to UTC for ephemerides queries, TDB
for element queries and vector queries. By default, ``epochs=None``, which uses
the current date and time.

``id_type`` controls how `Horizons resolves the 'id' <https://ssd.jpl.nasa.gov/horizons/manual.html#select>`_
to match a Solar System body:

+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``id_type``        | Query behavior                                                                                                                           |
+====================+==========================================================================================================================================+
| ``None`` (default) | Searches major bodies (planets, natural satellites, spacecraft, special cases) first, and if none are found, then searches small bodies. |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``smallbody``      | Limits the search to small solar system bodies (comets and asteroids).                                                                   |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``designation``    | Limits the search to small body designations, e.g., 73P or 2014 MU69.                                                                    |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``name``           | Limits the search to asteroid or comet names, e.g., Halley will match 1P/Halley and (2688) Halley.                                       |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``asteroid_name``  | Limits the search to asteroid names, e.g., Don Quixote.                                                                                  |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+
| ``comet_name``     | Limits the search to comet names, e.g., Encke will only match comet 2P/Encke, and not (9134) Encke.                                      |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------+

In the case of ambiguities in the name resolution, a list of matching objects
will be provided. In order to select an object from this list, provide the
respective id number or record number as ``id`` and use ``id_type=None``:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> print(Horizons(id='Encke').ephemerides())
   ...
   ValueError: Ambiguous target name; provide unique id:
       Record #  Epoch-yr  Primary Desig  >MATCH NAME<
       --------  --------  -------------  -------------------------
           9134            4822 P-L        Encke
       90000034    1786    2P              Encke
       90000035    1796    2P              Encke
       90000036    1805    2P              Encke
	    ...     ...    ...               ...
   >>> print(Horizons(id='90000034', id_type=None).ephemerides())
   targetname       datetime_str          datetime_jd    ... RA_3sigma DEC_3sigma
      ---               ---                    d         ...   arcsec    arcsec
   ---------- ------------------------ ----------------- ... --------- ----------
     2P/Encke 2018-Jan-17 05:06:07.709 2458135.712589224 ...        --         --



The `JPL Horizons`_ system provides ephemerides, orbital elements, and state
vectors for almost all known Solar System bodies. These queries are provided
through three functions:
:meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides`,
:meth:`~astroquery.jplhorizons.HorizonsClass.elements`, and
:meth:`~astroquery.jplhorizons.HorizonsClass.vectors`.

Ephemerides
-----------

:meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides` returns ephemerides
for a given observer location (``location``) and epoch or range of epochs
(``epochs``) in the form of an astropy table. The following example queries the
ephemerides of asteroid (1) Ceres for a range of dates as seen from Mauna Kea:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='Ceres', location='568',
   ...		      epochs={'start':'2010-01-01', 'stop':'2010-03-01',
   ...                        'step':'10d'})
   >>> eph = obj.ephemerides()
   >>> print(eph)
   targetname    datetime_str   datetime_jd ...   GlxLat  RA_3sigma DEC_3sigma
      ---            ---             d      ...    deg      arcsec    arcsec
   ---------- ----------------- ----------- ... --------- --------- ----------
      1 Ceres 2010-Jan-01 00:00   2455197.5 ... 24.120057       0.0        0.0
      1 Ceres 2010-Jan-11 00:00   2455207.5 ... 20.621496       0.0        0.0
      1 Ceres 2010-Jan-21 00:00   2455217.5 ... 17.229529       0.0        0.0
      1 Ceres 2010-Jan-31 00:00   2455227.5 ...  13.97264       0.0        0.0
      1 Ceres 2010-Feb-10 00:00   2455237.5 ... 10.877201       0.0        0.0
      1 Ceres 2010-Feb-20 00:00   2455247.5 ...  7.976737       0.0        0.0


The following fields are available for each ephemerides query:

.. code-block:: python

   >>> print(eph.columns)
   <TableColumns names=('targetname','datetime_str','datetime_jd','H','G','solar_presence','flags','RA','DEC','RA_app','DEC_app','RA_rate','DEC_rate','AZ','EL','AZ_rate','EL_rate','sat_X','sat_Y','sat_PANG','siderealtime','airmass','magextinct','V','surfbright','illumination','illum_defect','sat_sep','sat_vis','ang_width','PDObsLon','PDObsLat','PDSunLon','PDSunLat','SubSol_ang','SubSol_dist','NPole_ang','NPole_dist','EclLon','EclLat','r','r_rate','delta','delta_rate','lighttime','vel_sun','vel_obs','elong','elongFlag','alpha','lunar_elong','lunar_illum','sat_alpha','sunTargetPA','velocityPA','OrbPlaneAng','constellation','TDB-UT','ObsEclLon','ObsEclLat','NPole_RA','NPole_DEC','GlxLon','GlxLat','solartime','earth_lighttime','RA_3sigma','DEC_3sigma','SMAA_3sigma','SMIA_3sigma','Theta_3sigma','Area_3sigma','RSS_3sigma','r_3sigma','r_rate_3sigma','SBand_3sigma','XBand_3sigma','DoppDelay_3sigma','true_anom','hour_angle','alpha_true','PABLon','PABLat')>

The values in these columns are the same as those defined in the Horizons
`Definition of Observer Table Quantities`_; names have been simplified in a few
cases. Quantities ``H`` and ``G`` are the target's Solar System absolute
magnitude and photometric phase curve slope, respectively. In the case of
comets, ``H`` and ``G`` are replaced by ``M1``, ``M2``, ``k1``, ``k2``, and
``phasecoeff``; please refer to the `Horizons documentation`_ for definitions.

Optional parameters of :meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides`
correspond to optional features of the Horizons system: ``airmass_lessthan``
sets an upper limit to airmass, ``solar_elongation`` enables the definition of a
solar elongation range, ``max_hour_angle`` sets a cutoff of the hour angle,
``skip_daylight=True`` rejects epochs during daylight, ``rate_cutoff`` rejects
targets with sky motion rates higher than provided (in units of arcsec/h),
``refraction`` accounts for refraction in the computation of the ephemerides
(disabled by default), and ``refsystem`` defines the coordinate reference system
used (ICRF by default). For comets, the options ``closest_apparition`` and
``no_fragments`` are available, which selects the closest apparition in time and
limits fragment matching (73P-B would only match 73P-B), respectively.  Note
that these options should only be used for comets and will crash the query for
other object types. Extra precision in the queried properties can be requested
using the ``extra_precision`` option.  Furthermore, ``get_query_payload=True``
skips the query and only returns the query payload, whereas
``get_raw_response=True`` returns the raw query response instead of the astropy
table.

:meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides` queries by default all
available quantities from the JPL Horizons servers. This might take a while. If
you are only interested in a subset of the available quantities, you can query
only those. The corresponding optional parameter to be set is ``quantities``.
This parameter uses the same numerical codes as JPL Horizons defined in the `JPL
Horizons User Manual Definition of Observer Table Quantities
<https://ssd.jpl.nasa.gov/horizons/manual.html#observer-table>`_. For instance,
if you only want to query astrometric RA and Dec, you can use ``quantities=1``;
if you only want the heliocentric and geocentric distances, you can use
``quantities='19,20'`` (note that in this case a string with comma-separated
codes has to be provided).


Orbital elements
----------------

:meth:`~astroquery.jplhorizons.HorizonsClass.elements` returns orbital elements
relative to some Solar System body (``location``, referred to as "CENTER" in
Horizons) and for a given epoch or a range of epochs (``epochs``) in the form of
an astropy table. The following example queries the osculating elements of
asteroid (433) Eros for a given date relative to the Sun:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='433', location='500@10',
   ...                epochs=2458133.33546)
   >>> el = obj.elements()
   >>> print(el)
       targetname      datetime_jd  ...       Q            P
          ---               d       ...       AU           d
   ------------------ ------------- ... ------------- ------------
   433 Eros (A898 PA) 2458133.33546 ... 1.78244263804 642.93873484


The following fields are queried:

.. code-block:: python

   >>> print(el.columns)
   <TableColumns names=('targetname','datetime_jd','datetime_str','H','G','e','q','incl','Omega','w','Tp_jd','n','M','nu','a','Q','P')>

Optional parameters of :meth:`~astroquery.jplhorizons.HorizonsClass.elements`
include ``refsystem``, which defines the coordinate reference system used (ICRF
by default), ``refplane`` which defines the reference plane of the orbital
elements queried, and ``tp_type``, which switches between a relative and
absolute representation of the time of perihelion passage.  For comets, the
options ``closest_apparition`` and ``no_fragments`` are available, which select
the closest apparition in time and reject fragments, respectively. Note that
these options should only be used for comets and will crash the query for other
object types. Also available are ``get_query_payload=True``, which skips the
query and only returns the query payload, and ``get_raw_response=True``, which
returns the raw query response instead of the astropy table.

Vectors
-------

:meth:`~astroquery.jplhorizons.HorizonsClass.vectors` returns the
state vector of the target body in cartesian coordinates relative to
some Solar System body (``location``, referred to as "CENTER" in
Horizons) and for a given epoch or a range of epochs (``epochs``) in
the form of an astropy table. The following example queries the state
vector of asteroid 2012 TC4 as seen from Goldstone for a range of
epochs:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='2012 TC4', location='257',
   ...                epochs={'start':'2017-10-01', 'stop':'2017-10-02',
   ...                        'step':'10m'})
   >>> vec = obj.vectors()
   >>> print(vec)
   targetname  datetime_jd  ...      range          range_rate
       ---           d       ...        AU             AU / d
   ---------- ------------- ... --------------- -----------------
   (2012 TC4)     2458027.5 ... 0.0429332099306 -0.00408018711862
   (2012 TC4) 2458027.50694 ... 0.0429048742906 -0.00408040726527
   (2012 TC4) 2458027.51389 ... 0.0428765385796 -0.00408020747595
   (2012 TC4) 2458027.52083 ... 0.0428482057142  -0.0040795878561
   (2012 TC4) 2458027.52778 ...  0.042819878607 -0.00407854931543
   (2012 TC4) 2458027.53472 ... 0.0427915601617  -0.0040770935665
          ...           ... ...             ...               ...
   (2012 TC4) 2458028.45833 ... 0.0392489462501 -0.00405496595173
   (2012 TC4) 2458028.46528 ...   0.03922077771 -0.00405750632914
   (2012 TC4) 2458028.47222 ...  0.039192592935 -0.00405964084539
   (2012 TC4) 2458028.47917 ...  0.039164394759 -0.00406136516755
   (2012 TC4) 2458028.48611 ... 0.0391361860433 -0.00406267574646
   (2012 TC4) 2458028.49306 ... 0.0391079696711  -0.0040635698239
   (2012 TC4)     2458028.5 ... 0.0390797485422 -0.00406404543822
   Length = 145 rows

The following fields are queried:

   >>> print(vec.columns)
   <TableColumns names=('targetname','datetime_jd','datetime_str','H','G','x','y','z','vx','vy','vz','lighttime','range','range_rate')>


Similar to the other :class:`~astroquery.jplhorizons.HorizonsClass` functions,
optional parameters of :meth:`~astroquery.jplhorizons.HorizonsClass.vectors` are
``get_query_payload=True``, which skips the query and only returns the query
payload, and ``get_raw_response=True``, which returns the raw query response
instead of the astropy table. For comets, the options ``closest_apparation`` and
``no_fragments`` are available, which select the closest apparition in time and
reject fragments, respectively. Note that these options should only be used for
comets and will crash the query for other object types. Options ``aberrations``
and ``delta_T`` provide different choices for aberration corrections as well as
a measure for time-varying differences between TDB and UT time-scales,
respectively.


How to Use the Query Tables
===========================

`astropy table`_ objects created by the query functions are extremely versatile
and easy to use. Since all query functions return the same type of table, they
can all be used in the same way.

We provide some examples to illustrate how to use them based on the following
JPL Horizons ephemerides query of near-Earth asteroid (3552) Don Quixote since
its year of Discovery:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='3552', location='568',
   ...                epochs={'start':'2010-01-01', 'stop':'2019-12-31',
   ...                        'step':'1y'})
   >>> eph = obj.ephemerides()

As we have seen before, we can display a truncated version of table
``eph`` by simply using

.. code-block:: python

   >>> print(eph)
           targetname            datetime_str   ...  PABLon   PABLat
              ---                    ---        ...   deg      deg
   -------------------------- ----------------- ... -------- --------
   3552 Don Quixote (1983 SA) 2010-Jan-01 00:00 ...   8.0371  18.9349
   3552 Don Quixote (1983 SA) 2011-Jan-01 00:00 ...  85.4082  34.5611
   3552 Don Quixote (1983 SA) 2012-Jan-01 00:00 ... 109.2959  30.3834
   3552 Don Quixote (1983 SA) 2013-Jan-01 00:00 ... 123.0777   26.136
   3552 Don Quixote (1983 SA) 2014-Jan-01 00:00 ... 133.9392  21.8962
   3552 Don Quixote (1983 SA) 2015-Jan-01 00:00 ... 144.2701  17.1908
   3552 Don Quixote (1983 SA) 2016-Jan-01 00:00 ... 156.1007  11.1447
   3552 Don Quixote (1983 SA) 2017-Jan-01 00:00 ... 174.0245   1.3487
   3552 Don Quixote (1983 SA) 2018-Jan-01 00:00 ... 228.9956 -21.6723
   3552 Don Quixote (1983 SA) 2019-Jan-01 00:00 ...  45.1979  32.3885


Please note the formatting of this table, which is done automatically. Above the
dashes in the first two lines, you have the column name and its unit. Every
column is assigned a unit from `astropy units`_. We will learn later how to use
these units.


Columns
-------

We can get at list of all the columns in this table with:

.. code-block:: python

   >>> print(eph.columns)
   <TableColumns names=('targetname','datetime_str','datetime_jd','H','G','solar_presence','flags','RA','DEC','RA_app','DEC_app','RA_rate','DEC_rate','AZ','EL','AZ_rate','EL_rate','sat_X','sat_Y','sat_PANG','siderealtime','airmass','magextinct','V','surfbright','illumination','illum_defect','sat_sep','sat_vis','ang_width','PDObsLon','PDObsLat','PDSunLon','PDSunLat','SubSol_ang','SubSol_dist','NPole_ang','NPole_dist','EclLon','EclLat','r','r_rate','delta','delta_rate','lighttime','vel_sun','vel_obs','elong','elongFlag','alpha','lunar_elong','lunar_illum','sat_alpha','sunTargetPA','velocityPA','OrbPlaneAng','constellation','TDB-UT','ObsEclLon','ObsEclLat','NPole_RA','NPole_DEC','GlxLon','GlxLat','solartime','earth_lighttime','RA_3sigma','DEC_3sigma','SMAA_3sigma','SMIA_3sigma','Theta_3sigma','Area_3sigma','RSS_3sigma','r_3sigma','r_rate_3sigma','SBand_3sigma','XBand_3sigma','DoppDelay_3sigma','true_anom','hour_angle','alpha_true','PABLon','PABLat')>

We can address each column individually by indexing it using its name as
provided in this list. For instance, we can get all RAs for Don Quixote by using

.. code-block:: python

   >>> print(eph['RA'])
       RA
      deg
   ---------
   345.50204
    78.77158
   119.85659
   136.60021
   147.44947
   156.58967
   166.32129
    180.6992
   232.11974
     16.1066


This column is formatted like the entire table; it has a column name and a unit.
We can select several columns at a time, for instance RA and DEC for each epoch

.. code-block:: python

   >>> print(eph['datetime_str', 'RA', 'DEC'])
      datetime_str       RA      DEC
          ---           deg      deg
   ----------------- --------- --------
   2010-Jan-01 00:00 345.50204 13.43621
   2011-Jan-01 00:00  78.77158 61.48831
   2012-Jan-01 00:00 119.85659 54.21955
   2013-Jan-01 00:00 136.60021 45.82409
   2014-Jan-01 00:00 147.44947 37.79876
   2015-Jan-01 00:00 156.58967 29.23058
   2016-Jan-01 00:00 166.32129 18.48174
   2017-Jan-01 00:00  180.6992  1.20453
   2018-Jan-01 00:00 232.11974 -37.9554
   2019-Jan-01 00:00   16.1066 45.50296


We can use the same representation to do math with these columns. For instance,
let's calculate the total rate of the object by summing 'RA_rate' and 'DEC_rate'
in quadrature:

.. code-block:: python

   >>> import numpy as np
   >>> print(np.sqrt(eph['RA_rate']**2 + eph['DEC_rate']**2))
        dRA*cosD
   ------------------
    86.18728612153883
   26.337249029653798
   21.520859656742434
   17.679843758686584
   14.775809055378625
   11.874886005626538
    7.183281978025435
    7.295600209387093
    94.84824546372009
   23.952470898018017


Please note that the column name is wrong (copied from the name of the first
column used), and that the unit is lost.

Units
-----

Columns have units assigned to them. For instance, the ``RA`` column has
the unit ``deg`` assigned to it, i.e., degrees. More complex units are
available, too, e.g., the ``RA_rate`` column is expressed in ``arcsec /
h`` - arcseconds per hour:

.. code-block:: python

   >>> print(eph['RA_rate'])
    RA_rate
   arcsec / h
   ----------
     72.35438
     -23.8239
     -20.7151
     -15.5509
      -12.107
     -9.32616
     -5.80004
     3.115853
     85.22719
     19.02548


The unit of this column can be easily converted to any other unit describing the
same dimensions. For instance, we can turn ``RA_rate`` into ``arcsec / s``:

.. code-block:: python

   >>> eph['RA_rate'].convert_unit_to('arcsec/s')
   >>> print(eph['RA_rate'])
          RA_rate
         arcsec / s
   ----------------------
      0.02009843888888889
   -0.0066177499999999995
    -0.005754194444444445
    -0.004319694444444445
   -0.0033630555555555553
   -0.0025905999999999998
   -0.0016111222222222222
    0.0008655147222222222
     0.023674219444444443
     0.005284855555555556


Please refer to the `astropy table`_ and `astropy units`_ documentations for
more information.

Hints and Tricks
================

Checking the original JPL Horizons output
-----------------------------------------

Once either of the query methods has been called, the retrieved raw response is
stored in the attribute ``raw_response``. Inspecting this response can help to
understand issues with your query, or you can process the results differently.

For all query types, the query URI (the URI is what you would put into the URL
field of your web browser) that is used to request the data from the JPL
Horizons server can be obtained from the
:class:`~astroquery.jplhorizons.HorizonsClass` object after a query has been
performed (before the query only ``None`` would be returned):

   >>> print(obj.uri)
   https://ssd.jpl.nasa.gov/api/horizons.api?format=text&EPHEM_TYPE=OBSERVER&QUANTITIES=%271%2C2%2C3%2C4%2C5%2C6%2C7%2C8%2C9%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2C40%2C41%2C42%2C43%27&COMMAND=%223552%22&SOLAR_ELONG=%220%2C180%22&LHA_CUTOFF=0&CSV_FORMAT=YES&CAL_FORMAT=BOTH&ANG_FORMAT=DEG&APPARENT=AIRLESS&REF_SYSTEM=ICRF&EXTRA_PREC=NO&CENTER=%27568%27&START_TIME=%222010-01-01%22&STOP_TIME=%222019-12-31%22&STEP_SIZE=%221y%22&SKIP_DAYLT=NO

If your query failed, it might be useful for you to put the URI into a web
browser to get more information why it failed. Please note that ``uri`` is an
attribute of :class:`~astroquery.jplhorizons.HorizonsClass` and not the results
table.

Date Formats
------------

JPL Horizons puts somewhat strict guidelines on the date formats: individual
epochs have to be provided as Julian dates, whereas epoch ranges have to be
provided as ISO dates (YYYY-MM-DD HH-MM UT). If you have your epoch dates in one
of these formats but you need the other format, make use of
:class:`astropy.time.Time` for the conversion. An example is provided here:

.. doctest-requires:: astropy

    >>> from astropy.time import Time
    >>> mydate_fromiso = Time('2018-07-23 15:55:23')  # pass date as string
    >>> print(mydate_fromiso.jd)  # convert Time object to Julian date
    2458323.163460648
    >>> mydate_fromjd = Time(2458323.163460648, format='jd')
    >>> print(mydate_fromjd.iso) # convert Time object to ISO
    2018-07-23 15:55:23.000

:class:`astropy.time.Time` allows you to convert dates across a wide range of
formats. Please note that when reading in Julian dates, you have to specify the
date format as ``'jd'``, as number passed to :class:`~astropy.time.Time` is
ambiguous.

Keep Queries Short
------------------

Keep in mind that queries are sent as URIs to the Horizons server. If
you query a large number of epochs (in the form of a list), this list
might be truncated as URIs are typically expected to be shorter than
2,000 symbols and your results might be compromised. If your query URI
is longer than this limit, a warning is given. In that case, please
try using a range of dates instead of a list of individual dates.

.. _jpl-horizons-reference-frames:

Reference Frames
----------------

The coordinate reference frame for Horizons output is controlled by the
``refplane`` and ``refsystem`` keyword arguments.  See the `Horizons
documentation`_ for details. Some output reference frames are included in
astropy's `~astropy.coordinates`:

+----------------+--------------+----------------+----------------+---------------------------------+
| Method         | ``location`` | ``refplane``   | ``refsystem``  | astropy frame                   |
+================+==============+================+================+=================================+
| ``.vectors()`` | ``'@0'``     | ``'ecliptic'`` | N/A            | ``'custombarycentricecliptic'`` |
+----------------+--------------+----------------+----------------+---------------------------------+
| ``.vectors()`` | ``'@0'``     | ``'earth'``    | N/A            | ``'icrs'``                      |
+----------------+--------------+----------------+----------------+---------------------------------+
| ``.vectors()`` | ``'@10'``    | ``'ecliptic'`` | N/A            | ``'heliocentriceclipticiau76'`` |
+----------------+--------------+----------------+----------------+---------------------------------+

For example, get the barycentric coordinates of Jupiter as an astropy
`~astropy.coordinates.SkyCoord` object:

.. code-block:: python

   >>> from astropy.coordinates import SkyCoord
   >>> from astropy.time import Time
   >>> from astroquery.jplhorizons import Horizons
   >>> epoch = Time('2021-01-01')
   >>> q = Horizons('599', location='@0', epochs=epoch.tdb.jd)
   >>> tab = q.vectors(refplane='earth')
   >>> c = SkyCoord(tab['x'].quantity, tab['y'].quantity, tab['z'].quantity,
   ...              representation_type='cartesian', frame='icrs',
   ...              obstime=epoch)
   >>> print(c)
   <SkyCoord (ICRS): (x, y, z) in AU
       [(3.03483263, -3.72503309, -1.67054586)]>




Acknowledgements
================

This submodule makes use of the `JPL Horizons
<https://ssd.jpl.nasa.gov/horizons/>`_ system.

The development of this submodule is in part funded through NASA PDART Grant No.
80NSSC18K0987 to the `sbpy project <http://sbpy.org>`_.


Reference/API
=============

.. automodapi:: astroquery.jplhorizons
    :no-inheritance-diagram:

.. _Solar System Dynamics group at the Jet Propulation Laboratory: http://ssd.jpl.nasa.gov/
.. _MPC Observatory codes: http://minorplanetcenter.net/iau/lists/ObsCodesF.html
.. _astropy table: http://docs.astropy.org/en/stable/table/index.html
.. _astropy units: http://docs.astropy.org/en/stable/units/index.html
.. _Definition of Observer Table Quantities: https://ssd.jpl.nasa.gov/horizons/manual.html#observer-table
.. _Horizons documentation: https://ssd.jpl.nasa.gov/horizons/manual.html#observer-table
