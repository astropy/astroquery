.. doctest-skip-all

.. _astroquery.jplhorizons:

***********************************************************************************
JPL Horizons Queries (`astroquery.jplhorizons`/astroquery.solarsystem.jpl.horizons)
***********************************************************************************

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
   JPLHorizons instance "Ceres"; location=568, epochs=[2458133.33546], id_type=smallbody

``id`` refers to the target identifier and is mandatory; the exact
string will be used in the query to the Horizons system.

``location`` means either the observer's location (e.g., Horizons
ephemerides query) or the body relative to which orbital elements are
provided (e.g., Horizons orbital elements or vectors query); the same
codes as used by Horizons are used here, which includes `MPC
Observatory codes`_. The default is ``location=None``, which uses a
geocentric location for ephemerides queries and the Sun as central body
for orbital elements and state vector queries. User-defined
topocentric locations for ephemerides queries can be provided, too, in
the form of a dictionary. The dictionary has to be formatted as
follows: {``'lon'``: longitude in degrees (East positive, West
negative), ``'lat'``: latitude in degrees (North positive, South
negative), ``'elevation'``: elevation in km above the reference
ellipsoid}. In addition, ``'body'`` can be set to the Horizons body ID
of the central body if different from Earth; by default, it is
assumed that this location is on Earth if it has not been specifically
set. The following example uses the coordinates of the `Statue of
Liberty
<https://www.google.com/maps/place/Statue+of+Liberty+National+Monument/@40.6892534,-74.0466891,17z/data=!3m1!4b1!4m5!3m4!1s0x89c25090129c363d:0x40c6a5770d25022b!8m2!3d40.6892494!4d-74.0445004>`_
as the observer's location:

    >>> statue_of_liberty = {'lon': -74.0466891,
    ...                      'lat': 40.6892534,
    ...                      'elevation': 0.093}
    >>> obj = Horizons(id='Ceres',
    ...                location=statue_of_liberty,
    ...                epochs=2458133.33546)
    JPLHorizons instance "Ceres"; location={'lon': -74.0466891, 'lat': 40.6892534, 'elevation': 0.093}, epochs=[2458133.33546], id_type=smallbody



``epochs`` is either a scalar or list of Julian Dates (floats or
strings) in the case of discrete epochs, or, in
the case of a range of
epochs, a dictionary that has to include the keywords ``start``,
``stop`` (both using the following format "YYYY-MM-DD [HH:MM:SS]"),
and ``step`` (e.g., ``'1m'`` for one minute, ``'3h'``three hours,
``'10d'`` for ten days). Note that all input epochs, both calendar
dates/times and Julian Dates, refer to UTC for ephemerides queries, TDB for
element queries, and CT for vector queries. By default,
``epochs=None``, which uses the current date and time.

``id_type`` describes what type of target identifier has been provided
in order to minimize the risk of confusion when identifying the
target: ``smallbody`` (default; refers to an asteroid or comet),
``majorbody`` (planets or satellites), ``designation`` (any type of
asteroid or comet designation), ``name`` (any type of target name),
``asteroid_name`` (name of an asteroid), or ``comet_name`` (name of a
comet). In order to minimize confusion, try to be as specific as
possible; namely, in the case of comets, make use of ``comet_name``
(e.g., "Halley") and ``designation`` (e.g., "73P"). In the case of
ambiguities in the name resolving, a list of matching objects will be
provided. In order to select an object from this list, provide the
respective id number or record number as ``id`` and use ``id_type=id``:

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
   >>> print(Horizons(id='90000034', id_type='id').ephemerides())
   targetname       datetime_str          datetime_jd    ... RA_3sigma DEC_3sigma
      ---               ---                    d         ...   arcsec    arcsec
   ---------- ------------------------ ----------------- ... --------- ----------
     2P/Encke 2018-Jan-17 05:06:07.709 2458135.712589224 ...        --         --


Querying JPL Horizons
---------------------

The `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`_ system provides ephemerides, orbital elements, and
state vectors for almost all known Solar System bodies. These queries
are provided through three functions:

:meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides` returns
ephemerides for a given observer location (``location``) and epoch or
range of epochs (``epochs``) in the form of an astropy table. The
following example queries the ephemerides of asteroid (1) Ceres for
a range of dates as seen from Maunakea:

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
   <TableColumns names=('targetname','datetime_str','datetime_jd','H','G','solar_presence','flags','RA','DEC','RA_rate','DEC_rate','AZ','EL','airmass','magextinct','V','surfbright','illumination','EclLon','EclLat','r','r_rate','delta','delta_rate','lighttime','elong','elongFlag','alpha','sunTargetPA','velocityPA','ObsEclLon','ObsEclLat','GlxLon','GlxLat','RA_3sigma','DEC_3sigma')>

The values in these columns are the same as those defined in the
Horizons `Definition of Observer Table Quantities`_; names have been
simplified in a few cases. Quantities ``H`` and ``G`` are the target's
Solar System absolute magnitude and photometric phase curve slope,
respectively. In the case of comets, ``H`` and ``G`` are replaced by ``M1``,
``M2``, ``k1``, ``k2``, and ``phasecoeff``; please refer to the `Horizons
documentation`_ for definitions.

Optional parameters of
:meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides` are
corresponding to optional features of the Horizons system:
``airmass_lessthan`` sets an upper limit to airmass,
``solar_elongation`` enables the definition of a solar elongation
range, ``max_hour_angle`` sets a cutoff of the hour angle,
``skip_daylight=True`` reject epochs during daylight, ``rate_cutoff``
allows to reject targets with sky motion rates higher than provided
(in units of arcsec/h), ``refraction`` accounts for refraction in the
computation of the ephemerides (disabled by default), and
``refsystem`` defines the coordinate reference system used (J2000 by
default).. For comets, the options ``closest_apparation`` and
``no_fragments`` are available, which select the closest apparition in
time and reject fragments, respectively. Note that these options
should only be used for comets and will crash the query for other
object types. Extra precision in the queried properties can be
requested using the ``extra_precision`` option. Furthermore,
``get_query_payload=True`` skips the query and only returns the query
payload, whereas ``get_raw_response=True`` the raw query response
instead of the astropy table returns.

:meth:`~astroquery.jplhorizons.HorizonsClass.ephemerides` queries by
default all available quantities from the JPL Horizons servers. This
might take a while. If you are only interested in a subset of the
available quantities, you can query only those. The corresponding
optional parameter to be set is ``quantities``. This parameter uses
the same numerical codes as JPL Horizons defined in the `JPL Horizons
User Manual Definition of Observer Table Quantities
<https://ssd.jpl.nasa.gov/?horizons_doc#table_quantities>`_. For
instance, if you only want to query astrometric RA and Dec, you can
use ``quantities=1``; if you only want the heliocentric and geocentric
distances, you can use ``quantities='19,20'`` (note that in this case
a string with comma-separated codes has to be provided).



:meth:`~astroquery.jplhorizons.HorizonsClass.elements` returns orbital
elements relative to some Solar System body (``location``, referred to as
"CENTER" in Horizons) and for a given epoch or a range of epochs
(``epochs``) in the form of an astropy table. The following example
queries the osculating elements of asteroid (433) Eros for a given
data relative to the Sun:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='433', location='500@10',
   ...		      epochs=2458133.33546)
   >>> el = obj.elements()
   >>> print(el)
       targetname      datetime_jd  ...       Q            P
          ---               d       ...       AU           d
   ------------------ ------------- ... ------------- ------------
   433 Eros (1898 DQ) 2458133.33546 ... 1.78244263804 642.93873484


The following fields are queried:

.. code-block:: python

   >>> print(el.columns)
   <TableColumns names=('targetname','datetime_jd','datetime_str','H','G','e','q','incl','Omega','w','Tp_jd','n','M','nu','a','Q','P')>

Optional parameters of
:meth:`~astroquery.jplhorizons.HorizonsClass.elements` include
``refsystem``, which defines the coordinate reference system used
(J2000 by default), ``refplane`` which defines the reference plane of
the orbital elements queried, and ``tp_type``, which switches between
a relative and absolute representation of the time of perihelion
passage.  For comets, the options ``closest_apparation`` and
``no_fragments`` are available, which select the closest apparition in
time and reject fragments, respectively. Note that these options
should only be used for comets and will crash the query for other
object types. Furthermore,``get_query_payload=True``, which skips the
query and only returns the query payload, and
``get_raw_response=True``, which returns the raw query response
instead of the astropy table, are available.

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


Similar to the other :class:`~astroquery.jplhorizons.HorizonsClass`
functions, optional parameters of
:meth:`~astroquery.jplhorizons.HorizonsClass.vectors` are
``get_query_payload=True``, which skips the query and only returns the
query payload, and ``get_raw_response=True``, which returns the raw
query response instead of the astropy table. For comets, the options
``closest_apparation`` and ``no_fragments`` are available, which
select the closest apparition in time and reject fragments,
respectively. Note that these options should only be used for comets
and will crash the query for other object types. Options
``aberrations`` and ``delta_T`` provide different choices for
aberration corrections as well as a measure for time-varying
differences between TDB and UT time-scales, respectively.


How to Use the Query Tables
===========================

`astropy table`_ created by the query functions are extremely
versatile and easy to use. Since all query functions return the same
type of table, they can all be used in the same way.

We provide some examples to illustrate how to use them based on the
following JPL Horizons ephemerides query of near-Earth asteroid (3552)
Don Quixote since its year of Discovery:

.. code-block:: python

   >>> from astroquery.jplhorizons import Horizons
   >>> obj = Horizons(id='3552', location='568',
   ...		      epochs={'start':'2010-01-01', 'stop':'2019-12-31',
   ...                        'step':'1y'})
   >>> eph = obj.ephemerides()

As we have seen before, we can display a truncated version of table
``eph`` by simply using

.. code-block:: python

   >>> print(eph)
           targetname            datetime_str   ... RA_3sigma DEC_3sigma
              ---                    ---        ...   arcsec    arcsec
   -------------------------- ----------------- ... --------- ----------
   3552 Don Quixote (1983 SA) 1983-Jan-01 00:00 ...     0.159      0.141
   3552 Don Quixote (1983 SA) 1984-Jan-01 00:00 ...     0.187      0.231
   3552 Don Quixote (1983 SA) 1985-Jan-01 00:00 ...     0.138      0.147
   3552 Don Quixote (1983 SA) 1986-Jan-01 00:00 ...     0.117      0.123
   3552 Don Quixote (1983 SA) 1987-Jan-01 00:00 ...     0.106      0.104
   3552 Don Quixote (1983 SA) 1988-Jan-01 00:00 ...     0.095      0.089
                          ...               ... ...       ...        ...
   3552 Don Quixote (1983 SA) 2013-Jan-01 00:00 ...     0.106      0.107
   3552 Don Quixote (1983 SA) 2014-Jan-01 00:00 ...     0.095      0.092
   3552 Don Quixote (1983 SA) 2015-Jan-01 00:00 ...     0.083      0.079
   3552 Don Quixote (1983 SA) 2016-Jan-01 00:00 ...      0.07      0.067
   3552 Don Quixote (1983 SA) 2017-Jan-01 00:00 ...     0.061      0.062
   3552 Don Quixote (1983 SA) 2018-Jan-01 00:00 ...     0.126      0.089
   3552 Don Quixote (1983 SA) 2019-Jan-01 00:00 ...     0.174      0.174
   Length = 37 rows


Please note the formatting of this table, which is done
automatically. Above the dashes in the first two lines, you have the
column name and its unit. Every column is assigned a unit from
`astropy units`_. We will learn later how to use these units.


Columns
-------

We can get at list of all the columns in this table with

.. code-block:: python

   >>> print(eph.columns)
   <TableColumns names=('targetname','datetime_str','datetime_jd','H','G','solar_presence','flags','RA','DEC','RA_rate','DEC_rate','AZ','EL','airmass','magextinct','V','surfbright','illumination','EclLon','EclLat','r','r_rate','delta','delta_rate','lighttime','elong','elongFlag','alpha','sunTargetPA','velocityPA','ObsEclLon','ObsEclLat','GlxLon','GlxLat','RA_3sigma','DEC_3sigma')>


We can address each column individually by indexing it using its name
as provided in this list. For instance, we can get all RAs for Don
Quixote by using


.. code-block:: python

   >>> print(eph['RA'])

      RA
      deg
   ---------
   209.43762
   357.85696
    86.22996
   122.10393
   137.91137
   148.42444
         ...
   136.60019
   147.44945
   156.58965
   166.32128
   180.69918
   232.11974
    16.10662
   Length = 37 rows


This column is formatted like the entire table; it has a column name
and a unit. We can select several columns at a time, for instance RA
and DEC for each epoch

.. code-block:: python

   >>> print(eph['datetime_str', 'RA', 'DEC'])
      datetime_str       RA       DEC
          ---           deg       deg
   ----------------- --------- ---------
   1983-Jan-01 00:00 209.43762 -25.92118
   1984-Jan-01 00:00 357.85696  28.74791
   1985-Jan-01 00:00  86.22996  60.90524
   1986-Jan-01 00:00 122.10393  53.19306
   1987-Jan-01 00:00 137.91137  44.95184
   1988-Jan-01 00:00 148.42444  37.01774
                 ...       ...       ...
   2013-Jan-01 00:00 136.60019  45.82408
   2014-Jan-01 00:00 147.44945  37.79874
   2015-Jan-01 00:00 156.58965  29.23058
   2016-Jan-01 00:00 166.32128  18.48173
   2017-Jan-01 00:00 180.69918   1.20453
   2018-Jan-01 00:00 232.11974 -37.95539
   2019-Jan-01 00:00  16.10662  45.50296
   Length = 37 rows


We can use the same representation to do math with these columns. For
instance, let's calculate the total rate of the object by calculating
the geometric mean of 'RA_rate' and 'DEC_rate':

.. code-block:: python

   >>> import numpy as np
   >>> print(np.sqrt(eph['RA_rate']**2 + eph['DEC_rate']**2))
      dRA*cosD
   ------------------
   58.69696313151559
   51.59679292260421
   25.793090188451636
   20.994411962530627
   17.258738465267385
   14.376579229218054
   11.73881436960752
                  ...
   17.679841379965037
   14.775806762375074
   11.874884148540735
    7.183280208160058
    7.2955985010416375
   94.84821056509183
   23.952455011994072

Please note that the column is wrong (it uses the title of the first
column used), and that there is no unit (this will be fixed with the
use of astropy QTables in the future).

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
     44.35495
     49.20015
     -24.5561
     -20.0651
     -15.0293
     -11.6761
          ...
     -15.5509
      -12.107
     -9.32616
     -5.80004
     3.115849
      85.2272
     19.02546
   Length = 37 rows


The unit of this column can be easily converted to any other unit
describing the same dimensions. For instance, we can turn ``RA_rate``
into ``arcsec / s``:

.. code-block:: python

   >>> eph['RA_rate'].convert_unit_to('arcsec/s')
   >>> print(eph['RA_rate'])
          RA_rate
         arcsec / s
   ----------------------
     0.012320819444444445
     0.013666708333333333
    -0.006821138888888889
    -0.005573638888888889
    -0.004174805555555556
    -0.003243361111111111
                      ...
    -0.004319694444444445
   -0.0033630555555555553
   -0.0025905999999999998
   -0.0016111222222222222
    0.0008655136111111111
      0.02367422222222222
               0.00528485
   Length = 37 rows


Please refer to the `astropy table`_ and `astropy units`_
documentations for more information.

Hints and Tricks
================

Checking the original JPL Horizons output
-----------------------------------------

Once either of the query methods has been called, the retrieved raw response is
stored in the attribute ``raw_response``. Inspecting this response can help
to understand issues with your query, or you can process the results
differently.

For all query types, the query URI (the URI is what you would put into
the URL field of your web browser) that is used to request the data
from the JPL Horizons server can be obtained from the
:class:`~astroquery.jplhorizons.HorizonsClass` object after a query
has been performed (before the query only ``None`` would be returned):

   >>> print(obj.uri)
   https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1&TABLE_TYPE=VECTORS&OUT_UNITS=AU-D&COMMAND=%222012+TC4%3B%22&CENTER=%27257%27&CSV_FORMAT=%22YES%22&REF_PLANE=ECLIPTIC&REF_SYSTEM=J2000&TP_TYPE=ABSOLUTE&LABELS=YES&OBJ_DATA=YES&START_TIME=2017-10-01&STOP_TIME=2017-10-02&STEP_SIZE=10m

If your query failed, it might be useful for you to put the URI into a
web browser to get more information why it failed. Please note that
``uri`` is an attribute of
:class:`~astroquery.jplhorizons.HorizonsClass` and not the results
table.

Date Formats
------------

JPL Horizons puts somewhat strict guidelines on the date formats:
individual epochs have to be provided as Julian Dates, whereas epoch
ranges have to be provided as ISO dates (YYYY-MM-DD HH-MM UT). If you
have your epoch dates in one of these formats but you need the other
format, make use of :class:`astropy.time.Time` for the conversion. An
example is provided here:

.. doctest-requires:: astropy

    >>> from astropy.time import Time
    >>> mydate_fromiso = Time('2018-07-23 15:55:23')  # pass date as string
    >>> print(mydate_fromiso.jd)  # convert Time object to Julian Date
    2458323.163460648
    >>> mydate_fromjd = Time(2458323.163460648, format='jd')
    >>> print(mydate_fromjd.iso) # convert Time object to ISO
    2018-07-23 15:55:23.000

:class:`astropy.time.Time` allows you to convert dates across a wide
range of formats. Please note that when reading in Julian Dates, you
have to specify the date format as ``'jd'``, as the integer passed to
:class:`~astropy.time.Time` is ambiguous.

Keep Queries Short
------------------

Keep in mind that queries are sent as URIs to the Horizons server. If
you query a large number of epochs (in the form of a list), this list
might be truncated as URIs are typically expected to be shorter than
2,000 symbols and your results might be compromised. If your query URI
is longer than this limit, a warning is given. In that case, please
try using a range of dates instead of a list of individual dates.


Acknowledgements
================

This submodule makes use of the `JPL Horizons <https://ssd.jpl.nasa.gov/horizons.cgi>`_ system.

The development of this submodule is in part funded through NASA PDART
Grant No. 80NSSC18K0987 to the `sbpy project <http://sbpy.org>`_.


Reference/API
=============

.. automodapi:: astroquery.jplhorizons
    :no-inheritance-diagram:

.. _Solar System Dynamics group at the Jet Propulation Laboratory: http://ssd.jpl.nasa.gov/
.. _MPC Observatory codes: http://minorplanetcenter.net/iau/lists/ObsCodesF.html
.. _astropy table: http://docs.astropy.org/en/stable/table/index.html
.. _astropy units: http://docs.astropy.org/en/stable/units/index.html
.. _Definition of Observer Table Quantities: http://ssd.jpl.nasa.gov/?horizons_doc#table_quantities
.. _Horizons documentation: http://ssd.jpl.nasa.gov/?horizons_doc
