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
 - Solar System Object Name Input (`name_input`)
 - Solar System Object NAIF ID Input (`naifid_input`)
 - MPC One-Line Element Input (`mpc_input`)
 - Orbital Elements Manual Input (`manual_input`)

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
Center (MPC) one-line format <https://irsa.ipac.caltech.edu/applications/Gator/GatorAid/irsa/moving.html>`_.

The desired input mode can be specified by providing one of the accepted values
as `input_mode` keyword to :meth:`~astroquery.ipac.irsa.most.MostClass.query`
or by specifying a new default value in :class:`~astroquery.ipac.irsa.most.Conf`

Depending on what input mode MOST is being queried as, the list of required
parameters will change.

Output Modes
------------

The service accepts several different output modes:
 - `Regular`
 - `Full`
 - `Brief`
 - `VOTable`
 - `Gator`

The :meth:`~astroquery.ipac.irsa.most.MostClass.query` method will return
different objects depending on the specified output mode.

===================  =========================================================
Output mode          Returned object
===================  =========================================================
`Regular` or `Full`  Dictionary containing `results`, `metadata` and `region`.
                     keys, optionally additionally `fits_tarball` and
                     `region_tarball`.
`Brief` or `Gator`   :class:`astropy.table.Table` object.
`VOTable`            :class:`astropy.io.VOTable` object.
===================  =========================================================

In `Regular` or `Full` output mode, the returned dictionary's key `results`
maps to the table titled "Images with a Matched Object Position", which
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

The table contained under `metadata` key, when in `Regular` or `Full` mode
contains the following columns:

+---------------------+-------------------------------------------------------+
| Column              | Description                                           |
+=====================+=======================================================+
|                     **General**                                             |
+---------------------+-------------------------------------------------------+
| ra1, dec1,          | Right ascension and declination of the 4 corners of   |
| ra2, dec2, etc.     | the image (deg, J2000)                                |
+---------------------+-------------------------------------------------------+
| match               | match = 1 indicates a matched image (added by MOST)   |
+---------------------+-------------------------------------------------------+
|                     **WISE/NEOWISE**                                        |
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
|                     **2MASS**                                               |
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
|                     **PTF**                                                 |
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
|                     **ZTF**                                                 |
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
|                     **Spitzer**                                             |
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

The key `region` contains an URL to the DS9 Region file.

In `Full` and `Regular` mode, when the query parameter `fits_region_files` (see
below) is set to True, the two additional keys - `fits_tarball` and
`region_tarball` will be present in the return. The two keys contain a link to
all the matched FITS images and the DS9 region file, as a TAR archive.

In `Brief` and `VOTable` output modes, only the second table (the above
`metadata`) is returned. The main difference is that in `Brief` mode the table
is retrieved as a :class:`~astropy.table.Table` object and in `VOTable` as an
:class:`~astropy.io.VOTable`.

`Gator` mode returns :class:`~astropy.table.Table` containing the following
columns:

=========      =====================================
Column 	       Description
=========      =====================================
mjd            Modified Julian Date of observation
scan_id        Scan ID
frame_num      Frame number
ra             Right Ascension of the object (J2000)
dec            Declination of the object (J2000)
=========      =====================================

I guess? It's not clearly documented if these are RA DEC of images or objects

Query Parameters
-----------------

Depending on the selected `input_mode` the required and optional parameters
differ. Certain parameters are always required and for some reasonable defaults
are provided.

+-------------------+------------------+-------+------------------------------+
| Parameter         | Required         | Type  | Note                         |
+===================+==================+=======+==============================+
| catalog           | always required  | str   | Catalog. By default          |
|                   |                  |       | `conf.catalog`. See          |
|                   |                  |       | `self.list_catalogs`.        |
+-------------------+------------------+-------+------------------------------+
| input_type        | always required  | str   | Input mode.                  |
+-------------------+------------------+-------+------------------------------+
| output_mode       | always required  | str   | Output mode.                 |
+-------------------+------------------+-------+------------------------------+
| ephem_step        | always required  | float | Ephemeris step size, days.   |
|                   |                  |       | Default `conf`.              |
+-------------------+------------------+-------+------------------------------+
| obs_begin         | always optional  | str   | In 'YYYY-MM-DD` format, the  |
|                   |                  | None  | date prior to which results  |
|                   |                  |       | will not be returned. When   |
|                   |                  |       | not specified, all           |
|                   |                  |       | observations are returned.   |
+-------------------+------------------+-------+------------------------------+
| obs_end           | always optional  | str   | In 'YYYY-MM-DD` format, the  |
|                   |                  | None  | date after  which results    |
|                   |                  |       | will not be returned. When   |
|                   |                  |       | not specified, all           |
|                   |                  |       | observations are returned.   |
+-------------------+------------------+-------+------------------------------+
| fits_region_files | Only in Regular, | bool  | Return tarballs of fits and  |
|                   | Full output mode |       | regions. Default: `False`    |
+-------------------+------------------+-------+------------------------------+
| obj_name          | name_input       | str   | Solar System Object name.    |
+-------------------+------------------+-------+------------------------------+
| obj_naifid        | naifid_input     | str   | Object's NAIF ID.            |
+-------------------+------------------+-------+------------------------------+
| obj_type          | mpc_input        | str   | Either 'Asteroid' or 'Comet' |
|                   |                  |       | Case sensitive               |
+-------------------+------------------+-------+------------------------------+
| mpc_data          | mpc_input        | str   | String in MPC's One-Line     |
|                   |                  |       | format.                      |
+-------------------+------------------+-------+------------------------------+
| body_designation  | manual_input     | str   | Name of the object described |
|                   |                  |       | by the given orbit, does not |
|                   |                  |       | need to be a real name. By   |
|                   |                  |       | default constructed from the |
|                   |                  |       | type, i.e `TestAsteroid` or  |
|                   |                  |       | `TestComet`                  |
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
|                   |                  |       | Comets (YYYY+MM+DD+HH:MM:SS) |
+-------------------+------------------+-------+------------------------------+

"""
import io
import re

from bs4 import BeautifulSoup

from astropy.io import votable
from astropy.table import Table

from astroquery.query import BaseQuery
from astroquery.utils import class_or_instance

from . import conf


class MOSTClass(BaseQuery):
    URL = conf.server
    TIMEOUT = conf.timeout

    _default_qparams = {
        "catalog": conf.catalog,
        "input_type": conf.input_type,
        "output_mode": conf.output_mode,
        "obs_begin": None,
        "obs_end": None,
        "ephem_step": conf.ephem_step,
        "fits_region_files": False,
        "obj_name": None,
        "obj_nafid": None,
        "obj_type": None,
        "mpc_data": None,
        "body_designation": None,
        "epoch": None,
        "eccentricity": None,
        "inclination": None,
        "arg_perihelion": None,
        "ascend_node": None,
        "semimajor_axis": None,
        "mean_anomaly": None,
        "perih_dist": None,
        "perih_time": None
    }

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
        if not params.get("catalog", False):
            raise ValueError("Which catalog is being queried is always required.")

        input_type = params.get("input_type", False)
        if not input_type:
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
    def query(self, get_query_payload=False, **query_params):
        """
        Query the MOST interface using specified parameters and/or default
        query values.

        The required and optional query parameters vary depending on the query
        input type. Parameters that do not match the required input type will
        be ignored. Certain parameters are always required input to the
        service. Provided default values match the defaults of the online
        MOST interface.
        See module help for more details.

        Parameters
        ----------
        get_query_payload : `bool`, optional
            Return the query parameters as a dictionary. Useful for debugging.
            Set to `False` by default.
        **query_params
            Query parameters, see module help for all available options. By
            default requires at least `obj_name` value and queries `wise_merge`
            catalog matching in the `name_input` mode.

        Returns
        -------
        query_results : `astropy.table.Table`, `astropy.io.VOTable` or `dict`
            Returns query results in a format specified by the output mode. See
            module help for more details.
        """
        qparams = self._default_qparams.copy()
        qparams.update(query_params)
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
