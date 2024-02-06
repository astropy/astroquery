
.. _astroquery.esa.neocc:

***********************************************************************************************
ESA NEOCC Portal Python Interface Library (`astroquery.esa.neocc`/astroquery.solarsystem.neocc)
***********************************************************************************************

The ESA NEO Coordination Centre (NEOCC) is the operational centre of ESA’s Planetary Defence Office
PDO) within the Space Safety Programme (S2P). Its aim is to coordinate and contribute to the
observation of small Solar System bodies in order to evaluate and monitor the threat coming from 
near-Earth objects (NEOs).

ESA NEOCC Portal Python interface library makes the data that `ESA NEOCC <https://neo.ssa.esa.int/>`_
provides easily accessible through a Python program.

The main functionality of this library is to allow a programmer to easily retrieve:

* All the NEAs
* Other data that the NEOCC provides (risk list, close approach list, etc.)
* All basic and advanced information regarding a NEA
* An ephemeris service for NEAs

============================
Getting ESA NEOCC's products
============================

--------------------------------
1. Direct download of list files
--------------------------------

This function allows the user to download the requested list data from ESA NEOCC.
Different lists that can be requested are:

* All NEA list: ``nea_list``
* Catalogue of NEAs (current date): ``neo_catalogue_current``
* Catalogue of NEAs (middle arc): ``neo_catalogue_middle``
* Updated NEA list: ``updated_nea``
* Monthly computation date: ``monthly_update``
* Risk list (normal): ``risk_list``
* Risk list (special): ``risk_list_special``
* Close approaches (upcoming): ``close_approaches_upcoming``
* Close approaches (recent): ``close_approaches_recent``
* Priority list (normal): ``priority_list``
* Priority list (faint): ``priority_list_faint``
* Close encounter list: ``close_encounter``
* Impacted objects: ``impacted_objects``
 
These lists are referenced in `<https://neo.ssa.esa.int/computer-access>`_.

--------
Examples
--------

NEA list
^^^^^^^^

The output of this list is a `~astropy.table.Table` which contains the list of all NEAs
currently considered in the NEOCC system.

.. doctest-remote-data::

    >>> from astroquery.esa.neocc import neocc
    >>> list_data = neocc.query_list(list_name='nea_list')
    >>> print(list_data)  # doctest: +IGNORE_OUTPUT
        NEA     
    ------------
        433 Eros
      719 Albert
      887 Alinda
    1036 Ganymed
       1221 Amor
             ...
          2023RJ
          2023RK
          2023RL
          2023RM
          6344P-L
    Length = 32564 rows


Each asteroid can be accessed using its index. This information can
be used as input for :meth:`~astroquery.esa.neocc.NEOCCClass.query_object` method.

.. doctest-remote-data::

    >>> print(list_data["NEA"][4])
    1221 Amor

Close approaches
^^^^^^^^^^^^^^^^

The output of this list is a `~astropy.table.Table` which
contains information about asteroid close approaches.

.. doctest-remote-data::

    >>> from astroquery.esa.neocc import neocc
    >>> list_data = neocc.query_list(list_name='close_approaches_upcoming')
    >>> print(list_data)  # doctest: +IGNORE_OUTPUT
    Object Name           Date          ... Rel. vel in km/s CAI index
    ----------- ----------------------- ... ---------------- ---------
        2021JA5 2023-09-07 00:00:00.000 ...             11.0     3.496
        2023QC5 2023-09-08 00:00:00.000 ...              7.6     2.662
         2020GE 2023-09-08 00:00:00.000 ...              1.4     3.308
         2023RH 2023-09-08 00:00:00.000 ...             19.1     2.114
         2023RG 2023-09-08 00:00:00.000 ...             12.5     3.242
            ...                     ... ...              ...       ...
       2012SX49 2024-08-29 00:00:00.000 ...              4.3     2.665
       2016RJ20 2024-08-30 00:00:00.000 ...             14.8     2.118
         2021JT 2024-09-02 00:00:00.000 ...              8.3     4.216
       2021RB16 2024-09-02 00:00:00.000 ...              8.5     3.685
        2007RX8 2024-09-02 00:00:00.000 ...              7.0     2.322
    Length = 182 rows


**Note:** If the contents request fails the following message will be printed:

*Initial attempt to obtain list failed. Reattempting...*

Then a second request will be automatically sent to the NEOCC portal.

---------------------------------------
2. Direct download of data on an object
---------------------------------------

This function allows the user to download the requested data tabe for a designated object.
The list of data properties that can be requested is:

* Asteroid orbit properties: ``orbit_properties``
* Asteroid physical properties: ``physical_properties``
* Asteroid observation records: ``observations``
* Generation of observational ephemerides for an object: ``ephemerides``
* Asteroid close approach report: ``close_approaches``
* Possible impacts: ``impacts``

These properties are referenced in `<https://neo.ssa.esa.int/computer-access>`_.

--------
Examples
--------

Impacts, Physical Properties and Observations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This example tries to summarize how to access the data of this tabs and how to
use it. Note that this classes only require as inputs the name of
the object and the requested tab.

The information can be obtained introducing directly the name of
the object, but it can be also added from the output of a
:meth:`~astroquery.esa.neocc.NEOCCClass.query_list` search:

.. doctest-remote-data::

    >>> from astroquery.esa.neocc import neocc
    >>> ast_impacts = neocc.query_object(name='1979XB', tab='impacts')

or

.. doctest-remote-data::

    >>> nea_list = neocc.query_list(list_name='nea_list')
    >>> print(nea_list["NEA"][3163])
    1979XB
    >>> ast_impacts = neocc.query_object(name=nea_list["NEA"][3163], tab='impacts')

or

.. doctest-remote-data::

    >>> risk_list = neocc.query_list(list_name='risk_list')
    >>> print(risk_list['Object Name'][1])
    1979XB
    >>> ast_impacts = neocc.query_object(name=risk_list['Object Name'][1], tab='impacts')

This query returns a list containing a single table:

.. doctest-remote-data::

    >>> print(ast_impacts[0])  # doctest: +IGNORE_OUTPUT
              date             MJD    sigma  sigimp ... Exp. Energy in MT   PS   TS
    ----------------------- --------- ------ ------ ... ----------------- ----- ---
    2056-12-12 21:38:52.800 72344.902  0.255    0.0 ...             0.013 -2.86   0
    2065-12-16 11:06:43.200 75635.463  -1.11    0.0 ...           3.3e-05 -5.42   0
    2101-12-14 04:53:45.600 88781.204 -0.384    0.0 ...           8.6e-05 -5.32   0
    2113-12-14 18:04:19.200 93164.753 -0.706    0.0 ...           0.00879 -3.35   0


**Note:** Most of the tables returned by this tye of query contain additional information
in the ``meta`` property, including information about the table columns.

.. doctest-remote-data::
   
   >>> print(ast_impacts[0].meta.keys())
   odict_keys(['Column Info', 'observation_accepted', 'observation_rejected', 'arc_start', 'arc_end', 'info', 'computation'])


Physical Properties
^^^^^^^^^^^^^^^^^^^

This example shows how to obtain the physical properties table.

.. doctest-remote-data::

    >>> from astroquery.esa.neocc import neocc
    >>> properties = neocc.query_object(name='433', tab='physical_properties')

 Again, the output is a list containing a single table.

.. doctest-remote-data::

    >>> print(properties[0])  # doctest: +IGNORE_OUTPUT
            Property        ...
    ----------------------- ...
     Absolute Magnitude (H) ...
     Absolute Magnitude (H) ...
                     Albedo ...
                  Amplitude ...
    Color Index Information ...
    Color Index Information ...
    Color Index Information ...
    Color Index Information ...
                   Diameter ...
                    Quality ...
         Rotation Direction ...
            Rotation Period ...
                  Sightings ...
                  Sightings ...
        Slope Parameter (G) ...
               Spinvector B ...
               Spinvector L ...
                   Taxonomy ...
             Taxonomy (all) ...


Observations
^^^^^^^^^^^^

In this example we query for Observations tables, a query that
returns a list containing 3-5 `~astropy.table.Table` objects depending if there are
"Roving observer" or satellite observations.


.. doctest-remote-data::

    >>> ast_observations = neocc.query_object(name='99942', tab='observations')
    >>> for tab in ast_observations:
    ...     print(tab.meta["Title"])
    Observation metadata
    Optical Observations
    Satellite  Observations
    Radar Observations
    >>> sat_obs = ast_observations[2]
    >>> print(sat_obs)  # doctest: +IGNORE_OUTPUT
    Design.  K   T   N  ...     X              Y                 Z          Obs Code
    ------- --- --- --- ... ---------- ----------------- ------------------ --------
      99942   S   s  -- ... -5634.1734        -2466.2657         -3038.3924      C51
      99942   S   s  -- ... -5654.1816        -2501.9465         -2971.1902      C51
      99942   S   s  -- ... -5645.7831        -2512.1036         -2978.6411      C51
      99942   S   s  -- ... -5617.3465        -2486.4031         -3053.2209      C51
      99942   S   s  -- ... -5620.3829        -2542.3521         -3001.1135      C51
        ... ... ... ... ...        ...               ...                ...      ...
      99942   S   s  -- ... -4105.3228 5345.915299999999          1235.1318      C51
      99942   S   s  -- ... -4117.8192         5343.1834          1205.2107      C51
      99942   S   s  -- ... -4137.4411         5329.7318          1197.3972      C51
      99942   S   s  -- ... -4144.5939 5319.084499999999          1219.4675      C51
    Length = 1357 rows

Close Approaches
^^^^^^^^^^^^^^^^

This example queris for close approaches, another query
which results in a single data table.

.. doctest-remote-data::

    >>> close_appr = neocc.query_object(name='99942', tab='close_approaches')
    >>> print(close_appr[0])  # doctest: +IGNORE_OUTPUT
    BODY      CALENDAR-TIME          MJD-TIME    ...  STRETCH    WIDTH   PROBABILITY
    ----- ----------------------- --------------- ... --------- --------- -----------
    EARTH 1957-04-01T03:19:44.544 35929.138710654 ... 2.871e-05 5.533e-09         1.0
    EARTH 1964-10-24T21:44:40.127 38692.906017295 ...  1.72e-05 5.033e-09         1.0
    EARTH 1965-02-11T12:15:30.527 38802.510774301 ... 4.732e-06 1.272e-09         1.0
    EARTH 1972-12-24T11:51:41.472 41675.494228687 ... 1.584e-05 4.627e-09         1.0
    EARTH 1980-12-18T01:51:14.400 44591.077250448 ... 1.136e-05 5.436e-09         1.0
      ...                     ...             ... ...       ...       ...         ...
    EARTH 2087-04-07T09:10:54.912 83417.382583343 ...   0.01214 3.978e-08         1.0
    EARTH 2102-09-11T03:12:44.640 89052.133849042 ...   0.08822 1.191e-06       0.751
    EARTH 2109-03-22T13:19:55.200 91436.555501683 ...    0.3509 1.066e-06       0.189
    EARTH 2109-06-08T14:21:12.384 91514.598061046 ...    0.1121 1.149e-06       0.577
    EARTH 2116-04-07T12:48:42.912  94009.53382919 ...    0.7074 9.723e-08      0.0943
    [18 rows x 10 columns]

Orbit Properties
^^^^^^^^^^^^^^^^

In order to access the orbital properties
information, it is necessary to provide two additional inputs to
:meth:`~astroquery.esa.neocc.NEOCCClass.query_object` method: ``orbital_elements`` and ``orbit_epoch``.

This query returns a list of three tables, the orbital properties, and the covariance
and corotation matrices.

.. doctest-remote-data::

    >>> ast_orbit_prop = neocc.query_object(name='99942', tab='orbit_properties',
    ...                                     orbital_elements='keplerian', orbit_epoch='present')
    >>> for tab in ast_orbit_prop:
    ...     print(tab.meta["Title"])
    Orbital Elements
    COV
    COR
    >>> print(ast_orbit_prop[0][:5])  # doctest: +IGNORE_OUTPUT
    Section  Property          Value
    -------- -------- -----------------------
       ANODE    ANODE -8.6707715058413322E-04
    APHELION APHELION  1.0993687643243035E+00
       DNODE    DNODE -1.9894296321957006E-01
      HEADER   format                  OEF2.0
      HEADER  rectype                      ML


Ephemerides
^^^^^^^^^^^
In order to access ephemerides information, it
is necessary to provide five additional inputs to :meth:`~astroquery.esa.neocc.NEOCCClass.query_object`
method: ``observatory``, ``start``, ``stop``, ``step`` and ``step_unit``.

.. doctest-remote-data::

    >>> ast_ephemerides = neocc.query_object(name='99942', tab='ephemerides', observatory='500',
    ...                                      start='2019-05-08 01:30', stop='2019-05-23 01:30',
    ...                                      step='1', step_unit='days')
    >>> ast_ephemerides = ast_ephemerides[0]
    >>> print(ast_ephemerides.meta.keys())
    odict_keys(['Ephemerides generation for', 'Observatory', 'Initial Date', 'Final Date', 'Time step', 'Column Info'])
    >>> print(ast_ephemerides)  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
               Date          MJD (UTC)  RA (h  m  s) ... Err1 (") Err2 (") AngAx (deg)
    ----------------------- ---------- ------------ ... -------- -------- -----------
    2019-05-08T01:30:00.000 58611.0625  6 43 40.510 ...    0.001      0.0       115.8
    2019-05-09T01:30:00.000 58612.0625  6 47 20.055 ...    0.001      0.0       117.3
    2019-05-10T01:30:00.000 58613.0625  6 50 59.059 ...    0.001      0.0       119.0
    2019-05-11T01:30:00.000 58614.0625  6 54 37.518 ...    0.001      0.0       120.8
    2019-05-12T01:30:00.000 58615.0625  6 58 15.428 ...    0.001      0.0       122.8
                        ...        ...          ... ...      ...      ...         ...
    2019-05-19T01:30:00.000 58622.0625  7 23 25.375 ...    0.001      0.0       143.8
    2019-05-20T01:30:00.000 58623.0625  7 26 58.899 ...    0.001      0.0       147.6
    2019-05-21T01:30:00.000 58624.0625  7 30 31.891 ...    0.001      0.0       151.5
    2019-05-22T01:30:00.000 58625.0625  7 34  4.357 ...    0.001    0.001       155.2
    2019-05-23T01:30:00.000 58626.0625  7 37 36.303 ...    0.001    0.001       158.7



Reference/API
=============

.. automodapi:: astroquery.esa.neocc
    :no-inheritance-diagram:
