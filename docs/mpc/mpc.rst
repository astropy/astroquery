.. doctest-skip-all

.. _astroquery.mpc:

**********************************************
Minor Planet Center Queries (`astroquery.mpc`)
**********************************************

Getting started
===============

This is an Astroquery wrapper for querying services at the IAU Minor
Planet Center (MPC).  Two services are available:

    - `MPC Web Service
      <https://minorplanetcenter.net/web_service/>`__ for comet and
      asteroid orbits and parameters
    - `Minor Planet Ephemeris Service
      <https://www.minorplanetcenter.net/iau/MPEph/MPEph.html>`__ for
      comet and asteroid ephemerides

In addition, the module provides access to the MPC's hosted list of
`IAU Observatory Codes
<https://www.minorplanetcenter.net/iau/lists/ObsCodesF.html>`__.


Asteroid and comet orbits and parameters
----------------------------------------

Queries with varying forms of selection parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Individual objects can be found with `MPC.query_object`, and
`MPC.query_objects` can return multiple objects.  Parameters can
be queried in three manners:
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

Sorting results, setting limits, and ```is_not_null```
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MPC web service allows a consumer to sort results in order to find
a number of objects fitting into the top or bottom of a range of
values (or all, if truly desired).

The service also allows a consumer to limit their results to a number
of objects, which, when paired with sorting, creates very flexible
options.

.. code-block:: python

    >>> result = MPC.query_objects('asteroid', order_by_desc="semimajor_axis", limit=10)

This will return the 10 furthest asteroids.

There is another parameter that can be used, ```is_not_null```. This
can be used in the following fashion:

.. code-block:: python

    >>> result = MPC.query_objects('asteroid', name="is_not_null")

This will, predictably, find all named objects in the MPC
database--but that would take a while!

Customizing return fields
^^^^^^^^^^^^^^^^^^^^^^^^^

If a consumer isn't interested in some return fields, they can use the
MPC to limit the fields they're interested in.

.. code-block:: python

    >>> result = MPC.query_object('asteroid', name="ceres", return_fields="name,number")
    >>> print(result)
    [{'name': 'Ceres', 'number': 1}]


Comet and asteroid ephemerides
------------------------------

Comet and asteroid ephemerides can be generated using the `Minor
Planet Ephemeris Service
<https://www.minorplanetcenter.net/iau/MPEph/MPEph.html>`__ (MPES).
The MPES supports queries for any comet or asteroid by name,
designation, or packed designation, and any Earth-based location.
Ephemerides are computed starting on a specific date, then for
equally-spaced intervals thereafter.  The ephemeris is returned as an
Astropy `~astropy.table.Table`.

Dates and intervals
^^^^^^^^^^^^^^^^^^^

For the ephemeris of asteroid (24) Themis, starting today with the
default time step (1 day) and location (geocenter):

.. code-bock:: python

    >>> from astroquery.mpc import MPC
    >>> eph = MPC.get_ephemeris('24')
    >>> print(eph)
              Date                  RA               Dec         Delta   r   Elongation Phase  V   Proper motion Direction Uncertainty 3sig Unc. P.A.
                                hourangle            deg           AU    AU     deg      deg  mag    arcsec / h     deg         arcsec         deg   
    ----------------------- ----------------- ------------------ ----- ----- ---------- ----- ---- ------------- --------- ---------------- ---------
    2018-08-16 12:44:41.000 6.429166666666667 23.750833333333333 3.503 2.916       47.5  14.8 12.9         53.09      92.1               --        --
    2018-08-17 12:44:41.000 6.454888888888889 23.737222222222222 3.492 2.915       48.1  15.0 12.9         52.92      92.2               --        --
    2018-08-18 12:44:41.000 6.480527777777778 23.723055555555554 3.481 2.914       48.7  15.1 12.9         52.75      92.4               --        --
    2018-08-19 12:44:41.000 6.506055555555555 23.708055555555553  3.47 2.913       49.3  15.3 12.9         52.57      92.5               --        --
                        ...               ...                ...   ...   ...        ...   ...  ...           ...       ...              ...       ...
    2018-09-02 12:44:41.000 6.853027777777777  23.41444444444444 3.303 2.898       58.0  17.2 12.8         49.71      94.5               --        --
    2018-09-03 12:44:41.000 6.876972222222222 23.388055555555557  3.29 2.897       58.7  17.3 12.8         49.47      94.6               --        --
    2018-09-04 12:44:41.000 6.900805555555556  23.36138888888889 3.278 2.896       59.3  17.4 12.8         49.23      94.7               --        --
    2018-09-05 12:44:41.000 6.924472222222223 23.333888888888886 3.265 2.895       59.9  17.5 12.8         48.98      94.9               --        --
    Length = 21 rows

Step sizes are parsed with Astropy's `~astropy.unit.Quantity`.  For a time step of 1 hour:

.. code-bock:: python

    >>> eph = MPC.get_ephemeris('24', step='1h')
    >>> print(eph)
              Date                  RA               Dec         Delta   r   Elongation Phase  V   Proper motion Direction Uncertainty 3sig Unc. P.A.
                                hourangle            deg           AU    AU     deg      deg  mag    arcsec / h     deg         arcsec         deg   
    ----------------------- ----------------- ------------------ ----- ----- ---------- ----- ---- ------------- --------- ---------------- ---------
    2018-08-16 12:00:00.000  6.42838888888889  23.75111111111111 3.504 2.916       47.5  14.8 12.9          53.1      92.1               --        --
    2018-08-16 13:00:00.000 6.429444444444445 23.750555555555554 3.503 2.916       47.5  14.8 12.9         53.09      92.1               --        --
    2018-08-16 14:00:00.000 6.430527777777778              23.75 3.503 2.916       47.5  14.8 12.9         53.09      92.1               --        --
    2018-08-16 15:00:00.000 6.431583333333333 23.749444444444446 3.502 2.916       47.5  14.8 12.9         53.08      92.1               --        --
                        ...               ...                ...   ...   ...        ...   ...  ...           ...       ...              ...       ...
    2018-08-18 09:00:00.000 6.476527777777778 23.725277777777777 3.483 2.914       48.6  15.1 12.9         52.78      92.4               --        --
    2018-08-18 10:00:00.000 6.477611111111111  23.72472222222222 3.482 2.914       48.6  15.1 12.9         52.77      92.4               --        --
    2018-08-18 11:00:00.000 6.478666666666666 23.724166666666665 3.482 2.914       48.6  15.1 12.9         52.76      92.4               --        --
    2018-08-18 12:00:00.000 6.479722222222223 23.723611111111108 3.481 2.914       48.7  15.1 12.9         52.76      92.4               --        --
    Length = 49 rows

Start dates are parsed with Astropy's `~astropy.time.Time`.  For a
weekly ephemeris in 2020:

.. code-bock:: python

    >>> eph = MPC.get_ephemeris('24', start='2020-01-01', step='7d', number=52)
    >>> print(eph)
              Date                  RA                 Dec         Delta   r   Elongation Phase  V   Proper motion Direction Uncertainty 3sig Unc. P.A.
                                hourangle              deg           AU    AU     deg      deg  mag    arcsec / h     deg         arcsec         deg   
    ----------------------- ------------------ ------------------- ----- ----- ---------- ----- ---- ------------- --------- ---------------- ---------
    2020-01-01 00:00:00.000            13.9445  -11.63361111111111 3.066 2.856       68.5  18.7 12.7         45.15     110.6               --        --
    2020-01-08 00:00:00.000 14.074666666666666 -12.342500000000001  2.98 2.863       73.6  19.2 12.7         42.09     110.2               --        --
    2020-01-15 00:00:00.000 14.195833333333333 -12.987222222222222 2.892  2.87       78.9  19.7 12.6          38.7     109.8               --        --
    2020-01-22 00:00:00.000 14.306722222222223 -13.564722222222223 2.803 2.877       84.3  19.9 12.6         34.89     109.5               --        --
                        ...                ...                 ...   ...   ...        ...   ...  ...           ...       ...              ...       ...
    2020-12-02 00:00:00.000 16.858694444444446  -22.87638888888889 4.224 3.242        4.3   1.3 12.9         54.42      96.9               --        --
    2020-12-09 00:00:00.000  17.04136111111111 -23.159166666666664 4.235  3.25        0.5   0.1 12.8         54.31      95.9               --        --
    2020-12-16 00:00:00.000 17.224138888888888             -23.395 4.237 3.258        4.9   1.5 13.0         54.07      94.8               --        --
    2020-12-23 00:00:00.000 17.406416666666665 -23.583055555555557 4.232 3.265        9.5   2.8 13.1         53.67      93.8               --        --

    
Working with ephemeris tables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Columns in the returned ephemeris tables carry the appropriate units.
Convert the columns to Astropy quantities using the `.quantity`
attribute.  To find comet Hyakutake's peak proper motion in the sky in
degrees per hour:

.. code-bock:: python

    >>> eph = MPC.get_ephemeris('C/1996 B2', start='1996-03-01', step='1h', number=30 * 24, proper_motion_unit='deg/h')
    >>> print(eph['Proper motion'].quantity.max())
    0.7756944444444445 deg / h

Sky coordinates are returned as RA and Dec in decimal format by
default.  If a sexagesimal representation is desired, the columns must
be converted to strings:

.. code-bock:: python

    >>> eph = MPC.get_ephemeris('2P')
    >>> eph['RA Dec'] = 



IAU Observatory Codes
---------------------


Reference/API
=============

.. automodapi:: astroquery.mpc
    :no-inheritance-diagram:
