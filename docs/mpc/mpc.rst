.. doctest-skip-all

.. _astroquery.mpc:

*************************************************************************
Minor Planet Center Queries (`astroquery.mpc`/astroquery.solarsystem.MPC)
*************************************************************************

Getting started
===============

This is an Astroquery wrapper for querying services at the IAU Minor
Planet Center (MPC).  Three services are available:

    - `Minor Planet Center Web Service
      <https://minorplanetcenter.net/web_service/>`__ for comet and
      asteroid orbits and parameters
    - `Minor Planet Ephemeris Service
      <https://www.minorplanetcenter.net/iau/MPEph/MPEph.html>`__ for
      comet and asteroid ephemerides
    - `Minor Planet Center Observations Database
      <https://minorplanetcenter.net/db_search>`_ for obtaining
      observations of asteroids and comets reported to the MPC
      
In addition, the module provides access to the MPC's hosted list of
`IAU Observatory Codes
<https://www.minorplanetcenter.net/iau/lists/ObsCodesF.html>`__.

To return the orbit of Ceres and an ephemeris for the next 20 days:

.. code-block:: python

    >>> from astroquery.mpc import MPC
    >>> from pprint import pprint
    >>> result = MPC.query_object('asteroid', name='ceres')
    >>> pprint(result)

    [{'absolute_magnitude': '3.34',
      'aphelion_distance': '2.976',
      'arc_length': 79346,
      'argument_of_perihelion': '73.11528',
      'ascending_node': '80.309916',
      'critical_list_numbered_object': False,
      'delta_v': 10.5,
      'designation': None,
      'earth_moid': 1.59353,
      'eccentricity': '0.0755347',
      'epoch': '2018-03-23.0',
      'epoch_jd': '2458200.5',
      'first_observation_date_used': '1801-01-31.0',
      'first_opposition_used': '1801',
      'inclination': '10.59351',
      'jupiter_moid': 2.09509,
      'km_neo': False,
      'last_observation_date_used': '2018-04-30.0',
      'last_opposition_used': '2018',
      'mars_moid': 0.939285,
      'mean_anomaly': '352.23053',
      'mean_daily_motion': '0.2141308',
      'mercury_moid': 2.18454,
      'name': 'Ceres',
      'neo': False,
      'number': 1,
      'observations': 6714,
      'oppositions': 114,
      'orbit_type': 0,
      'orbit_uncertainty': '0',
      'p_vector_x': '-0.87827464',
      'p_vector_y': '0.33795667',
      'p_vector_z': '0.33825869',
      'perihelion_date': '2018-04-28.28377',
      'perihelion_date_jd': '2458236.78377',
      'perihelion_distance': '2.5580384',
      'period': '4.6',
      'pha': False,
      'phase_slope': '0.12',
      'q_vector_x': '-0.44248619',
      'q_vector_y': '-0.84255513',
      'q_vector_z': '-0.30709418',
      'residual_rms': '0.6',
      'saturn_moid': 6.38856,
      'semimajor_axis': '2.7670463',
      'tisserand_jupiter': 3.3,
      'updated_at': '2018-05-31T01:07:39Z',
      'uranus_moid': 15.6642,
      'venus_moid': 1.84632}]

    >>> eph = MPC.get_ephemeris('ceres')
    >>> print(eph)
    
              Date                  RA                Dec        Delta   r   Elongation Phase  V  Proper motion Direction Uncertainty 3sig Unc. P.A.
                                   deg                deg          AU    AU     deg      deg  mag   arcsec / h     deg         arcsec         deg   
    ----------------------- ------------------ ----------------- ----- ----- ---------- ----- --- ------------- --------- ---------------- ---------
    2018-08-23 15:56:35.000 177.25874999999996              9.57 3.466 2.581       24.6   9.4 8.7         66.18     115.9               --        --
    2018-08-24 15:56:35.000          177.66125 9.377222222222223 3.471 2.581       24.1   9.2 8.7         66.24     115.9               --        --
    2018-08-25 15:56:35.000 178.06416666666667 9.184166666666666 3.476 2.582       23.6   9.0 8.7          66.3     115.9               --        --
    2018-08-26 15:56:35.000  178.4670833333333  8.99111111111111 3.481 2.582       23.1   8.8 8.7         66.36     115.9               --        --
                        ...                ...               ...   ...   ...        ...   ... ...           ...       ...              ...       ...
    2018-09-09 15:56:35.000             184.13 6.287222222222222 3.539 2.588       16.3   6.3 8.7         67.08     115.5               --        --
    2018-09-10 15:56:35.000          184.53625 6.094444444444444 3.542 2.588       15.9   6.1 8.6         67.12     115.5               --        --
    2018-09-11 15:56:35.000 184.94249999999997 5.901944444444445 3.545 2.589       15.4   5.9 8.6         67.15     115.5               --        --
    2018-09-12 15:56:35.000 185.34874999999997 5.709444444444444 3.548 2.589       14.9   5.8 8.6         67.18     115.4               --        --
    Length = 21 rows



Orbits and parameters
=====================

Search parameters
-----------------

Individual objects can be found with ``MPC.query_object``, and
``MPC.query_objects`` can return multiple objects.  Parameters can be
queried in three manners:

    - exact match
    - with a _min suffix, which sets the minimum value for the parameter
    - with a _max suffix, which sets the maximum value for the parameter

An example of an exact match:

.. code-block:: python

    >>> from astroquery.mpc import MPC
    >>> result = MPC.query_object('asteroid', name='ceres')
    >>> print(result)

    [{'absolute_magnitude': '3.34', 'aphelion_distance': '2.976', 'arc_length': 79247, 'argument_of_perihelion': '73.11528', 'ascending_node': '80.3099167', 'critical_list_numbered_object': False, 'delta_v': 10.5, 'designation': None, 'earth_moid': 1.59353, 'eccentricity': '0.0755347', 'epoch': '2018-03-23.0', 'epoch_jd': '2458200.5', 'first_observation_date_used': '1801-01-31.0', 'first_opposition_used': '1801', 'inclination': '10.59351', 'jupiter_moid': 2.09509, 'km_neo': False, 'last_observation_date_used': '2018-01-20.0', 'last_opposition_used': '2018', 'mars_moid': 0.939285, 'mean_anomaly': '352.23052', 'mean_daily_motion': '0.2141308', 'mercury_moid': 2.18454, 'name': 'Ceres', 'neo': False, 'number': 1, 'observations': 6689, 'oppositions': 114, 'orbit_type': 0, 'orbit_uncertainty': '0', 'p_vector_x': '-0.87827466', 'p_vector_y': '0.33795664', 'p_vector_z': '0.33825868', 'perihelion_date': '2018-04-28.28378', 'perihelion_date_jd': '2458236.78378', 'perihelion_distance': '2.5580384', 'period': '4.6', 'pha': False, 'phase_slope': '0.12', 'q_vector_x': '-0.44248615', 'q_vector_y': '-0.84255514', 'q_vector_z': '-0.30709419', 'residual_rms': '0.6', 'saturn_moid': 6.38856, 'semimajor_axis': '2.7670463', 'tisserand_jupiter': 3.3, 'updated_at': '2018-02-26T17:29:46Z', 'uranus_moid': 15.6642, 'venus_moid': 1.84632}]

A minimum value:

.. code-block:: python

    >>> result = MPC.query_objects('asteroid', inclination_min=170)

which will get all asteroids with an inclination of greater than or
equal to 170.

A maximum value:

.. code-block:: python

    >>> result = MPC.query_objects('asteroid', inclination_max=1.0)
    
which will get all asteroids with an inclination of less than or equal to 1.

There is another parameter that can be used, ```is_not_null```. This
can be used in the following fashion:

.. code-block:: python

    >>> result = MPC.query_objects('asteroid', name="is_not_null")

This will, predictably, find all named objects in the MPC
database--but that would take a while!


Sorting and return limits
-------------------------

The MPC web service allows a consumer to sort results in order to find
a number of objects fitting into the top or bottom of a range of
values (or all, if truly desired).

The service also allows a consumer to limit their results to a number
of objects, which, when paired with sorting, creates very flexible
options.

.. code-block:: python

    >>> result = MPC.query_objects('asteroid', order_by_desc="semimajor_axis", limit=10)

This will return the 10 furthest asteroids.

Customizing return fields
-------------------------

If a consumer isn't interested in some return fields, they can use the
MPC to limit the fields they're interested in.

.. code-block:: python

    >>> result = MPC.query_object('asteroid', name="ceres", return_fields="name,number")
    >>> print(result)
    [{'name': 'Ceres', 'number': 1}]


Ephemerides
===========

Comet and asteroid ephemerides can be generated using the `Minor
Planet Ephemeris Service
<https://www.minorplanetcenter.net/iau/MPEph/MPEph.html>`__ (MPES).
The MPES supports queries for any comet or asteroid by name,
designation, or packed designation, and any Earth-based location.
Ephemerides are computed starting on a specific date, then for
equally-spaced intervals thereafter.  The ephemeris is returned as an
Astropy `~astropy.table.Table`.



Dates and intervals
-------------------

For the ephemeris of asteroid (24) Themis, starting today with the
default time step (1 day) and location (geocenter):

.. code-block:: python

    >>> from astroquery.mpc import MPC
    >>> eph = MPC.get_ephemeris('24')
    >>> print(eph)
              Date                  RA                Dec         Delta   r   Elongation Phase  V   Proper motion Direction Uncertainty 3sig Unc. P.A.
                                   deg                deg           AU    AU     deg      deg  mag    arcsec / h     deg         arcsec         deg   
    ----------------------- ------------------ ------------------ ----- ----- ---------- ----- ---- ------------- --------- ---------------- ---------
    2018-08-16 14:34:53.000  96.46708333333333 23.749722222222225 3.502 2.916       47.5  14.8 12.9         53.08      92.1               --        --
    2018-08-17 14:34:53.000  96.85291666666666  23.73638888888889 3.491 2.915       48.1  15.0 12.9         52.91      92.3               --        --
    2018-08-18 14:34:53.000  97.23708333333333 23.721944444444443  3.48 2.914       48.7  15.1 12.9         52.74      92.4               --        --
    2018-08-19 14:34:53.000  97.62041666666666 23.706666666666667 3.469 2.912       49.3  15.3 12.9         52.56      92.6               --        --
                        ...                ...                ...   ...   ...        ...   ...  ...           ...       ...              ...       ...
    2018-09-02 14:34:53.000 102.82333333333332 23.412499999999998 3.302 2.898       58.1  17.2 12.8          49.7      94.5               --        --
    2018-09-03 14:34:53.000 103.18208333333332  23.38611111111111 3.289 2.897       58.7  17.3 12.8         49.46      94.6               --        --
    2018-09-04 14:34:53.000 103.53916666666666 23.359166666666667 3.277 2.896       59.4  17.4 12.8         49.21      94.8               --        --
    2018-09-05 14:34:53.000 103.89458333333332 23.331666666666667 3.264 2.895       60.0  17.6 12.8         48.96      94.9               --        --
    Length = 21 rows

Step sizes are parsed with Astropy's `~astropy.units.Quantity`.  For a time step of 1 hour:

.. code-block:: python

    >>> eph = MPC.get_ephemeris('24', step='1h')
    >>> print(eph)
              Date                  RA               Dec         Delta   r   Elongation Phase  V   Proper motion Direction Uncertainty 3sig Unc. P.A.
                                   deg               deg           AU    AU     deg      deg  mag    arcsec / h     deg         arcsec         deg   
    ----------------------- ----------------- ------------------ ----- ----- ---------- ----- ---- ------------- --------- ---------------- ---------
    2018-08-16 14:00:00.000 96.45791666666666              23.75 3.503 2.916       47.5  14.8 12.9         53.09      92.1               --        --
    2018-08-16 15:00:00.000 96.47374999999998 23.749444444444446 3.502 2.916       47.5  14.8 12.9         53.08      92.1               --        --
    2018-08-16 16:00:00.000             96.49  23.74888888888889 3.502 2.916       47.6  14.8 12.9         53.07      92.1               --        --
    2018-08-16 17:00:00.000 96.50624999999998 23.748333333333335 3.501 2.916       47.6  14.9 12.9         53.06      92.1               --        --
                        ...               ...                ...   ...   ...        ...   ...  ...           ...       ...              ...       ...
    2018-08-18 11:00:00.000 97.17999999999998 23.724166666666665 3.482 2.914       48.6  15.1 12.9         52.76      92.4               --        --
    2018-08-18 12:00:00.000 97.19583333333333 23.723611111111108 3.481 2.914       48.7  15.1 12.9         52.76      92.4               --        --
    2018-08-18 13:00:00.000 97.21208333333333 23.723055555555554 3.481 2.914       48.7  15.1 12.9         52.75      92.4               --        --
    2018-08-18 14:00:00.000 97.22791666666666  23.72222222222222  3.48 2.914       48.7  15.1 12.9         52.74      92.4               --        --
    Length = 49 rows

Start dates are parsed with Astropy's `~astropy.time.Time`.  For a
weekly ephemeris in 2020:

.. code-block:: python

    >>> eph = MPC.get_ephemeris('24', start='2020-01-01', step='7d', number=52)
    >>> print(eph)
              Date                  RA                 Dec         Delta   r   Elongation Phase  V   Proper motion Direction Uncertainty 3sig Unc. P.A.
                                   deg                 deg           AU    AU     deg      deg  mag    arcsec / h     deg         arcsec         deg   
    ----------------------- ------------------ ------------------- ----- ----- ---------- ----- ---- ------------- --------- ---------------- ---------
    2020-01-01 00:00:00.000 209.16749999999996  -11.63361111111111 3.066 2.856       68.5  18.7 12.7         45.15     110.6               --        --
    2020-01-08 00:00:00.000 211.11999999999995 -12.342500000000001  2.98 2.863       73.6  19.2 12.7         42.09     110.2               --        --
    2020-01-15 00:00:00.000 212.93749999999997 -12.987222222222222 2.892  2.87       78.9  19.7 12.6          38.7     109.8               --        --
    2020-01-22 00:00:00.000 214.60083333333333 -13.564722222222223 2.803 2.877       84.3  19.9 12.6         34.89     109.5               --        --
                        ...                ...                 ...   ...   ...        ...   ...  ...           ...       ...              ...       ...
    2020-12-02 00:00:00.000 252.88041666666666  -22.87638888888889 4.224 3.242        4.3   1.3 12.9         54.42      96.9               --        --
    2020-12-09 00:00:00.000 255.62041666666664 -23.159166666666664 4.235  3.25        0.5   0.1 12.8         54.31      95.9               --        --
    2020-12-16 00:00:00.000 258.36208333333326             -23.395 4.237 3.258        4.9   1.5 13.0         54.07      94.8               --        --
    2020-12-23 00:00:00.000 261.09624999999994 -23.583055555555557 4.232 3.265        9.5   2.8 13.1         53.67      93.8               --        --
    Length = 52 rows


Observer location
-----------------

Ephemerides may be calculated for Earth-based observers.  To calculate
Makemake's ephemeris for the Discovery Channel Telescope (IAU
observatory code G37):

.. code-block:: python

    >>> eph = MPC.get_ephemeris('Makemake', location='G37')
    >>> print(eph)
              Date                  RA                Dec         Delta    r    Elongation Phase  V   Proper motion Direction Azimuth Altitude Sun altitude Moon phase Moon distance Moon altitude Uncertainty 3sig Unc. P.A.
                                   deg                deg           AU     AU      deg      deg  mag    arcsec / h     deg      deg     deg        deg                      deg           deg           arcsec         deg   
    ----------------------- ------------------ ------------------ ------ ------ ---------- ----- ---- ------------- --------- ------- -------- ------------ ---------- ------------- ------------- ---------------- ---------
    2018-08-16 14:42:27.000 194.66791666666663 24.109722222222224 53.211 52.528       47.2   0.8 17.2          2.62     134.2      53       -9           23       0.33            36           -43               --        --
    2018-08-17 14:42:27.000 194.68166666666664  24.09722222222222  53.22 52.528       46.5   0.8 17.2          2.65     133.7      53       -8           23       0.43            46           -54               --        --
    2018-08-18 14:42:27.000  194.6958333333333 24.084999999999997 53.229 52.528       45.7   0.8 17.2          2.67     133.1      54       -7           22       0.53            57           -64               --        --
    2018-08-19 14:42:27.000 194.70999999999998 24.072777777777777 53.238 52.528       45.0   0.8 17.2          2.69     132.6      55       -7           22       0.63            68           -72               --        --
                        ...                ...                ...    ...    ...        ...   ...  ...           ...       ...     ...      ...          ...        ...           ...           ...              ...       ...
    2018-09-02 14:42:27.000 194.93124999999995  23.90583333333333 53.343 52.529       35.9   0.6 17.2          2.93     126.0      63        3           21       0.56           119            58               --        --
    2018-09-03 14:42:27.000 194.94874999999996 23.894166666666667 53.349 52.529       35.3   0.6 17.2          2.94     125.6      63        3           20       0.45           106            69               --        --
    2018-09-04 14:42:27.000 194.96624999999997  23.88277777777778 53.355 52.529       34.8   0.6 17.2          2.96     125.2      64        4           20       0.33            93            76               --        --
    2018-09-05 14:42:27.000 194.98374999999996  23.87138888888889  53.36 52.529       34.2   0.6 17.2          2.97     124.7      64        5           20       0.23            80            72               --        --
    Length = 21 rows

Note additional columns are returned for topocentric coordinates.

The observer location may be specified with an IAU observatory code,
an array of longitude (east), latitude, and altitude (parsed with
`~astropy.units.Quantity`), or an
`~astropy.coordinates.EarthLocation`.  For example, to compute
Encke's parallax between Mauna Kea and Botswana:

.. code-block:: python

    >>> from astropy.table import Table
    >>> from astropy.coordinates import SkyCoord
    >>> eph = MPC.get_ephemeris('2P', location='586', start='2003-11-01')
    >>> mko = SkyCoord.guess_from_table(eph)
    >>> eph = MPC.get_ephemeris('2P', location=('24d', '-22d', '1000m'), start='2003-11-01')
    >>> bw = SkyCoord.guess_from_table(eph)
    >>> mu = mko.separation(bw)
    >>> tab = Table(data=(eph['Date'], mu), names=('Date', 'Parallax'))
    >>> print(tab)
              Date                 Parallax      
                                     deg         
    ----------------------- ---------------------
    2003-11-01 00:00:00.000  0.005050002777840046
    2003-11-02 00:00:00.000  0.005439170027971742
    2003-11-03 00:00:00.000  0.005202581443927997
    2003-11-04 00:00:00.000  0.005302672506812041
                        ...                   ...
    2003-11-18 00:00:00.000  0.006954051057362872
    2003-11-19 00:00:00.000  0.007231766703916716
    2003-11-20 00:00:00.000  0.007537846117097956
    2003-11-21 00:00:00.000 0.0075389478267517745
    Length = 21 rows

    
Working with ephemeris tables
-----------------------------

Columns in the returned ephemeris tables carry the appropriate units.
Convert the columns to Astropy quantities using the ``.quantity``
attribute.  To find comet Hyakutake's peak proper motion in the sky in
degrees per hour:

.. code-block:: python

    >>> eph = MPC.get_ephemeris('C/1996 B2', start='1996-03-01', step='1h', number=30 * 24)
    >>> print(eph['Proper motion'].quantity.to('deg/h').max())
    0.7756944444444445 deg / h

Sky coordinates are returned as quantities carrying units of degrees.
If a sexagesimal representation is desired, they may be replaced with
strings using the ``ra_format`` and ``dec_format`` keyword arguments
(see ``Angle``'s `~astropy.coordinates.Angle.to_string` for formatting
options):

.. code-block:: python

    >>> eph = MPC.get_ephemeris('2P', ra_format={'sep': ':', 'unit': 'hourangle', 'precision': 1}, dec_format={'sep': ':', 'precision': 0})
    >>> print(eph)
              Date              RA       Dec    Delta   r   Elongation Phase  V   Proper motion Direction
                            hourangle    deg      AU    AU     deg      deg  mag    arcsec / h     deg   
    ----------------------- ---------- -------- ----- ----- ---------- ----- ---- ------------- ---------
    2018-08-16 14:12:18.000 22:52:30.5 -6:18:57 3.076 4.048      161.4   4.6 22.4         36.34     250.9
    2018-08-17 14:12:18.000 22:51:35.0 -6:23:43 3.072 4.049      162.6   4.3 22.4         36.67     250.9
    2018-08-18 14:12:18.000 22:50:38.9 -6:28:33 3.069  4.05      163.8   4.0 22.3         36.98     250.9
    2018-08-19 14:12:18.000 22:49:42.4 -6:33:24 3.066 4.052      165.0   3.7 22.3         37.26     250.9
                        ...        ...      ...   ...   ...        ...   ...  ...           ...       ...
    2018-09-02 14:12:18.000 22:36:03.8 -7:43:45 3.057 4.066      177.7   0.6 22.1         38.71     250.9
    2018-09-03 14:12:18.000 22:35:04.7 -7:48:48 3.059 4.067      176.5   0.9 22.1         38.62     251.0
    2018-09-04 14:12:18.000 22:34:05.8 -7:53:50 3.062 4.068      175.3   1.2 22.1         38.52     251.0
    2018-09-05 14:12:18.000 22:33:07.1 -7:58:51 3.064 4.068      174.1   1.5 22.2         38.38     251.0
    Length = 21 rows


IAU Observatory Codes and Locations
===================================

Two methods are available for working with the MPC's observatory list.
To retrieve a list of all observatories:

.. code-block:: python

    >>> obs = MPC.get_observatory_codes()
    >>> print(obs)
    Code Longitude   cos      sin                      Name                  
    ---- --------- -------- -------- ----------------------------------------
     000       0.0  0.62411  0.77873                                Greenwich
     001    0.1542  0.62992  0.77411                              Crowborough
     002      0.62    0.622    0.781                                 Rayleigh
     003       3.9    0.725    0.687                              Montpellier
     004    1.4625   0.7252  0.68627                                 Toulouse
     005     2.231 0.659891 0.748875                                   Meudon
     ...       ...      ...      ...                                      ...
     Z94  358.8565  0.62725  0.77623                                Kempshott
     Z95  358.8909  0.76782  0.63883 Astronomia Para Todos Remote Observatory
     Z96 359.19369 0.747818 0.661731                Observatorio Cesaraugusto
     Z97 359.41647 0.704568  0.70727          OPERA Observatory, Saint Palais
     Z98  359.5216  0.77156  0.63405                 Observatorio TRZ, Betera
     Z99 359.97874 0.595468 0.800687          Clixby Observatory, Cleethorpes
    Length = 2099 rows

The results are cached by default.  To update the cache, use the
``cache=False`` optional keyword:

.. code-block:: python

    >>> obs = MPC.get_observatory_codes(cache=False)

To get the location (longitude, parallax constants, and name) of a
single observatory:

.. code-block:: python

    >>> print(MPC.get_observatory_location('371'))
    (<Angle 133.5965 deg>, 0.82433, 0.56431, 'Tokyo-Okayama')

The parallax constants are ``rho * cos(phi)`` and ``rho * sin(phi)`` where
``rho`` is the geocentric distance in earth radii, and ``phi`` is the
geocentric latitude.


Observations
============

The following code snippet queries all reported observations for
asteroid 12893:

.. code-block:: python

   >>> obs = MPC.get_observations(12893)
   >>> print(obs)
   number   desig   discovery note1 ...         DEC          mag  band observatory
				    ...         deg          mag                  
   ------ --------- --------- ----- ... ------------------- ----- ---- -----------
    12893 1998 QS55        --    -- ...  -15.78888888888889   0.0   --         413
    12893 1998 QS55        --    -- ... -15.788944444444445   0.0   --         413
    12893 1998 QS55         *     4 ...   5.526472222222222   0.0   --         809
    12893 1998 QS55        --     4 ...   5.525555555555555   0.0   --         809
    12893 1998 QS55        --     4 ...   5.524805555555555   0.0   --         809
    12893 1998 QS55        --     4 ...   5.440555555555556  18.4   --         809
      ...       ...       ...   ... ...                 ...   ...  ...         ...
    12893 1998 QS55        --    -- ...            12.63075 18.53    c         T05
    12893 1998 QS55        --    -- ...   12.63088888888889 18.63    c         T05
    12893 1998 QS55        --    -- ...  12.631472222222223 18.55    c         T05
    12893 1998 QS55        --    -- ...  12.669888888888888  18.3    r         I41
    12893 1998 QS55        --    -- ...            12.71525  18.3    r         I41
    12893 1998 QS55        --    -- ...  12.716833333333334  18.2    r         I41
    12893 1998 QS55        --    -- ...  12.717527777777779  18.3    r         I41
   Length = 1401 rows

The query results of `~astroquery.mpc.MPCClass.get_observations` are parsed
into a `~astropy.table.QTable` by default; it is also possible to
output the original MPC 80-column format strings using the optional
argument ``get_mpcformat``.

The query can only be run for single targets. The target body is
identified either through an asteroid number (as int or str), a
periodic comet number (as str, e.g., ``'2P'``), a provisional asteroid
designation (as str, e.g., ``'1998 QS55'``), or a provisional comet
designation (as str, e.g., ``'P/2019 A4'``). Note that comet
identifiers have to be accompanied by a comet type identifier (``P``,
``C``, ``X``, etc.), e.g., ``'1P'``, ``'354P'``, ``'P/2019 A4'``,
``'C/1932 Y1'``. The lack of a comet type identifier may lead to a
misleading target identification or an error being raised. If the
target identifier is not parsed properly, the user can use the keyword
argument ``id_type`` to set the target type and identifier type
manually. Asteroid or comet names cannot be queried, as well as
Palomar-Leiden Survey designations, and individual comet fragments. In
case an object name cannot be resolved, a ``ValueError`` is raised. If
a query returns no results, a ``RuntimeError`` is raised.

Reference/API
=============

.. automodapi:: astroquery.mpc
    :no-inheritance-diagram:
