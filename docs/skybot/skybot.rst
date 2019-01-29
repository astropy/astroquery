.. doctest-skip-all

.. _astroquery.skybot:

******************************************************************************
IMCCE SkyBoT Queries (`astroquery.skybot`/astroquery.solarsystem.imcce.skybot)
******************************************************************************

Overview
========

IMCCE's `SkyBoT <http://vo.imcce.fr/webservices/skybot/>`_ service
provides functionality to search for and identify Solar System objects
that are present in a given area of the sky at a given time. It's
typical use case is to identify moving objects that have been
serendipitously observed.

`astroquery.skybot` provides an interface to the `cone search
<http://vo.imcce.fr/webservices/skybot/?conesearch>`_ offered by SkyBoT.

Cone Search
===========

A simple cone search for Solar System objects in a circular field
looks like this:

.. code-block:: python
	  
   >>> from astroquery.skybot import Skybot
   >>> Skybot.cone_search((0, 0), 0.1, 2451200)  # doctest: +SKIP
   <QTable length=6>
   Number    Name            RA          ...      vy          vz       epoch  
			    deg          ...    AU / d      AU / d       d    
   int64     str9         float64        ...   float64     float64    float64 
   ------ --------- -------------------- ... ----------- ----------- ---------
   299383 2005 VC73   359.94077541666667 ... 0.010886508 0.003535381 2451200.0
   518441  2004 FC6 0.048321666666666666 ... 0.006622583 0.004266802 2451200.0
   395111 2009 VC31   359.97290749999996 ... 0.008183291 0.004832045 2451200.0
   192116  2006 DM9         359.91487125 ...  0.00767636 0.005744082 2451200.0
   239169 2006 KT47  0.09837624999999998 ... 0.009238599  0.00336863 2451200.0
   359191 2009 CD65  0.09119958333333332 ... 0.009023276 0.001463182 2451200.0

`~astroquery.skybot.SkybotClass.cone_search` produces a
`~astropy.table.QTable` object with the properties of all Solar System
bodies that are present in the cone at the given epoch. 
   
The required input arguments for
`~astroquery.skybot.SkybotClass.cone_search` are the center coordinates of
the cone, its radius, as well as the epoch of the
observation. Coordinates ``coo`` can be provided as
`~astropy.coordinates.SkyCoord` object, or as a tuple; in the latter
case, the tuple has to consist of two floats that refer to RA and
declination in degrees (all coordinates are given in J2000.0). The
radius of the cone ``rad`` has to be provided either as an
`~astropy.coordinates.Angle` object, or as a float using degrees as
units. Note that the maximum cone radius is limited to 10 degrees by
the SkyBoT service. The ``epoch`` of the observation has to be
provided as `~astropy.time.Time` object, int, or str; integer values
are assumed to be Julian Dates, string values are assumed to be
datetimes provided in ISO format (YYYY-MM-DD HH:MM:SS).

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


Acknowledgements
================

This submodule makes use of IMCCE's `SkyBoT
<http://vo.imcce.fr/webservices/skybot/>`_ VO tool. Additional
information on SkyBoT can be obtained from `Berthier et al. 2006
<http://adsabs.harvard.edu/abs/2006ASPC..351..367B>`_.

Please consider this note from the SkyBot maintainers: If SkyBoT was
helpful for your research work, the following acknowledgment would be
appreciated: "This research has made use of IMCCE's SkyBoT VO tool",
or cite the following article `2006ASPC..351..367B
<http://adsabs.harvard.edu/abs/2006ASPC..351..367B>`_.

The development of this submodule is funded through NASA PDART Grant
No. 80NSSC18K0987 to the `sbpy project <http://sbpy.org>`_.

     
Reference/API
=============

.. automodapi:: astroquery.skybot
    :no-inheritance-diagram:

