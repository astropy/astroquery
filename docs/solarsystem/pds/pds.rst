.. _astroquery.solarsystem.pds:

***********************************************************************************
PDS Ring-Moon Systems (RMS) Node Queries (`astroquery.solarsystem.pds`)
***********************************************************************************

Overview
========


The :class:`~astroquery.solarsystem.pds.RMSNodeClass` provides an
interface to the ephemeris tools provided by the `NASA Planetary Data System's Ring-Moon Systems (RMS) Node <https://pds-rings.seti.org/>`_ hosted by the SETI institute.


Ephemeris
-----------

In order to query information for a specific Solar System body, a
``RMSNode`` object is instantiated and the :meth:`~astroquery.solarsystem.pds.RMSNodeClass.ephemeris` method is called. The following example queries the
ephemerides of the rings and small moons around Uranus as viewed from ALMA:

.. doctest-remote-data::

   >>> from astroquery.solarsystem.pds import RMSNode
   >>> import astropy.units as u
   >>> bodytable, ringtable = RMSNode.ephemeris(planet='Uranus',
   ...                 epoch='2024-05-08 22:39',
   ...                 location = (-67.755 * u.deg, -23.029 * u.deg, 5000 * u.m))
   >>> print(ringtable)
         ring  pericenter ascending node
                  deg          deg
       ------- ---------- --------------
           Six    293.129           52.0
          Five    109.438           81.1
          Four    242.882           66.9
         Alpha    184.498          253.9
          Beta     287.66          299.2
           Eta        0.0            0.0
         Gamma     50.224            0.0
         Delta        0.0            0.0
        Lambda        0.0            0.0
       Epsilon    298.022            0.0

``planet`` must be one of ['mars', 'jupiter', 'uranus', 'saturn', 'neptune', 'pluto'] (case-insensitive)


.. doctest-remote-data::

   >>> bodytable, ringtable = RMSNode.ephemeris(planet='Venus',
   ...                 epoch='2024-05-08 22:39',
   ...                 location = (-67.755 * u.deg, -23.029 * u.deg, 5000 * u.m))
   Traceback (most recent call last):
   ...
   ValueError: illegal value for 'planet' parameter (must be 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', or 'Pluto')

``epoch`` is the datetime to query. Accepts a string in format 'YYYY-MM-DD HH:MM' (UTC assumed), or a `~astropy.time.Time` object. If no epoch is provided, the current time is used.

``location`` is the observer's location. Accepts an `~astropy.coordinates.EarthLocation`, or any 3-element array-like (e.g. list, tuple) of format (longitude, latitude, elevation). Longitude and latitude should be anything that initializes an `~astropy.coordinates.Angle` object, and altitude should initialize a `~astropy.units.Quantity` object (with units of length).  If ``None``, then the geocenter is used.

``neptune_arcmodel`` is the choice of which ephemeris to assume for Neptune's ring arcs. accepts a float. must be one of 1, 2, or 3 (see https://pds-rings.seti.org/tools/viewer3_nep.shtml for details). default 3. has no effect if planet != 'Neptune'

Outputs
---------
``bodytable`` is a `~astropy.table.QTable` containing ephemeris information on the moons in the planetary system. Every column is assigned a unit from `~astropy.units`. We can get a list of all the columns in this table with:


.. doctest-remote-data::

	>>> print(bodytable.columns)
	<TableColumns names=('NAIF ID','Body','RA','Dec','RA (deg)','Dec (deg)','dRA','dDec','sub_obs_lon','sub_obs_lat','sub_sun_lon','sub_sun_lat','phase','distance')>

``ringtable`` is a `~astropy.table.QTable` containing ephemeris information on the individual rings in the planetary system. Every column is assigned a unit from `~astropy.units`. We can get a list of all the columns in this table with:


.. doctest-remote-data::

	>>> print(ringtable.columns)
	<TableColumns names=('ring','pericenter','ascending node')>

Note that the behavior of ``ringtable`` changes depending on the planet you query. For Uranus and Saturn the table columns are as above. For Jupiter, Mars, and Pluto, there are no individual named rings returned by the RMS Node, so ``ringtable`` returns None; ephemeris for the ring systems of these bodies is still contained in ``systemtable`` as usual. For Neptune, the ring table shows the minimum and maximum longitudes (from the ring plane ascending node) of the five ring arcs according to the orbital evolution assumed by ``neptune_arcmodel``, e.g.:


.. doctest-remote-data::

	>>> bodytable, ringtable = RMSNode.ephemeris(planet='Neptune', epoch='2022-05-24 00:00')
	>>> print(ringtable)
    	   ring    min_angle max_angle
    	              deg       deg
    	---------- --------- ---------
    	   Courage   53.4818   54.4818
    	   Liberte  44.68181  48.78178
    	 Egalite A  33.88179  34.88179
    	 Egalite B   30.0818   33.0818
    	Fraternite   16.0818  25.68181

System-wide data are available as metadata in both ``bodytable`` and ``ringtable`` (if ``ringtable`` exists), e.g.:

.. doctest-remote-data::

	>>> systemtable = bodytable.meta
	>>> print(systemtable.keys())
	dict_keys(['sub_sun_lat', 'sub_sun_lat_min', 'sub_sun_lat_max', 'opening_angle', 'phase_angle', 'sub_sun_lon', 'sub_obs_lon', 'd_sun', 'd_obs', 'light_time', 'epoch'])


Reference/API
=============

.. automodapi:: astroquery.solarsystem.pds
    :no-inheritance-diagram:
