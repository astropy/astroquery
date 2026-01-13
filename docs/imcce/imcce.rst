.. _astroquery.imcce:

******************************************************************************************************************************************
Institut de Mécanique Céleste et de Calcul des Éphémérides (IMCCE) Solar System Services (`astroquery.imcce`/astroquery.solarsystem.imcce)
******************************************************************************************************************************************

Overview
========

IMCCE provides a number of Solar System-related services, two of which are currently implemented here:

* `SkyBoT <https://ssp.imcce.fr/webservices/skybot/>`_: search for and
  identify Solar System objects that are present in a given area of
  the sky at a given time
* `Miriade <https://ssp.imcce.fr/webservices/miriade/>`_: ephemerides service

Use cases for both services are detailed below.


SkyBot - Solar System Body Identification Service
=================================================

Cone Search
-----------

`astroquery.imcce.SkybotClass` provides an interface to the `cone search
<https://ssp.imcce.fr/webservices/skybot/api/conesearch/>`_ offered by SkyBoT.

A simple cone search for Solar System objects in a circular field
looks like this:

.. doctest-remote-data::

   >>> from astroquery.imcce import Skybot
   >>> from astropy.coordinates import SkyCoord
   >>> from astropy.time import Time
   >>> import astropy.units as u
   >>> field = SkyCoord(0*u.deg, 0*u.deg)
   >>> epoch = Time('2019-05-29 21:42', format='iso')
   >>> results = Skybot.cone_search(field, 5*u.arcmin, epoch)
   >>> results["Number", "Name", "RA", "DEC", "Type"]
   <QTable length=5>
   Number    Name             RA                   DEC             Type  
                             deg                   deg                   
   int64    str32          float64               float64          str24  
   ------ ---------- -------------------- --------------------- ---------
       --  2012 BO42 0.019139999999999997              -0.01297 MB>Middle
   516566  2007 DH36 0.005300833333333333   0.02301111111111111  MB>Inner
   659626  2019 SS82         359.99291625 -0.028969444444444443  MB>Inner
       -- 2019 SH196   359.96022083333327 -0.030131944444444444  MB>Inner
   163149 2002 CV106    359.9866720833333  -0.06932138888888889  MB>Inner

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

+--------------------+-----------------------------------------------+
| Column Name        | Definition                                    |
+====================+===============================================+
| ``'Number'``       | Target Number (``-1`` if none provided, int)  |
+--------------------+-----------------------------------------------+
| ``'Name'``         | Target Name (str)                             |
+--------------------+-----------------------------------------------+
| ``'RA'``           | Target RA (J2000, deg, float)                 |
+--------------------+-----------------------------------------------+
| ``'DEC'``          | Target declination (J2000, deg, float)        |
+--------------------+-----------------------------------------------+
| ``'Type'``         | Target dynamical/physical type (str)          |
+--------------------+-----------------------------------------------+
| ``'V'``            | Target apparent brightness (V-band, mag,      |
|                    | float)                                        |
+--------------------+-----------------------------------------------+
| ``'posunc'``       | Positional uncertainty (arcsec, float)        |
+--------------------+-----------------------------------------------+
| ``'centerdist'``   | Angular distance of target from cone center   |
|                    | (arcsec, float)                               |
+--------------------+-----------------------------------------------+
| ``'RA_rate'``      | RA rate of motion (arcsec/hr, float)          |
+--------------------+-----------------------------------------------+
| ``'DEC_rate'``     | Declination rate of motion (arcsec/hr, float) |
+--------------------+-----------------------------------------------+
| ``'geodist'``      | Geocentric distance of target (au, float)     |
+--------------------+-----------------------------------------------+
| ``'heliodist'``    | Heliocentric distance of target (au, float)   |
+--------------------+-----------------------------------------------+
| ``'alpha'``        | Solar phase angle (deg, float)                |
+--------------------+-----------------------------------------------+
| ``'elong'``        | Solar elongation angle (deg, float)           |
+--------------------+-----------------------------------------------+
| ``'x'``            | Target equatorial vector x (au, float)        |
+--------------------+-----------------------------------------------+
| ``'y'``            | Target equatorial vector y (au, float)        |
+--------------------+-----------------------------------------------+
| ``'z'``            | Target equatorial vector z (au, float)        |
+--------------------+-----------------------------------------------+
| ``'vx'``           | Target velocity vector x (au/d, float)        |
+--------------------+-----------------------------------------------+
| ``'vy'``           | Target velocity vector y (au/d, float)        |
+--------------------+-----------------------------------------------+
| ``'vz'``           | Target velocity vector z (au/d, float)        |
+--------------------+-----------------------------------------------+
| ``'epoch'``        | Ephemerides epoch (JD, float)                 |
+--------------------+-----------------------------------------------+
| ``'_raj2000'``     | Astrometric J2000 right ascension             |
+--------------------+-----------------------------------------------+
| ``'_decj2000'``    | Astrometric J2000 declination                 |
+--------------------+-----------------------------------------------+
| ``'externallink'`` | External link to the target                   |
+--------------------+-----------------------------------------------+


Miriade - Ephemeris Service
===========================

The *Miriade* service enable the query of Solar System object ephemerides.
The most minimalistic `~astroquery.imcce.MiriadeClass.get_ephemerides`
query looks like this:

.. doctest-remote-data::

   >>> from astroquery.imcce import Miriade
   >>> Miriade.get_ephemerides('Ceres')  # doctest: +IGNORE_OUTPUT
   <Table length=1>
       epoch           RA             DEC         ...   DEC_rate       rv    
         d            deg             deg         ... arcsec / min   km / s  
      float64       float64         float64       ...   float64     float64  
   -------------- ------------ ------------------ ... ------------ ----------
   2461053.384583 11.912435375 -3.715397138888889 ...       0.3874   22.45706

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

.. doctest-remote-data::

   >>> from astroquery.imcce import Miriade
   >>> Miriade.get_ephemerides('Pallas', epoch='2019-01-01',
   ...                         epoch_step='1d', epoch_nsteps=365)  # doctest: +IGNORE_OUTPUT
   <Table length=365>
     epoch           RA                 DEC         ...   DEC_rate       rv    
       d            deg                 deg         ... arcsec / min   km / s  
   float64       float64             float64       ...   float64     float64  
   --------- ------------------ ------------------- ... ------------ ----------
   2458484.5 200.58658462499997  -5.998279138888889 ...       0.1585  -19.36784
   2458485.5 200.92701474999998  -5.933115777777778 ...       0.1673  -19.41378
   2458486.5 201.26418570833332  -5.864435027777778 ...       0.1761  -19.45526
   2458487.5       201.59803025 -5.7921869444444445 ...       0.1851  -19.49211
   2458488.5 201.92848124999998  -5.716322083333334 ...       0.1942  -19.52419
         ...                ...                 ... ...          ...        ...
   2458844.5  261.5084273333333   3.596639722222222 ...       0.0295   -2.51070
   2458845.5      261.885360875  3.6093634722222223 ...       0.0341   -2.72909
   2458846.5         262.261614  3.6239013055555556 ...       0.0386   -2.94674
   2458847.5 262.63715837499996           3.6402525 ...       0.0431   -3.16358
   2458848.5  263.0119662916667   3.658415888888889 ...       0.0477   -3.37956


The observer location is defined through the ``location`` keyword,
expecting a string containing the official IAU observatory code, a
spacecraft name, or a set of coordinates (see the `Miriade manual
<http://vo.imcce.fr/webservices/miriade/?documentation#field_7>`_ for
details).


Coordinate Types
^^^^^^^^^^^^^^^^

The `Miriade <https://ssp.imcce.fr/webservices/miriade/>`_ system offers
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
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``RA``           | Target RA at ``ephtype`` (deg, float)         |
  +------------------+-----------------------------------------------+
  | ``DEC``          | Target declination at ``ephtype`` (deg, float)|
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
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
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``px``           | X position state vector (au, float)           |
  +------------------+-----------------------------------------------+
  | ``py``           | Y position state vector (au, float)           |
  +------------------+-----------------------------------------------+
  | ``pz``           | Z position state vector (au, float)           |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``heldist``      | Target heliocentric distance (au, float)      |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``vx``           | X velocity state vector (au/d, float)         |
  +------------------+-----------------------------------------------+
  | ``vy``           | Y velocity state vector (au/d, float)         |
  +------------------+-----------------------------------------------+
  | ``vz``           | Z velocity state vector (au/d, float)         |
  +------------------+-----------------------------------------------+


3. Local coordinates:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``siderealtime`` | Local sidereal time (h min s, float)          |
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
  | ``refrac``       | Refraction (arcsec)                           |
  +------------------+-----------------------------------------------+

4. Hour angle coordinates:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``siderealtime`` | Local sidereal time (h min s, float)          |
  +------------------+-----------------------------------------------+
  | ``hourangle``    | Target hour angle (deg, float)                |
  +------------------+-----------------------------------------------+
  | ``dec``          | Target declination at ``ephtype`` (deg)       |
  +------------------+-----------------------------------------------+
  | ``delta``        | Distance from observer (au, float)            |
  +------------------+-----------------------------------------------+
  | ``V``            | Apparent visual magnitude (mag, float)        |
  +------------------+-----------------------------------------------+
  | ``alpha``        | Solar phase angle (deg)                       |
  +------------------+-----------------------------------------------+
  | ``elong``        | Solar elongation angle (deg)                  |
  +------------------+-----------------------------------------------+
  | ``airmass``      | Target airmass (float)                        |
  +------------------+-----------------------------------------------+

5. Dedicated to observations:

  +------------------+-----------------------------------------------+
  | Column Name      | Definition                                    |
  +==================+===============================================+
  | ``epoch``        | Ephemerides epoch (JD, float)                 |
  +------------------+-----------------------------------------------+
  | ``siderealtime`` | Local sidereal time (h min s, float)          |
  +------------------+-----------------------------------------------+
  | ``RA``           | Target RA at ``ephtype`` (deg, float)         |
  +------------------+-----------------------------------------------+
  | ``DEC``          | Target declination at ``ephtype`` (deg, float)|
  +------------------+-----------------------------------------------+
  | ``hourangle``    | Target hour angle (deg, float)                |
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
  | ``airmass``      | Target airmass (float)                        |
  +------------------+-----------------------------------------------+
  | ``RAcosD_rate``  | Rate of motion in RA * cos(DEC) (arcsec/min,  |
  |                  | float)                                        |
  +------------------+-----------------------------------------------+
  | ``DEC_rate``     | Rate of motion in DEC (arcsec/min, float)     |
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

See the `Miridae documentation
<https://ssp.imcce.fr/webservices/miriade/api/ephemcc/>`_ for details.


Acknowledgements
================

This submodule makes use of IMCCE's `SkyBoT
<https://ssp.imcce.fr/webservices/skybot/>`_ VO tool and the `IMCCE
Miriade service
<https://ssp.imcce.fr/webservices/miriade//>`_. Additional information on
SkyBoT can be obtained from `Berthier et al. 2006
<https://ui.adsabs.harvard.edu/abs/2006ASPC..351..367B/abstract>`_.

Please consider the following notes from IMCCE:

* If SkyBoT was helpful for your research work, the following
  acknowledgment would be appreciated: "*This research has made use of
  IMCCE's SkyBoT VO tool*", or cite the following article
  `2006ASPC..351..367B
  <https://ui.adsabs.harvard.edu/abs/2006ASPC..351..367B/abstract>`_.
* If Miriade was helpful for your research work, the following
  acknowledgment would be appreciated: "*This research has made use of
  IMCCE's Miriade VO tool*"

The development of this submodule was funded through NASA PDART Grant
No. 80NSSC18K0987 to the `sbpy project <https://sbpy.org>`_.


Reference/API
=============

.. automodapi:: astroquery.imcce
    :no-inheritance-diagram:
