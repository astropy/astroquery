"""
MOST
====

Moving Object Search Tool can determine the orbit for a given solar system
object then find images that covered the object's predicted positions in select
image datasets housed at IRSA. It can serve as a "precovery" tool to see if
newly discovered objects were previously observed.

The URL of the MOST interface is:

 https://irsa.ipac.caltech.edu/applications/MOST/

Input Modes
-----------

The service accepts several different input modes:
 - Solar System Object Name Input (``"name_input"``)
 - Solar System Object NAIF ID Input (``"naifid_input"``)
 - MPC One-Line Element Input (``"mpc_input"``)
 - Orbital Elements Manual Input (``"manual_input"``)

Name resolution and ephemeris generation for known objects is done via query to
JPL's Horizon database whenever possible. This lookup can fail when name
ambiguities exist. For example, entering "Neptune" is unclear because ephemeris
for both Neptune and Neptune system barycenter exist.

MOST will deliver a messsage if there is an ambiguity. The message may contain
suggested NAIF ID's, e.g. "899:NID" for Neptune.

NAIF ID's are considered valid input. Satellites and asteroids with the same
name may be distinguished by, e.g. "Europa:SAT" and "Europa:AST".

The ephemeris can also be calculated for comets or asteroids using orbital
elements supplied by the user, either individually or in the `Minor Planet
Center (MPC) one-line format
<https://irsa.ipac.caltech.edu/applications/Gator/GatorAid/irsa/moving.html>`_.

Depending on what input mode MOST is being queried as, the list of required
parameters will change.

Output Modes
------------

The service accepts several different output modes:
 - ``Regular`` - default
 - ``Full``
 - ``Brief``
 - ``VOTable``
 - ``Gator``

The :meth:`~astroquery.ipac.irsa.most.MOSTClass.query_object` method will
return different objects depending on the specified output mode.

============================ ==================================================
Output mode                  Returned object
============================ ==================================================
``"Regular"`` or ``"Full"``` Dictionary containing ``results``, ``metadata``
                             and ``region`` keys. Optionally also
                             ``fits_tarball`` and ``region_tarball``.
``"Brief"`` or ``"Gator"``   :class:`~astropy.table.Table` object.
``"VOTable"``                :class:`~astropy.io.votable.tree.VOTableFile`
                             object.
============================ ==================================================

.. note::
    The difference between ``Regular`` and ``Full`` output mode is non-existant
    as the returned data in both cases is identical, as the figures created in
    ``Full`` mode are not downloaded. The difference between the two modes are
    mainly visible in presentation of the data when MOST is used via their
    online interface. It is, therefore, recommended ``Regular`` because the
    query will complete significantly faster.

Regular and Full
________________

In ``"Regular"`` or ``"Full"`` output mode :meth:`~astroquery.ipac.irsa.most.MOSTClass.query_object`
returns a dictionary containing ``results``, ``metadata`` and ``region`` keys.

The ``results`` key contains a table that maps to the results table returned by
MOST service titled ``Images with a Matched Object Position``. The table
contains the following columns:

============   ===============================================================
Column 	       Description
============   ===============================================================
Image_ID       A unique identifier for the image data, not necessarily the
               image file name.
date_obs       Date (UTC) of the observation.
time_obs       Time (UTC) of the midpoint of the observation.
mjd_obs        Modified Julian Date (days) of the midpoint of the observation.
ra_obs         Ephemeris of the object's right ascension (deg, J2000).
dec_obs        Ephemeris of the object's declination (deg, J2000).
sun_dist       Heliocentric distance of the object (AU).
geo_dist       Geocentric distance of the object (AU).
dist_ctr       Projected distance  from the center of the image (deg).
phase          Sun-Object-earth angle (deg).
vmag           Estimate of visual magnitude (from Horizons).
image_url      Links to download or view the data.
postcard_url   ??? usually ``null``
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
| match               | match = 1 indicates a matched image (added by MOST)   |
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
-----------------

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
--------

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
    ...                   obs_end="2014-05-30")
    <Table length=10>
      ra_obj    dec_obj  sun_dist geo_dist ... saa_sep qual_frame image_set
     float64    float64  float64  float64  ... float64   int64      int64
    ---------- --------- -------- -------- ... ------- ---------- ---------
    333.539704 -0.779309   1.8179   1.4638 ...  15.039         10         6
    333.539704 -0.779309   1.8179   1.4638 ...  15.039         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  46.517         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  46.517         10         6
    333.638285  -0.71525   1.8179   1.4614 ...  89.053         10         6
    333.638285  -0.71525   1.8179   1.4614 ...  89.053         10         6
    333.687494 -0.683205   1.8178   1.4603 ... 115.076         10         6
    333.687494 -0.683205   1.8178   1.4603 ... 115.076         10         6
     333.73658 -0.651221   1.8178   1.4591 ...  73.321         10         6
     333.73658 -0.651221   1.8178   1.4591 ...  73.321         10         6

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
    >>> matched["metadata"]
    <Table length=10>
      ra_obj    dec_obj  sun_dist geo_dist ... saa_sep qual_frame image_set
     float64    float64  float64  float64  ... float64   int64      int64
    ---------- --------- -------- -------- ... ------- ---------- ---------
    333.539704 -0.779309   1.8179   1.4638 ...  15.039         10         6
    333.539704 -0.779309   1.8179   1.4638 ...  15.039         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  46.517         10         6
    333.589056 -0.747249   1.8179   1.4626 ...  46.517         10         6
    333.638285  -0.71525   1.8179   1.4614 ...  89.053         10         6
    333.638285  -0.71525   1.8179   1.4614 ...  89.053         10         6
    333.687494 -0.683205   1.8178   1.4603 ... 115.076         10         6
    333.687494 -0.683205   1.8178   1.4603 ... 115.076         10         6
     333.73658 -0.651221   1.8178   1.4591 ...  73.321         10         6
     333.73658 -0.651221   1.8178   1.4591 ...  73.321         10         6

As demonstrated, the returned values are stored in a dictionary and which
``metadata`` key table matches the ``Brief`` output mode table.

The ``fits_tarball`` and ``region_tarballs`` keys store the URL of the TAR
archive containing all 10 images that observed asteroid Victoria on that night.
Individual images that were put into the archive are stored under the ``results``
key:

.. doctest-remote-data::

    >>> matched["fits_tarball"]  # doctest: +IGNORE_OUTPUT
    'https://irsa.ipac.caltech.edu/workspace/TMP_X69utS_13312/MOST/pid15792/fitsimage_A850RA.tar.gz'
    >>> matched["region_tarball"]  # doctest: +IGNORE_OUTPUT
    'https://irsa.ipac.caltech.edu/workspace/TMP_X69utS_13312/MOST/pid15792/ds9region_A850RA.tar'
    >>> matched["results"].columns
    <TableColumns names=('Image_ID','date_obs','time_obs','mjd_obs','ra_obj','dec_obj','sun_dist','geo_dist','dist_ctr','phase','vmag','image_url','postcard_url','region_file')>  # noqa: E501
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
    The returned TAR Archives point to the MOST service hosted directory which
    will dissapear after a while, making the URLs return a 404 Not Found Error.
    The URLs returned by the results table, however, point to the NASA/IPAC
    Infrared Science Archive, which means that the URLs to the images themselves
    will remain valid even after the MOST URLs expire.
"""
import io
import re
import tarfile

from bs4 import BeautifulSoup

from astropy.io import votable, fits

from astropy.table import Table

from astroquery.query import BaseQuery
from astroquery.utils import class_or_instance

from . import conf


__all__ = ["Most", "MOSTClass"]


class MOSTClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout

    def __init__(self):
        super().__init__()

    def _validate_name_input_type(self, params):
        """
        Validate required parameters when `input_type='name_input'`.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        if not params.get("obj_name", False):
            raise ValueError("When input type is 'name_input' key 'obj_name' is required.")

    def _validate_nafid_input_type(self, params):
        """
        Validate required parameters when `input_type='naifid_input'`.


        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """

        if not params.get("obj_nafid", False):
            raise ValueError("When input type is 'nafid_input' key 'obj_nafid' is required.")

    def _validate_mpc_input_type(self, params):
        """
        Validate required parameters when `input_type='mpc_input'`.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        obj_type = params.get("obj_type", False)
        if not obj_type:
            raise ValueError("When input type is 'mpc_input' key 'obj_type' is required.")
        if obj_type not in ("Asteroid", "Comet"):
            raise ValueError("Object type is case sensitive and must be one of: `Asteroid` or `Comet`")

        if not params.get("mpc_data", False):
            raise ValueError("When input type is 'mpc_input' key 'mpc_data' is required.")

    def _validate_manual_input_type(self, params):
        """
        Validate required parameters when `input_type='manual_input'`.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        obj_type = params.get("obj_type", False)
        if not obj_type:
            raise ValueError("When input type is 'mpc_input' key 'obj_type' is required.")
        if obj_type not in ("Asteroid", "Comet"):
            raise ValueError("Object type is case sensitive and must be one of: `Asteroid` or `Comet`")

        # MOST will always require at least the distance and eccentricity
        # distance param is named differently in cases of asteroids and comets
        if not params.get("eccentricity", False):
            raise ValueError("When input_type is 'manual_input', 'eccentricity' is required.")

        if obj_type == "Asteroid":
            if not params.get("semimajor_axis", False):
                raise ValueError("When obj_type is 'Asteroid', 'semimajor_axis' is required.")
        elif obj_type == "Comet":
            if not params.get("perih_dist", False):
                raise ValueError("When obj_type is 'Comet', 'perih_dist' is required.")

        # This seemingly can be whatever
        if not params.get("body_designation", False):
            params["body_designation"] = "Test"+params["obj_type"]

    def _validate_input(self, params):
        """
        Validate the minimum required set of parameters, for a given input
        type, are at least truthy.

        These include the keys `catalog`, `input_type`, `output_mode` and
        `ephem_step` in addition to keys required by the specified input type.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        if params.get("catalog", None) is None:
            raise ValueError("Which catalog is being queried is always required.")

        input_type = params.get("input_type", None)
        if input_type is None:
            raise ValueError("Input type is always required.")

        if input_type == "name_input":
            self._validate_name_input_type(params)
        elif input_type == "nafid_input":
            self._validate_nafid_input_type(params)
        elif input_type == "mpc_input":
            self._validate_mpc_input_type(params)
        elif input_type == "manual_input":
            self._validate_manual_input_type(params)
        else:
            raise ValueError(
                "Unrecognized `input_type`. Expected `name_input`, `nafid_input` "
                f"`mpc_input` or `manual_input`, got {input_type} instead."
            )

    def _parse_full_regular_response(self, response, withTarballs=False):
        """
        Parses the response when output type is set to `Regular` or `Full`.

        Parameters
        ----------
        response : `requests.models.Response`
            Query response.
        withTarballs : `bool`, optional
            Parse the links to FITS and region tarballs from the response. By
            default, set to False.

        Returns
        -------
        retdict : `dict`
            Dictionary containing the keys `results`, `metadata` and `region`.
            Optionally can contain keys `fits_tarball` and `region_tarball`.
            The `results` and `metadata` are an `astropy.table.Table` object
            containing the links to image and region files and minimum object
            metadata, while `metadata` contains the image metadata and object
            positions. The `region` key contains a link to the DS9 region file
            representing the matched object trajectory and search boxes. When
            existing, `fits_tarball` and `region_tarball` are links to the
            tarball archives of the fits and region images.
        """
        retdict = {}
        html = BeautifulSoup(response.content, "html5lib")
        download_tags = html.find_all("a", string=re.compile(".*Download.*"))

        # this is "Download Results Table (above)"
        results_response = self._request("GET", download_tags[0]["href"])
        retdict["results"] = Table.read(results_response.text, format="ipac")

        # this is "Download Image Metadata with Matched Object position Table"
        imgmet_response = self._request("GET", download_tags[1]["href"])
        retdict["metadata"] = Table.read(imgmet_response.text, format="ipac")

        # this is "Download DS9 Region File with the Orbital Path", it's a link
        # to a DS9 region file
        # regions_response = self._request("GET", download_tags[2]["href"])
        retdict["region"] = download_tags[2]["href"]

        if withTarballs:
            retdict["fits_tarball"] = download_tags[-1]["href"]
            retdict["region_tarball"] = download_tags[-2]["href"]

        return retdict

    @class_or_instance
    def list_catalogs(self):
        """Returns a list of queriable catalogs."""
        response = self._request("GET", conf.interface_url, timeout=self.TIMEOUT)

        html = BeautifulSoup(response.content, "html5lib")
        catalog_dropdown_options = html.find("select").find_all("option")

        catalogs = [tag.string for tag in catalog_dropdown_options]
        # I think I saw somewhere that some password prompt will pop up for
        # catalogs listed as '--- Internal use only:' but there are seemingly
        # no limits to queries there.
        if "--- Internal use only:" in catalogs:
            catalogs.remove("--- Internal use only:")
        return catalogs

    def get_images(
            self,
            catalog="wise_merge",
            input_mode="name_input",
            ephem_step=0.25,
            obs_begin=None,
            obs_end=None,
            obj_name=None,
            obj_nafid=None,
            obj_type=None,
            mpc_data=None,
            body_designation=None,
            epoch=None,
            eccentricity=None,
            inclination=None,
            arg_perihelion=None,
            ascend_node=None,
            semimajor_axis=None,
            mean_anomaly=None,
            perih_dist=None,
            perih_time=None,
            get_query_payload=False,
            save=False,
            savedir='',
    ):
        """Gets images containing the specified object or orbit.

        Parameters are case sensitive.
        See module help for more details.

        Parameters
        ----------
        catalog : str
            Catalog to query.
            Required.
            Default ``"wise_merge"``.
        input_mode : str
            Input mode. One of ``"name_input"``, ``"naifid_input"``,
            ``"mpc_input"`` or ``"manual_input"``.
            Required.
            Default: ``"name_input"``.
        ephem_step : 0.25,
            Size of the steps (in days) at which the object ephemeris is evaluated.
            Required.
            Default: 0.25
        obs_begin : str or None
            UTC of the start of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog which can be slow.
            Optional.
            Default: ``None``.
        obs_end : str or None
            UTC of the end of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog, can be slow.
            Optional.
            Default: ``None``.
        obj_name : str or None
            Object name.
            Required when input mode is ``"name_input"``.
        obj_nafid : str or None
            Object NAIFD.
            Required when input mode is ``"naifid_input"``.
        obj_type : str or None
            Object type, ``"Asteroid"`` or ``Comet``.
            Required when input mode is ``"mpc_input"`` or ``"manual_input"``.
        mpc_data : str or None
            MPC formatted object string.
            Required when input mode is ``"mpc_input"``.
        body_designation : str or None
            Name of the object described by the given orbital parameters. Does
            not have to be a real name. Will default to ``"TestAsteroid"`` or
            ``"TestComet"`` depending on selected object type.
            Required when input mode is ``"manual_input"``.
        epoch : str or None
            Epoch in MJD.
            Required when input mode is ``"manual_input"``.
        eccentricity : float or None
            Eccentricity (0-1).
            Required when input mode is ``"manual_input"``.
        inclination : float or None
            Inclination (0-180 degrees).
            Required when input mode is ``"manual_input"``.
        arg_perihelion : str or None
            Argument of perihelion (0-360 degrees).
            Required when input mode is ``"manual_input"``.
        ascend_node : float or None
            Longitude of the ascending node (0-360).
            Required when input mode is ``"manual_input"``.
        semimajor_axis : float or None
            Semimajor axis (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        mean_anomaly : str or None
            Mean anomaly (degrees).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        perih_dist : float or None
            Perihelion distance (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        perih_time : str or None
            Perihelion time (YYYY+MM+DD+HH:MM:SS).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        get_query_payload : bool
            Return the query parameters as a dictionary. Useful for debugging.
            Optional.
            Default: ``False``
        save : bool
            Whether to save the file to a local directory.
        savedir : str
            The location to save the local file if you want to save it
            somewhere other than `~astroquery.query.BaseQuery.cache_location`

        Returns
        -------
        images : list
            A list of `~astropy.io.fits.HDUList` objects.
        """
        # We insist on output_mode being regular so that it executes quicker,
        # and we insist on tarballs so the download is quicker. We ignore
        # whatever else user provides, but leave the parameters as arguments to
        # keep the same signatures for doc purposes.
        queryres = self.query_object(
            catalog=catalog,
            input_mode=input_mode,
            obs_begin=obs_begin,
            obs_end=obs_end,
            ephem_step=ephem_step,
            obj_name=obj_name,
            obj_nafid=obj_nafid,
            obj_type=obj_type,
            mpc_data=mpc_data,
            body_designation=body_designation,
            epoch=epoch,
            eccentricity=eccentricity,
            inclination=inclination,
            arg_perihelion=arg_perihelion,
            ascend_node=ascend_node,
            semimajor_axis=semimajor_axis,
            mean_anomaly=mean_anomaly,
            perih_dist=perih_dist,
            perih_time=perih_time,
            get_query_payload=get_query_payload,
            output_mode="Regular",
            with_tarballs=True,
        )

        request = self._request("GET", queryres["fits_tarball"],
                                save=save, savedir=savedir)

        archive = tarfile.open(fileobj=io.BytesIO(request.content))
        images = []
        for name in archive.getnames():
            if ".fits" in name:
                fileobj = archive.extractfile(name)
                fitsfile = fits.open(fileobj)
                images.append(fitsfile)

        return images

    @class_or_instance
    def query_object(
            self,
            catalog="wise_merge",
            input_mode="name_input",
            output_mode="Regular",
            ephem_step=0.25,
            with_tarballs=False,
            obs_begin=None,
            obs_end=None,
            obj_name=None,
            obj_nafid=None,
            obj_type=None,
            mpc_data=None,
            body_designation=None,
            epoch=None,
            eccentricity=None,
            inclination=None,
            arg_perihelion=None,
            ascend_node=None,
            semimajor_axis=None,
            mean_anomaly=None,
            perih_dist=None,
            perih_time=None,
            get_query_payload=False
    ):
        """
        Query the MOST interface using specified parameters and/or default
        query values.

        MOST service takes an object/orbit, depending on the input mode,
        evaluates its ephemerides in the, in the given time range, and returns
        a combination of image identifiers, image metadata and/or ephemerides
        depending on the output mode.

        The required and optional query parameters vary depending on the query
        input type. Provided parameters that do not match the given input type
        will be ignored. Certain parameters are always required input to the
        service. For these the provided default values match the defaults of
        the online MOST interface.

        Parameters are case sensitive.
        See module help for more details.

        Parameters
        ----------
        catalog : str
            Catalog to query.
            Required.
            Default ``"wise_merge"``.
        input_mode : str
            Input mode. One of ``"name_input"``, ``"naifid_input"``,
            ``"mpc_input"`` or ``"manual_input"``.
            Required.
            Default: ``"name_input"``.
        output_mode : str
            Output mode. One of ``"Regular"``, ``"Full"``, ``"Brief"``,
            ``"Gator"`` or ``"VOTable"``.
            Required.
            Default: ``"Regular"``
        ephem_step : 0.25,
            Size of the steps (in days) at which the object ephemeris is evaluated.
            Required.
            Default: 0.25
        with_tarballs : bool
            Return links to tarballs of found FITS and Region files.
            Optional, only when output mode is ``"Regular"`` or ``"Full"``.
            Default: ``False``
        obs_begin : str or None
            UTC of the start of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog which can be slow.
            Optional.
            Default: ``"None"``.
        obs_end : str or None
            UTC of the end of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog, can be slow.
            Optional.
            Default: ``None``
        obj_name : str or None
            Object name.
            Required when input mode is ``"name_input"``.
        obj_nafid : str or None
            Object NAIFD
            Required when input mode is ``"naifid_input"``.
        obj_type : str or None
            Object type, ``"Asteroid"`` or ``Comet``
            Required when input mode is ``"mpc_input"`` or ``"manual_input"``.
        mpc_data : str or None
            MPC formatted object string.
            Required when input mode is ``"mpc_input"``.
        body_designation : str or None
            Name of the object described by the given orbital parameters. Does
            not have to be a real name. Will default to ``"TestAsteroid"`` or
            ``"TestComet"`` depending on selected object type.
            Required when input mode is ``"manual_input"``.
        epoch : str or None
            Epoch in MJD.
            Required when input mode is ``"manual_input"``.
        eccentricity : float or None
            Eccentricity (0-1).
            Required when input mode is ``"manual_input"``.
        inclination : float or None
            Inclination (0-180 degrees).
            Required when input mode is ``"manual_input"``.
        arg_perihelion : str or None
            Argument of perihelion (0-360 degrees).
            Required when input mode is ``"manual_input"``.
        ascend_node : float or None
            Longitude of the ascending node (0-360).
            Required when input mode is ``"manual_input"``.
        semimajor_axis : float or None
            Semimajor axis (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        mean_anomaly : str or None
            Mean anomaly (degrees).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        perih_dist : float or None
            Perihelion distance (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        perih_time : str or None
            Perihelion time (YYYY+MM+DD+HH:MM:SS).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        get_query_payload : bool
            Return the query parameters as a dictionary. Useful for debugging.
            Optional.
            Default: ``False``

        Returns
        -------
        query_results : `~astropy.table.Table`, `~astropy.io.votable.tree.VOTableFile` or `dict`
            Results of the query. Content depends on the selected output mode.
            In ``"Full"`` or ``"Regular"`` output mode returns a dictionary
            containing at least ``results``, ``metadata`` and ``region`` keys,
            and optionally ``fits_tarball`` and ``region_tarball`` keys. When
            in ``"Brief"`` or ``"Gator"`` an `~astropy.table.Table` object and
            in ``"VOTable"`` an `~astropy.io.votable.tree.VOTableFile`. See
            module help for more details on the content of these tables.
        """
        # This is a map between the keyword names used by the MOST cgi-bin
        # service and their more user-friendly names. For example,
        # input_type -> input_mode or fits_region_files --> with tarballs
        qparams = {
            "catalog": catalog,
            "input_type": input_mode,
            "output_mode": output_mode,
            "obs_begin": obs_begin,
            "obs_end": obs_end,
            "ephem_step": ephem_step,
            "fits_region_files": "on" if with_tarballs else "",
            "obj_name": obj_name,
            "obj_nafid": obj_nafid,
            "obj_type": obj_type,
            "mpc_data": mpc_data,
            "body_designation": body_designation,
            "epoch": epoch,
            "eccentricity": eccentricity,
            "inclination": inclination,
            "arg_perihelion": arg_perihelion,
            "ascend_node": ascend_node,
            "semimajor_axis": semimajor_axis,
            "mean_anomaly": mean_anomaly,
            "perih_dist": perih_dist,
            "perih_time": perih_time,
        }

        if get_query_payload:
            return qparams

        self._validate_input(qparams)
        response = self._request("POST", self.URL,
                                 data=qparams, timeout=self.TIMEOUT)

        if qparams["output_mode"] in ("Brief", "Gator"):
            return Table.read(response.text, format="ipac")
        elif qparams["output_mode"] == "VOTable":
            return votable.parse(io.BytesIO(response.content))
        else:
            return self._parse_full_regular_response(response, qparams["fits_region_files"])


Most = MOSTClass()
