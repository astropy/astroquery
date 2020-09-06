.. doctest-skip-all

.. _astroquery.imcce:

******************************************************************************************************************************************
Institut de Mécanique Céleste et de Calcul des Éphémérides (IMCCE) Solar System Services (`astroquery.imcce`/astroquery.solarsystem.imcce)
******************************************************************************************************************************************

Overview
========

IMCCE provides a number of Solar System-related services, two of which are currently implemented here:

* `SkyBoT <http://vo.imcce.fr/webservices/skybot/>`_: search for and
  identify Solar System objects that are present in a given area of
  the sky at a given time
* `Miriade <http://vo.imcce.fr/webservices/miriade/>`_: ephemerides service

Use cases for both services are detailed below.
  

SkyBot - Solar System Body Identification Service
=================================================

Cone Search
-----------

`astroquery.imcce.SkybotClass` provides an interface to the `cone search
<http://vo.imcce.fr/webservices/skybot/?conesearch>`_ offered by SkyBoT.

A simple cone search for Solar System objects in a circular field
looks like this:

.. code-block:: python

   >>> from astroquery.imcce import Skybot
   >>> from astropy.coordinates import SkyCoord
   >>> from astropy.time import Time
   >>> import astropy.units as u
   >>> field = SkyCoord(0*u.deg, 0*u.deg)
   >>> epoch = Time('2019-05-29 21:42', format='iso')
   >>> Skybot.cone_search(field, 5*u.arcmin, epoch)  # doctest: +SKIP
   <QTable length=2>
   Number    Name            RA         ...      vy          vz       epoch
			    deg         ...    AU / d      AU / d       d
   int64    str10         float64       ...   float64     float64    float64
   ------ ---------- ------------------ ... ----------- ----------- ---------
   516566  2007 DH36           0.005535 ... 0.008556458 0.002875929 2458630.0
   163149 2002 CV106 359.98691791666664 ... 0.009078103  0.00267749 2458630.0

`~astroquery.imcce.SkybotClass.cone_search` produces a
`~astropy.table.QTable` object with the properties of all Solar System
bodies that are present in the cone at the given epoch. 
   
The required input arguments for
`~astroquery.imcce.SkybotClass.cone_search` are the center coordinates
of the cone, its radius, as well as the epoch of the
observation. Field center coordinates ``coo`` should be provided as a
`~astropy.coordinates.SkyCoord` object, the radius of the cone ``rad``
should be provided as a `~astropy.units.Quantity` object. Note that
the maximum cone radius is limited to 10 degrees by the SkyBoT
service. The ``epoch`` of the observation should be provided as
`~astropy.time.Time` object.

The following optional parameters are available:

* ``location``: the location of the observer on Earth using the
  official `list of IAU codes
  <https://www.minorplanetcenter.net/iau/lists/ObsCodes.html>`_. If no
  location is provided, the center of the Earth is used as location.
* ``position_error``: the maximum positional uncertainty of each body
  at the given epoch. This option can be used to improve the
  reliability of associations with detected sources in the field. If
  not provided, the maximum positional uncertainty of 120 arcsec is
  used.
* ``find_planets``, ``find_asteroids``, ``find_comets``: these flags
  control what types of Solar System objects are identified. By
  default, each of the flags is ``True``.

For diagnostic purposes, the query payload or raw response from the
service can be returned instead of the parsed results using the flags
``get_query_payload`` and ``get_raw_response``, respectively.

The resulting `~astropy.table.QTable` contains all available
information provided by SkyBoT with corresponding units. The following
properties are obtained:

+------------------+-----------------------------------------------+
| Column Name      | Definition                                    |
+==================+===============================================+
| ``'Number'``     | Target Number (``-1`` if none provided, int)  |
+------------------+-----------------------------------------------+
| ``'Name'``       | Target Name (str)                             |
+------------------+-----------------------------------------------+
| ``'RA'``         | Target RA (J2000, deg, float)                 |
+------------------+-----------------------------------------------+
| ``'DEC'``        | Target declination (J2000, deg, float)        |
+------------------+-----------------------------------------------+
| ``'Type'``       | Target dynamical/physical type (str)          |
+------------------+-----------------------------------------------+
| ``'V'``          | Target apparent brightness (V-band, mag,      |
|                  | float)                                        |
+------------------+-----------------------------------------------+
| ``'posunc'``     | Positional uncertainty (arcsec, float)        |
+------------------+-----------------------------------------------+
| ``'centerdist'`` | Angular distance of target from cone center   |
|                  | (arcsec, float)                               |
+------------------+-----------------------------------------------+
| ``'RA_rate'``    | RA rate of motion (arcsec/hr, float)          |
+------------------+-----------------------------------------------+
| ``'DEC_rate'``   | Declination rate of motion (arcsec/hr, float) |
+------------------+-----------------------------------------------+
| ``'geodist'``    | Geocentric distance of target (au, float)     |
+------------------+-----------------------------------------------+
| ``'heliodist'``  | Heliocentric distance of target (au, float)   |
+------------------+-----------------------------------------------+
| ``'alpha'``      | Solar phase angle (deg, float)                |
+------------------+-----------------------------------------------+
| ``'elong'``      | Solar elongation angle (deg, float)           |
+------------------+-----------------------------------------------+
| ``'x'``          | Target equatorial vector x (au, float)        |
+------------------+-----------------------------------------------+
| ``'y'``          | Target equatorial vector y (au, float)        |
+------------------+-----------------------------------------------+
| ``'z'``          | Target equatorial vector z (au, float)        |
+------------------+-----------------------------------------------+
| ``'vx'``         | Target velocity vector x (au/d, float)        |
+------------------+-----------------------------------------------+
| ``'vy'``         | Target velocity vector y (au/d, float)        |
+------------------+-----------------------------------------------+
| ``'vz'``         | Target velocity vector z (au/d, float)        |
+------------------+-----------------------------------------------+
| ``'epoch'``      | Ephemerides epoch (JD, float)                 |
+------------------+-----------------------------------------------+


Miriade - Ephemeris Service
===========================

The *Miriade* service enable the query of Solar System object ephemerides.
The most minimalistic `~astroquery.imcce.MiriadeClass.get_ephemerides`
query looks like this:

.. code-block:: python

   >>> from astroquery.miriade import Miriade
   >>> Miriade.get_ephemerides('Ceres')
   <Table masked=True length=1>
    target        epoch                 RA        ...  DEC_rate   delta_rate 
		    d                  deg        ... arcs / min    km / s   
   bytes20       float64             float64      ...  float64     float64   
   ------- -------------------- ----------------- ... ---------- ------------
     Ceres    2458519.315165116 242.1874308333333 ...   -0.14926  -20.9668673
   
This query will return ephemerides for asteroid Ceres, for the current
epoch, and for a geocentric location. The query output is formatted as
a `~astropy.table.Table`.

Ephemerides Queries
-------------------

*Miriade* queries are highly customizable.


Epochs and Location
^^^^^^^^^^^^^^^^^^^

`~astroquery.imcce.MiriadeClass.get_ephemerides` is able to query a
range of epochs starting at epoch ``epoch`` in steps of ``epoch_step``
for a total of ``epoch_nsteps``. ``epoch`` has to be provided as a
`~astropy.time.Time` object, a float (interpreted as Julian Date), or
a string (interpreted as iso date *YYYY-MM-DD HH-MM-SS*). Time steps
``epoch_step`` are provided as string that consist of a floating point
number followed by a single character: ``d`` refers to days, ``h`` to
hours, ``m`` to minutes, ``s`` to seconds; e.g., ``'1.23d'`` defines a
time step of 1.23 days. ``epoch_nsteps`` defines the number of steps
between the individual ephemerides. By default, ``epoch_nsteps = 1``,
which means that only a single epoch ``epoch`` will be queried.

Consider the following example, which queries ephemerides for asteroid
Pallas over an entire year with a time step of 1 day:

.. code-block:: python

   >>> from astroquery.miriade import Miriade
   >>> Miriade.get_ephemerides('Pallas', epoch='2019-01-01',
   >>>                         epoch_step='1d', epoch_nsteps=365) # doctest: +SKIP
   <Table masked=True length=365>
    target        epoch                 RA         ...  DEC_rate   delta_rate 
		    d                  deg         ... arcs / min    km / s   
   bytes20       float64             float64       ...  float64     float64   
   ------- -------------------- ------------------ ... ---------- ------------
    Pallas            2458484.5  200.5865645833333 ...    0.15854  -19.3678422
    Pallas            2458485.5 200.92699458333328 ...    0.16727  -19.4137907
    Pallas            2458486.5 201.26416541666663 ...    0.17613  -19.4552649
    Pallas            2458487.5 201.59800958333332 ...    0.18511  -19.4921113
    Pallas            2458488.5  201.9284608333333 ...    0.19421  -19.5241972
    Pallas            2458489.5 202.25545124999996 ...    0.20344  -19.5514101
       ...                  ...                ... ...        ...          ...
    Pallas            2458843.5  261.1308308333333 ...   0.025007   -2.2916737
    Pallas            2458844.5  261.5084158333333 ...   0.029542   -2.5107013
    Pallas            2458845.5 261.88534958333327 ...   0.034077   -2.7290895
    Pallas            2458846.5        262.2616025 ...   0.038612   -2.9467393
    Pallas            2458847.5  262.6371470833333 ...   0.043144   -3.1635784
    Pallas            2458848.5         263.011955 ...   0.047672   -3.3795565


The observer location is defined through the ``location`` keyword,
expecting a string containing the official IAU observatory code,
a spacecraft name, or a set of coordinates (see the `Miriade manual
<http://vo.imcce.fr/webservices/miriade/?documentation#field_7>`_ for
details). You can access the list of IAU observatory codes with the
`~astroquery.imcce.MiriadeClass.get_observatory_codes` helper function:

.. code-block:: python

    >>> from astroquery.miriade import Miriade
    >>> obs_codes = Miriade.get_observatory_codes() # doctest: +SKIP
    <Table length=2238>
    Code   Long.     cos      sin                       Name                            c
    str3  float64  float64  float64                    str48                         float64
    ---- --------- -------- -------- ------------------------------------------ ------------------
     000       0.0  0.62411  0.77873                                  Greenwich 0.9959337050000001
     001    0.1542  0.62992  0.77411                                Crowborough       0.9960454985
     002      0.62    0.622    0.781                                   Rayleigh 0.9968450000000001
     003       3.9    0.725    0.687                                Montpellier 0.9975940000000001
     004    1.4625   0.7252  0.68627                                   Toulouse 0.9968815528999999
     005     2.231 0.659891 0.748875                                     Meudon     0.996269897506
     006   2.12417 0.751042 0.658129               Fabra Observatory, Barcelona     0.997197866405
     007   2.33675  0.65947 0.749223                                      Paris     0.996235784629
     008    3.0355  0.80172  0.59578                          Algiers-Bouzareah       0.9977087668
     009    7.4417   0.6838   0.7272                                Berne-Uecht 0.9964022799999999
     010   6.92124 0.723655 0.688135                                   Caussols 0.9972063372500002
     011    8.7975   0.6792  0.73161                                   Wetzikon       0.9965658321
     012   4.35821 0.633333 0.771306                                      Uccle 0.9960236345250001
     013   4.48397 0.614813 0.786029                                     Leiden      0.99583661381
     014   5.39509 0.728859 0.682384                                 Marseilles     0.996883365337
     ...       ...      ...      ...                                        ...                ...
     Z84 357.45179 0.797523 0.601826                         Calar Alto-Schmidt 0.9982374698049998
     Z85 356.75028 0.801058 0.596932            Observatorio Sierra Contraviesa 0.9980217319880001
     Z86    356.89  0.62347  0.77923                                St. Mellons 0.9959142337999999
     Z87  357.1021 0.608005 0.791293      Stanley Laver Observatory, Pontesbury 0.9958146918740001
     Z88  357.5101  0.62716  0.77632 Fosseway Observatoy, Stratton-on-the-Fosse 0.9960024080000001
     Z89  357.8281  0.59942  0.79777                               Macclesfield 0.9957413092999999
     Z90  357.8482   0.7954  0.60418                                      Albox       0.9976946324
     Z91 358.74999 0.631731 0.772595                                  Curdridge     0.995987090386
     Z92 358.39222 0.591378 0.803713                 Almalex Observatory, Leeds 0.9956825252529999
     Z93 359.85589  0.78238 0.620769               Observatorio Polop, Alicante     0.997472615761
     Z94  358.8565  0.62725  0.77623                                  Kempshott 0.9959755753999999
     Z95  358.8909  0.76782  0.63883   Astronomia Para Todos Remote Observatory 0.9976513212999999
     Z96 359.19369 0.747818 0.661731                  Observatorio Cesaraugusto     0.997119677485
     Z97 359.41647 0.704568  0.70727            OPERA Observatory, Saint Palais 0.9966469195239999
     Z98  359.5216  0.77156  0.63405                   Observatorio TRZ, Betera 0.9973242361000001
     Z99 359.97874 0.595468 0.800687            Clixby Observatory, Cleethorpes 0.9956818109930001

This will return the complete list of IAU observatory codes.  To search
for a particular observatory, you can provide a regular expression string
using the ``restr`` parameter:

.. code-block:: python

    >>> obs_codes = Miriade.get_observatory_codes(restr='Green') # doctest: +SKIP
    <Table length=8>
    Code   Long.     cos       sin                        Name
    str3  float64  float64   float64                     str48
    ---- --------- -------- --------- -------------------------------------------
     000       0.0  0.62411   0.77873                                   Greenwich
     256 280.16017 0.784451   0.61832                                  Green Bank
     912  288.2342  0.74769   0.66186          Carbuncle Hill Observatory, Greene
     967  358.9778  0.61508   0.78585                               Greens Norton
     B34   33.7258  0.81748   0.57405         Green Island Observatory, Gecitkale
     H48  265.0139  0.79424   0.60565        PSU Greenbush Observatory, Pittsburg
     Q54 147.28772  0.73929 -0.671278 Harlingten Telescope, Greenhill Observatory
     Z54 358.92214 0.623422  0.779306             Greenmoor Observatory, Woodcote

Coordinate Types
^^^^^^^^^^^^^^^^

The `Miriade <http://vo.imcce.fr/webservices/miriade/>`_ system offers
a range of different *coordinate types* - sets of coordinates and
properties that can be queried. In agreement with the Miriade webform
query, the coordinate type in
`~astroquery.imcce.MiriadeClass.get_ephemerides` is defined through
an integer value. For a full discussion of the different coordinate
types we refer to `this section
<http://vo.imcce.fr/webservices/miriade/?ephemcc#outputparam>`_ of the
Miriade website. The keyword ``coordtype`` controls which set of
coordinates and properties are queried.


Here, we list the different coordinates and properties as returned by
`~astroquery.imcce.MiriadeClass.get_ephemerides` for the different
coordinate types available (the item numbers refer to the integer code
to be provided to the keyword ``coordtype`` to use these sets) :

1. Spherical coordinates (default):

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``target``       | Target name (str)                             |
  +------------------+-----------------------------------------------+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``RA``           | Target RA at ``ephtype`` (deg, float)         |
  +------------------+-----------------------------------------------+
  | ``DEC``          | Target declination at ``ephtype`` (deg, float)|
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``delta_rate``   | Rate in observer distance (km/s, float)       |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``RAcosD_rate``  | Rate of motion in RA * cos(DEC) (arcsec/min,  |
  |                  | float)                                        |
  +------------------+-----------------------------------------------+
  | ``DEC_rate``     | Rate of motion in DEC (arcsec/min, float)     |
  +------------------+-----------------------------------------------+

2. Rectangular coordinates:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``target``       | Target name (str)                             |
  +------------------+-----------------------------------------------+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``x``            | X position state vector (au, float)           |
  +------------------+-----------------------------------------------+
  | ``y``            | Y position state vector (au, float)           |
  +------------------+-----------------------------------------------+
  | ``z``            | Z position state vector (au, float)           |
  +------------------+-----------------------------------------------+
  | ``vx``           | X velocity state vector (au/d, float)         |
  +------------------+-----------------------------------------------+
  | ``vy``           | Y velocity state vector (au/d, float)         |
  +------------------+-----------------------------------------------+
  | ``vz``           | Z velocity state vector (au/d, float)         |
  +------------------+-----------------------------------------------+
  | ``rv``           | Radial velocity (km/s, float)                 |
  +------------------+-----------------------------------------------+
  | ``heldist``      | Target heliocentric distance (au, float)      |
  +------------------+-----------------------------------------------+
  | ``x_h``          | X heliocentric position vector (au, float)    |
  +------------------+-----------------------------------------------+
  | ``y_h``          | Y heliocentric position vector (au, float)    |
  +------------------+-----------------------------------------------+
  | ``z_h``          | Z heliocentric position vector (au, float)    |
  +------------------+-----------------------------------------------+
  | ``vx_h``         | X heliocentric vel. vector (au/d, float)      |
  +------------------+-----------------------------------------------+
  | ``vy_h``         | Y heliocentric vel. vector (au/d, float)      |
  +------------------+-----------------------------------------------+
  | ``vz_h``         | Z heliocentric vel. vector (au/d, float)      |
  +------------------+-----------------------------------------------+
   
   
3. Local coordinates:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``target``       | Target name (str)                             |
  +------------------+-----------------------------------------------+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``AZ``           | Target azimuth (deg, float)                   |
  +------------------+-----------------------------------------------+
  | ``EL``           | Target elevation (deg, float)                 |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+

4. Hour angle coordinates:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``target``       | Target name (str)                             |
  +------------------+-----------------------------------------------+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``DEC``          | Target declination at ``ephtype`` (deg)       |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``hourangle``    | Target hour angle (deg, float)                |
  +------------------+-----------------------------------------------+

5. dedicated to observations:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``target``       | Target name (str)                             |
  +------------------+-----------------------------------------------+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``DEC``          | Target declination at ``ephtype`` (deg)       |
  +------------------+-----------------------------------------------+
  | ``RAJ2000``      | Target RA at J2000 (deg, float)               |
  +------------------+-----------------------------------------------+
  | ``DECJ2000``     | Target declination at J2000 (deg, float)      |
  +------------------+-----------------------------------------------+
  | ``AZ``           | Target azimuth (deg, float)                   |
  +------------------+-----------------------------------------------+
  | ``EL``           | Target elevation (deg, float)                 |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``delta_rate``   | Rate in observer distance (km/s, float)       |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``RAcosD_rate``  | Rate of motion in RA * cos(DEC) (arcsec/min,  |
  |                  | float)                                        |
  +------------------+-----------------------------------------------+
  | ``DEC_rate``     | Rate of motion in DEC (arcsec/min, float)     |
  +------------------+-----------------------------------------------+
  | ``heldist``      | Target heliocentric distance (au, float)      |
  +------------------+-----------------------------------------------+
  | ``hourangle``    | Target hour angle (deg, float)                |
  +------------------+-----------------------------------------------+
  | ``siderealtime`` | Local sidereal time (hr, float)               |
  +------------------+-----------------------------------------------+
  | ``refraction``   | Atmospheric refraction (arcsec, float)        |
  +------------------+-----------------------------------------------+
  | ``airmass``      | Target airmass (float)                        |
  +------------------+-----------------------------------------------+
  | ``posunc``       | Positional uncertainty (arcsec, float)        |
  +------------------+-----------------------------------------------+

6. dedicated to AO observations:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``target``       | Target name (str)                             |
  +------------------+-----------------------------------------------+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``RAJ2000``      | Target RA at J2000 (deg, float)               |
  +------------------+-----------------------------------------------+
  | ``DECJ2000``     | Target declination at J2000 (deg, float)      |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``delta_rate``   | Rate in observer distance (km/s, float)       |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``RAcosD_rate``  | Rate of motion in RA * cos(DEC) (arcsec/min,  |
  |                  | float)                                        |
  +------------------+-----------------------------------------------+
  | ``DEC_rate``     | Rate of motion in DEC (arcsec/min, float)     |
  +------------------+-----------------------------------------------+
  | ``heldist``      | Target heliocentric distance (au, float)      |
  +------------------+-----------------------------------------------+
  | ``siderealtime`` | Local sidereal time (hr, float)               |
  +------------------+-----------------------------------------------+
  | ``refraction``   | Atmospheric refraction (arcsec, float)        |
  +------------------+-----------------------------------------------+
  | ``airmass``      | Target airmass (float)                        |
  +------------------+-----------------------------------------------+
  | ``posunc``       | Positional uncertainty (arcsec, float)        |
  +------------------+-----------------------------------------------+


Other parameters
^^^^^^^^^^^^^^^^

A range of additional parameters is available in
`~astroquery.imcce.MiriadeClass.get_ephemerides` to modify the query
results:

* ``timescale``: switch between UTC (default) and TT
* ``planetary_theory``: use planetary ephemerides other than INPOP
* ``ephtype``: switch between J2000 ephemerides (default) and other
  coordinates
* ``refplane``: switch from equatorial coordinates (default) to
  ecliptical coordinates
* ``elements``: switch to MPCORB ephemerides instead of ASTORB
* ``radial_velocity``: provides additional information on target's radial
  velocity  




Acknowledgements
================

This submodule makes use of IMCCE's `SkyBoT
<http://vo.imcce.fr/webservices/skybot/>`_ VO tool and the `IMCCE
Miriade service
<http://vo.imcce.fr/webservices/miriade/>`_. Additional information on
SkyBoT can be obtained from `Berthier et al. 2006
<http://adsabs.harvard.edu/abs/2006ASPC..351..367B>`_.

Please consider the following notes from IMCCE:

* If SkyBoT was helpful for your research work, the following
  acknowledgment would be appreciated: "*This research has made use of
  IMCCE's SkyBoT VO tool*", or cite the following article
  `2006ASPC..351..367B
  <http://adsabs.harvard.edu/abs/2006ASPC..351..367B>`_.
* If Miriade was helpful for your research work, the following
  acknowledgment would be appreciated: "*This research has made use of
  IMCCE's Miriade VO tool*"

The development of this submodule is funded through NASA PDART Grant
No. 80NSSC18K0987 to the `sbpy project <http://sbpy.org>`_.

     
Reference/API
=============

.. automodapi:: astroquery.imcce
    :no-inheritance-diagram:

