.. _astroquery.ipac.irsa.most:

**********************************************************
IRSA Moving Object Search Tool (astroquery.ipac.irsa.most)
**********************************************************

Moving Object Search Tool (MOST) can determine the orbit for a given solar system
object then find images that covered the object's predicted positions in select
image datasets housed at IRSA. It can serve as a "precovery" tool to see if
newly discovered objects were previously observed.

The URL of the Most interface is:

 https://irsa.ipac.caltech.edu/applications/MOST

Input Modes
===========

The service accepts several different input modes:
 - Solar System Object Name Input (``"name_input"``)
 - Solar System Object NAIF ID Input (``"naifid_input"``)
 - MPC One-Line Element Input (``"mpc_input"``)
 - Orbital Elements Manual Input (``"manual_input"``)

Name resolution and ephemeris generation for known objects is done via query to
JPL's Horizon database whenever possible. This lookup can fail when name
ambiguities exist. For example, entering "Neptune" is unclear because ephemeris
for both Neptune and Neptune system barycenter exist.

Most will deliver a messsage if there is an ambiguity. The message may contain
suggested NAIF ID's, e.g. "899:NID" for Neptune.

NAIF ID's are considered valid input. Satellites and asteroids with the same
name may be distinguished by, e.g. "Europa:SAT" and "Europa:AST".

The ephemeris can also be calculated for comets or asteroids using orbital
elements supplied by the user, either individually or in the `Minor Planet
Center (MPC) one-line format
<https://irsa.ipac.caltech.edu/applications/Gator/GatorAid/irsa/moving.html>`_.

Depending on what input mode Most is being queried as, the list of required
parameters will change.

Output Modes
============

The service accepts several different output modes:
 - ``Regular`` - default
 - ``Full``
 - ``Brief``
 - ``VOTable``
 - ``Gator``

The :meth:`~astroquery.ipac.irsa.most.MostClass.query_object` method will
return different objects depending on the specified output mode.

=========================== ==================================================
Output mode                 Returned object
=========================== ==================================================
``"Regular"`` or ``"Full"`` Dictionary containing ``results``, ``metadata``
                            and ``region`` keys. Optionally also
                            ``fits_tarball`` and ``region_tarball``.
``"Brief"`` or ``"Gator"``  :class:`~astropy.table.Table` object.
``"VOTable"``               :class:`~astropy.io.votable.tree.VOTableFile`
                            object.
=========================== ==================================================

.. note::
    The difference between ``Regular`` and ``Full`` output mode is non-existant
    as the returned data in both cases is identical, as the figures created in
    ``Full`` mode are not downloaded. The difference between the two modes are
    mainly visible in presentation of the data when Most is used via their
    online interface. It is, therefore, recommended ``Regular`` because the
    query will complete significantly faster.

Regular and Full
________________

In ``"Regular"`` or ``"Full"`` output mode :meth:`~astroquery.ipac.irsa.most.MostClass.query_object`
returns a dictionary containing ``results``, ``metadata`` and ``region`` keys.

The ``results`` key contains a table that maps to the results table returned by
Most service titled ``Images with a Matched Object Position``. The table
contains the following columns:

============   ===============================================================
Column 	       Description
============   ===============================================================
Image_ID       A unique identifier for the image data, not necessarily the
               image file name.
date_obs       Date (UTC) of the observation.
time_obs       Time (UTC) of the midpoint of the observation.
mjd_obs        Modified Julian Date (days) of the midpoint of the observation.
ra_obj         Ephemeris of the object's right ascension (deg, J2000).
dec_obj        Ephemeris of the object's declination (deg, J2000).
sun_dist       Heliocentric distance of the object (AU).
geo_dist       Geocentric distance of the object (AU).
dist_ctr       Projected distance  from the center of the image (deg).
phase          Sun-Object-earth angle (deg).
vmag           Estimate of visual magnitude (from Horizons).
image_url      Links to download or view the data.
postcard_url   Currently ``null``.  It is waiting for a future dataset that may have a png along with the image.
region_file    Markers for the moving object in DS9 "region" format.
============   ===============================================================

The ``metadata`` key contains a table which columns change depending on what
catalog (instrument) was queried. Only a small set of columns are guaranteed to
always be present. The following table lays out which columns can be expected
to be present for a given instrument/observatory:

+---------------------+-------------------------------------------------------+
| Column              | Description                                           |
+=====================+=======================================================+
| .. centered:: **General**                                                   |
+---------------------+-------------------------------------------------------+
| ra1, dec1,          | Right ascension and declination of the 4 corners of   |
| ra2, dec2, etc.     | the image (deg, J2000)                                |
+---------------------+-------------------------------------------------------+
| match               | match = 1 indicates a matched image (added by Most)   |
+---------------------+-------------------------------------------------------+
| .. centered:: **WISE/NEOWISE**                                              |
+---------------------+-------------------------------------------------------+
| crpix1, crpix2      | Center of image (pixels)                              |
+---------------------+-------------------------------------------------------+
| crval1, crval2      | Center of image (deg, J2000)                          |
+---------------------+-------------------------------------------------------+
| equinox             | Equinox of coordinates                                |
+---------------------+-------------------------------------------------------+
| band                | WISE band number; 1 (3.4 microns), 2 (4.6 microns),   |
|                     | 3 (12 microns), 4 (22 microns)                        |
+---------------------+-------------------------------------------------------+
| scan_id             | Identification of pole-to-pole orbit scan             |
+---------------------+-------------------------------------------------------+
| date_obs            | Date and time of mid-point of frame observation UTC   |
+---------------------+-------------------------------------------------------+
| mjd_obs             | MJD of mid-point of frame observation UTC             |
+---------------------+-------------------------------------------------------+
| dtanneal            | Elapsed time in seconds since the last anneal         |
+---------------------+-------------------------------------------------------+
| moon_sep            | Angular distance from the frame center to the Moon (°)|
+---------------------+-------------------------------------------------------+
| saa_sep             | Angular distance from the frame center to South       |
|                     | Atlantic Anomaly (SAA) boundary (deg)                 |
+---------------------+-------------------------------------------------------+
| qual_frame          | This integer indicates the quality score value for    |
|                     | the Single-exposure image frameset, with values of 0  |
|                     | (poor| quality), 5, or 10 (high quality)              |
+---------------------+-------------------------------------------------------+
| image_set           | image_set=4 for 4band, 3 for 3band, 2 for 2band, and  |
|                     | 6, 7 etc. for NEOWISE-R year 1, 2 etc.                |
+---------------------+-------------------------------------------------------+
|.. centered:: **2MASS**                                                      |
+---------------------+-------------------------------------------------------+
| ordate              | UT date of reference (start of nightly operations)    |
+---------------------+-------------------------------------------------------+
| hemisphere          | N or S hemisphere                                     |
+---------------------+-------------------------------------------------------+
| scanno              | Nightly scan number                                   |
+---------------------+-------------------------------------------------------+
| fname               | FITS file name                                        |
+---------------------+-------------------------------------------------------+
| ut_date             | UT date of scan (YYMMDD)                              |
+---------------------+-------------------------------------------------------+
| telname             | Telescope location - Hopkins or CTIO                  |
+---------------------+-------------------------------------------------------+
| mjd                 | Modified Julian Date of observation                   |
+---------------------+-------------------------------------------------------+
| ds                  | ds=full for 2mass                                     |
+---------------------+-------------------------------------------------------+
| .. centered:: **PTF**                                                       |
+---------------------+-------------------------------------------------------+
| obsdate             | Observation UT date/time YYYY-MM-DD HH:MM:SS.SSS      |
+---------------------+-------------------------------------------------------+
| obsmjd              | Modified Julian date of observation                   |
+---------------------+-------------------------------------------------------+
| nid                 | Night database ID                                     |
+---------------------+-------------------------------------------------------+
| expid               | Exposure database ID                                  |
+---------------------+-------------------------------------------------------+
| ccdid               | CCD number (0...11)                                   |
+---------------------+-------------------------------------------------------+
| rfilename           | Raw-image filename                                    |
+---------------------+-------------------------------------------------------+
| pfilename           | Processed-image filename                              |
+---------------------+-------------------------------------------------------+
|.. centered:: **ZTF**                                                        |
+---------------------+-------------------------------------------------------+
| obsdate             | Observation UT date/time YYYY-MM-DD HH:MM:SS.SSS      |
+---------------------+-------------------------------------------------------+
| obsjd               | Julian date of observation                            |
+---------------------+-------------------------------------------------------+
| filefracday         | Observation date with fractional day YYYYMMDDdddddd   |
+---------------------+-------------------------------------------------------+
| field               | ZTF field number                                      |
+---------------------+-------------------------------------------------------+
| ccdid               | CCD number (1...16)                                   |
+---------------------+-------------------------------------------------------+
| qid                 | Detector quadrant (1...4)                             |
+---------------------+-------------------------------------------------------+
| fid                 | Filter ID                                             |
+---------------------+-------------------------------------------------------+
| filtercode          | Filter name (abbreviated)                             |
+---------------------+-------------------------------------------------------+
| pid                 | Science product ID                                    |
+---------------------+-------------------------------------------------------+
| nid                 | Night ID                                              |
+---------------------+-------------------------------------------------------+
| expid               | Exposure ID                                           |
+---------------------+-------------------------------------------------------+
| itid                | Image type ID                                         |
+---------------------+-------------------------------------------------------+
| imgtypecode         | Single letter image type code                         |
+---------------------+-------------------------------------------------------+
|.. centered:: **Spitzer**                                                    |
+---------------------+-------------------------------------------------------+
| reqkey              | Spitzer Astronomical Observation Request number       |
+---------------------+-------------------------------------------------------+
| bcdid               | Post Basic Calibrated Data ID (Lvl. 2 product search) |
+---------------------+-------------------------------------------------------+
| reqmode             | Spitzer Astonomical Observation Request type          |
+---------------------+-------------------------------------------------------+
| wavelength          | Bandpass ID                                           |
+---------------------+-------------------------------------------------------+
| minwavelength       | Min wavelength (microns)                              |
+---------------------+-------------------------------------------------------+
| maxwavelength       | Max wavelength (microns)                              |
+---------------------+-------------------------------------------------------+
| time                | UT time of observation                                |
+---------------------+-------------------------------------------------------+
| exposuretime        | Exposure time (sec)                                   |
+---------------------+-------------------------------------------------------+

The key ``region`` contains an URL to the DS9 Region file that draws a green
circle over the object, or predicted ephemeride, used in the search.

The results returned in this output mode could contain two additional keys -
``fits_tarball`` and ``region_tarball`` - depending on whether the query
parameter ``with_tarballs`` (see below) is set to ``True`` or ``False``. The
keys will contain a link to an TAR archive of all of the matched FITS and DS9
region files respectively.

Brief and VOTable
_________________

In these two modes, only the second key (``metadata``) is returned as either an
:class:`~astropy.table.Table` object, in ``"Brief"`` mode, or, in ``"VOTable"``
mode as an :class:`~astropy.io.votable.tree.VOTableFile` object.

The content of these tables is identical to the one described above. The
``with_tarballs`` parameter is also not applicable to these two modes and will
be ignored if provided.

Gator
_____

An :class:`~astropy.table.Table` is returned containing the following columns:

=========      =====================================
Column 	       Description
=========      =====================================
mjd            Modified Julian Date of observation
scan_id        Scan ID
frame_num      Frame number
ra             Right Ascension of the object (J2000)
dec            Declination of the object (J2000)
=========      =====================================


Query Parameters
================

Depending on the selected ``input_mode`` the required and optional parameters
differ. Certain parameters are always required and, for some, reasonable
defaults are provided. Parameters that are not applicable to the selected input
mode are ignored.

+-------------------+------------------+-------+------------------------------+
| Parameter         | Required         | Type  | Note                         |
+===================+==================+=======+==============================+
| catalog           | always required  | str   | Catalog.                     |
+-------------------+------------------+-------+------------------------------+
| input_mode        | always required  | str   | Input mode.                  |
+-------------------+------------------+-------+------------------------------+
| output_mode       | always required  | str   | Output mode.                 |
+-------------------+------------------+-------+------------------------------+
| ephem_step        | always required  | float | Ephemeris step size, days.   |
+-------------------+------------------+-------+------------------------------+
| with_tarballs     | Only in Regular, | bool  | Return tarballs of fits and  |
|                   | Full output mode |       | regions.                     |
+-------------------+------------------+-------+------------------------------+
| obs_begin         | always optional  | str   | In ``YYYY-MM-DD`` format,    |
|                   |                  | None  | Date prior to which results  |
|                   |                  |       | will not be returned. When   |
|                   |                  |       | ``None``, all observations   |
|                   |                  |       | are returned.                |
+-------------------+------------------+-------+------------------------------+
| obs_end           | always optional  | str   | In ``YYYY-MM-DD`` format,    |
|                   |                  | None  | the date after which results |
|                   |                  |       | will not be returned. When   |
|                   |                  |       | not specified, all           |
|                   |                  |       | observations are returned.   |
+-------------------+------------------+-------+------------------------------+
| obj_name          | name_input       | str   | Solar System Object name.    |
+-------------------+------------------+-------+------------------------------+
| obj_naifid        | naifid_input     | str   | Object's NAIF ID.            |
+-------------------+------------------+-------+------------------------------+
| obj_type          | mpc_input        | str   | Either ``"Asteroid"`` or     |
|                   |                  |       | ``"Comet"``. Case sensitive  |
+-------------------+------------------+-------+------------------------------+
| mpc_data          | mpc_input        | str   | String in MPC's One-Line     |
|                   |                  |       | format.                      |
+-------------------+------------------+-------+------------------------------+
| body_designation  | manual_input     | str   | Name of the object described |
|                   |                  |       | by the given orbit, does not |
|                   |                  |       | need to be a real name. By   |
|                   |                  |       | default constructed from the |
|                   |                  |       | type, i.e ``TestAsteroid``   |
|                   |                  |       | or ``TestComet``             |
+-------------------+------------------+-------+------------------------------+
| epoch             | manual_input     | str   | Epoch of coordinates in MJD. |
|                   |                  | float |                              |
+-------------------+------------------+-------+------------------------------+
| eccentricity      | manual_input     | float | Object's eccentricity (0-1). |
+-------------------+------------------+-------+------------------------------+
| inclination       | manual_input     | float | Inclination (0-180 deg).     |
+-------------------+------------------+-------+------------------------------+
| arg_perihelion    | manual_input     | float | Argument of perihelion       |
|                   |                  |       | (0-360 deg).                 |
+-------------------+------------------+-------+------------------------------+
| ascend_node       | manual_input     | float | Longitude of the ascending   |
|                   |                  |       | node (0-360 deg).            |
+-------------------+------------------+-------+------------------------------+
| semimajor_axis    | manual_input     | float | Semimajor axis for Asteroids |
| perih_dist        |                  |       | and perihelion distance for  |
|                   |                  |       | Comets. In AU.               |
+-------------------+------------------+-------+------------------------------+
| mean_anomaly      | manual_input     | float | Mean anomaly for Asteroids   |
| perih_time        |                  | str   | (deg) or perihelion time for |
|                   |                  |       | Comets                       |
|                   |                  |       | (``YYYY+MM+DD+HH:MM:SS``)    |
+-------------------+------------------+-------+------------------------------+

Examples
========

By default the input mode will be set to ``"name_input"``, the times to ``None``
and output mode to ``Regular``. So the only piece of information required is the
object's name. Since this will search the whole of ``wise_merged`` catalog for
any detections of the given asteroid - we will restrict the example query in
time and output in order to have a more manageable output.

So we can query the night of Thursday, 29th of May 2015 for observations of an
asteroid `Victoria <https://en.wikipedia.org/wiki/12_Victoria>`_ as:

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa.most import Most
    >>> Most.query_object(output_mode="Brief",
    ...                   obj_name="Victoria",
    ...                   obs_begin="2014-05-29",
    ...                   obs_end="2014-05-30")  # doctest: +IGNORE_OUTPUT
    <Table length=10>
      ra_obj    dec_obj  sun_dist geo_dist ... moon_sep saa_sep qual_frame image_set
     float64    float64  float64  float64  ... float64  float64   int64      int64
    ---------- --------- -------- -------- ... -------- ------- ---------- ---------
    333.539704 -0.779308   1.8179   1.4638 ...  102.339  15.039         10         6
    333.539704 -0.779308   1.8179   1.4638 ...  102.339  15.039         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  103.825  46.517         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  103.825  46.517         10         6
    333.638286  -0.71525   1.8179   1.4614 ...  105.327  89.053         10         6
    333.638286  -0.71525   1.8179   1.4614 ...  105.327  89.053         10         6
    333.687495 -0.683205   1.8178   1.4603 ...  106.803 115.076         10         6
    333.687495 -0.683205   1.8178   1.4603 ...  106.803 115.076         10         6
    333.736581  -0.65122   1.8178   1.4591 ...  108.294  73.321         10         6
    333.736581  -0.65122   1.8178   1.4591 ...  108.294  73.321         10         6

To return more than just a table of image identifiers, use one of the more
verbose output modes - ``Regular`` or ``Full``.

.. doctest-remote-data::

    >>> matched = Most.query_object(output_mode="Regular",
    ...                             with_tarballs=True,
    ...                             obj_name="Victoria",
    ...                             obs_begin="2014-05-29",
    ...                             obs_end="2014-05-30")
    >>> type(matched)
    <class 'dict'>
    >>> matched.keys()
    dict_keys(['results', 'metadata', 'region', 'fits_tarball', 'region_tarball'])
    >>> matched["metadata"] # doctest: +IGNORE_OUTPUT
    <Table length=10>
      ra_obj    dec_obj  sun_dist geo_dist ... moon_sep saa_sep qual_frame image_set
     float64    float64  float64  float64  ... float64  float64   int64      int64
    ---------- --------- -------- -------- ... -------- ------- ---------- ---------
    333.539704 -0.779308   1.8179   1.4638 ...  102.339  15.039         10         6
    333.539704 -0.779308   1.8179   1.4638 ...  102.339  15.039         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  103.825  46.517         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  103.825  46.517         10         6
    333.638286  -0.71525   1.8179   1.4614 ...  105.327  89.053         10         6
    333.638286  -0.71525   1.8179   1.4614 ...  105.327  89.053         10         6
    333.687495 -0.683205   1.8178   1.4603 ...  106.803 115.076         10         6
    333.687495 -0.683205   1.8178   1.4603 ...  106.803 115.076         10         6
    333.736581  -0.65122   1.8178   1.4591 ...  108.294  73.321         10         6
    333.736581  -0.65122   1.8178   1.4591 ...  108.294  73.321         10         6

As demonstrated, the returned values are stored in a dictionary and which
``metadata`` key table matches the ``Brief`` output mode table.

The ``fits_tarball`` and ``region_tarballs`` keys store the URL of the TAR
archive containing all 10 images that observed asteroid Victoria on that night.
Individual images that were put into the archive are stored under the ``results``
key:

.. doctest-remote-data::

    >>> matched["fits_tarball"]  # doctest: +IGNORE_OUTPUT
    'https://irsa.ipac.caltech.edu/workspace/TMP_X69utS_13312/Most/pid15792/fitsimage_A850RA.tar.gz'
    >>> matched["region_tarball"]  # doctest: +IGNORE_OUTPUT
    'https://irsa.ipac.caltech.edu/workspace/TMP_X69utS_13312/Most/pid15792/ds9region_A850RA.tar'
    >>> matched["results"].columns
    <TableColumns names=('Image_ID','date_obs','time_obs','mjd_obs','ra_obj','dec_obj','sun_dist','geo_dist','dist_ctr','phase','vmag','image_url','postcard_url','region_file')>
    >>> matched["results"]["time_obs", "image_url"]  # doctest: +IGNORE_OUTPUT
    <Table length=10>
      time_obs                                                  image_url
       str12                                                      str103
    ------------ -------------------------------------------------------------------------------------------------------
    11:00:08.319 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/3b/49273b/134/49273b134-w2-int-1b.fits
    11:00:08.319 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/3b/49273b/134/49273b134-w1-int-1b.fits
    14:09:44.351 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/7b/49277b/135/49277b135-w1-int-1b.fits
    14:09:44.351 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/7b/49277b/135/49277b135-w2-int-1b.fits
    17:19:09.391 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/1b/49281b/134/49281b134-w2-int-1b.fits
    17:19:09.391 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/1b/49281b/134/49281b134-w1-int-1b.fits
    20:28:45.431 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/5b/49285b/135/49285b135-w2-int-1b.fits
    20:28:45.431 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/5b/49285b/135/49285b135-w1-int-1b.fits
    23:38:10.476 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/9b/49289b/134/49289b134-w1-int-1b.fits
    23:38:10.476 https://irsa.ipac.caltech.edu/ibe/data/wise/merge/merge_p1bm_frm/9b/49289b/134/49289b134-w2-int-1b.fits

.. note::
    The returned TAR Archives point to the Most service hosted directory which
    will dissapear after a while, making the URLs return a 404 Not Found Error.
    The URLs returned by the results table, however, point to the NASA/IPAC
    Infrared Science Archive, which means that the URLs to the images themselves
    will remain valid even after the Most URLs expire.


Reference/API
=============

See `~astroquery.ipac.irsa.most.MostClass` and `~astroquery.ipac.irsa.Conf`.
