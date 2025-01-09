# -*- coding: utf-8 -*-

import json
import re
import warnings

import numpy as np
from bs4 import BeautifulSoup
from astropy.io import ascii
from astropy.time import Time
from astropy.table import Table, QTable, Column
import astropy.units as u
from astropy.coordinates import EarthLocation, Angle, SkyCoord
from erfa import ErfaWarning

from ..query import BaseQuery
from . import conf
from ..utils import async_to_sync, class_or_instance
from ..exceptions import InvalidQueryError, EmptyResponseError
from astropy.utils.decorators import deprecated_renamed_argument

__all__ = ['MPCClass']


@async_to_sync
class MPCClass(BaseQuery):
    MPC_URL = 'https://' + conf.web_service_server + '/web_service'
    # The authentication credentials for the MPC web service are publicly
    # available and can be openly viewed on the documentation page at
    # https://minorplanetcenter.net/web_service/
    MPC_USERNAME = 'mpc_ws'
    MPC_PASSWORD = 'mpc!!ws'

    MPES_URL = 'https://' + conf.mpes_server + '/cgi-bin/mpeph2.cgi'
    OBSERVATORY_CODES_URL = ('https://' + conf.web_service_server
                             + '/iau/lists/ObsCodes.html')

    MPCOBS_URL = conf.mpcdb_server

    TIMEOUT = conf.timeout

    _ephemeris_types = {
        'equatorial': 'a',
        'heliocentric': 's',
        'geocentric': 'G'
    }

    _default_number_of_steps = {
        'd': '21',
        'h': '49',
        'm': '121',
        's': '301'
    }

    _proper_motions = {
        'total': 't',
        'coordinate': 'c',
        'sky': 's'
    }

    def __init__(self):
        super().__init__()

    def query_object_async(self, target_type, *, get_query_payload=False, **kwargs):
        """
        Query around a specific object within a given mission catalog. When
        searching for a comet, it will return the entry with the latest epoch.

        The following are valid query parameters for the MPC API search. The
        params list and description are from
        https://minorplanetcenter.net/web_service/ and are accurate as of
        3/6/2018.

        Parameters
        ----------

        target_type : str
            Search for either a comet or an asteroid, with the two valid values being,
            naturally, "comet" and "asteroid"
        updated_at : str
            Date-time when the Orbits table was last updated (YYYY-MM-DDThh:mm:ssZ). Note:
            the documentation lists this field as "orbit-updated-at", but the service
            response contained "updated_at", which appears to correlate and can also be
            used as a query parameter.
        name : str
            The object's name; e.g., Eros. This can be queried as 'Eros' or 'eros'. If
            the object has not yet been named, this field will be 'null'.
        number : integer
            The object's number; e.g., 433. If the object has not yet been numbered,
            this field will be 'null'.
        designation : str
            The object's provisional designation (e.g., 2014 AA) if it has not been
            numbered yet. If the object has been numbered, this number is its permanent
            designation and is what the 'designation' parameter will return, padded with
            leading zeroes for a total of 7 digits; e.g., '0000433'. When querying for
            provisional designations, because white spaces aren't allowed in the query,
            escape the space with either a '+' or '%20'; e.g., '2014+AA' or '2014%20AA'.
        epoch : str
            The date/time of reference for the current orbital parameters.
        epoch_jd : str
            The Julian Date of the epoch.
        period (years) : str
            Time it takes for the object to complete one orbit around the Sun.
        semimajor_axis : str
            a, one half of the longest diameter of the orbital ellipse. (AU)
        aphelion_distance : str
            The distance when the object is furthest from the Sun in its orbit. (AU)
        perihelion_distance : str
            The distance when the object is nearest to the Sun in its orbit. (AU)
        perihelion_date : str
            Date when the object is at perihelion, i.e., reaches its closest point to
            the Sun.
        perihelion_date_jd : str
            The Julian Date of perihelion.
        argument_of_perihelion (°) : str
            ω, defines the orientation of the ellipse in the orbital plane and is the
            angle from the object's ascending node to its perihelion, measured in the
            direction of motion. Range: 0–360°.
        ascending_node (°) : str
            Ω, the longitude of the ascending node, it defines the horizontal orientation
            of the ellipse with respect to the ecliptic, and is the angle measured
            counterclockwise (as seen from North of the ecliptic) from the First Point of
            Aries to the ascending node. Range: 0–360°.
        inclination (°) : str
            i, the angle between the object's orbit and the ecliptic. Range: 0–180°.
        eccentricity : str
            e, a measure of how far the orbit shape departs from a circle. Range: 0–1,
            with e = 0 being a perfect circle, intermediate values being ellipses ever
            more elongated as e increases, and e = 1 describing a parabola.
        mean_anomaly (°) : str
            M, is related to the position of the object along its orbit at the given
            epoch. Range: 0–360°.
        mean_daily_motion (°/day) : str
            n, a measure of the average speed of the object along its orbit.
        absolute_magnitude : str
            H, apparent magnitude the object would have if it were observed from 1 AU
            away at zero phase, while it was 1 AU away from the Sun. Note this is
            geometrically impossible and is equivalent to observing the object from the
            center of the Sun.
        phase_slope :  str
            G, slope parameter as calculated or assumed by the MPC. The slope parameter
            is a measure of how much brighter the object gets as its phase angle
            decreases. When not known, a value of G = 0.15 is assumed.
        orbit_type : integer
            Asteroids are classified from a dynamics perspective by the area of the Solar
            System in which they orbit. A number identifies each orbit type.
            0: Unclassified (mostly Main Belters)
            1: Atiras
            2: Atens
            3: Apollos
            4: Amors
            5: Mars Crossers
            6: Hungarias
            7: Phocaeas
            8: Hildas
            9: Jupiter Trojans
            10: Distant Objects
        delta_v (km/sec) : float
            Δv, an estimate of the amount of energy necessary to jump from LEO (Low Earth
            Orbit) to the object's orbit.
        tisserand_jupiter : float
            TJ, Tisserand parameter with respect to Jupiter, which is a quasi-invariant
            value for each object and is frequently used to distinguish objects
            (typically TJ > 3) from Jupiter-family comets (typically 2 < TJ < 3).
        neo : bool
            value = 1 flags Near Earth Objects (NEOs).
        km_neo : bool
            value = 1 flags NEOs larger than ~1 km in diameter.
        pha : bool
            value = 1 flags Potentially Hazardous Asteroids (PHAs).
        mercury_moid : float
            Minimum Orbit Intersection Distance with respect to Mercury. (AU)
        venus_moid : float
            Minimum Orbit Intersection Distance with respect to Venus. (AU)
        earth_moid : float
            Minimum Orbit Intersection Distance with respect to Earth. (AU)
        mars_moid : float
            Minimum Orbit Intersection Distance with respect to Mars. (AU)
        jupiter_moid : float
            Minimum Orbit Intersection Distance with respect to Jupiter. (AU)
        saturn_moid : float
            Minimum Orbit Intersection Distance with respect to Saturn. (AU)
        uranus_moid : float
            Minimum Orbit Intersection Distance with respect to Uranus. (AU)
        neptune_moid : float
            Minimum Orbit Intersection Distance with respect to Neptune. (AU)

        """

        self._get_mpc_object_endpoint(target_type)

        kwargs['limit'] = 1
        return self.query_objects_async(target_type, get_query_payload=get_query_payload, **kwargs)

    def query_objects_async(self, target_type, *, get_query_payload=False, **kwargs):
        """
        Query around a specific object within a given mission catalog

        The following are valid query parameters for the MPC API search. The params list and
        description are from https://minorplanetcenter.net/web_service/ and are accurate
        as of 3/6/2018:

        Parameters
        ----------
        target_type : str
            Search for either a comet or an asteroid, with the two valid values being,
            naturally, "comet" and "asteroid"
        updated_at : str
            Date-time when the Orbits table was last updated (YYYY-MM-DDThh:mm:ssZ). Note:
            the documentation lists this field as "orbit-updated-at", but the service
            response contained "updated_at", which appears to correlate and can also be
            used as a query parameter.
        name : str
            The object's name; e.g., Eros. This can be queried as 'Eros' or 'eros'. If
            the object has not yet been named, this field will be 'null'.
        number : integer
            The object's number; e.g., 433. If the object has not yet been numbered,
            this field will be 'null'.
        designation : str
            The object's provisional designation (e.g., 2014 AA) if it has not been
            numbered yet. If the object has been numbered, this number is its permanent
            designation and is what the 'designation' parameter will return, padded with
            leading zeroes for a total of 7 digits; e.g., '0000433'. When querying for
            provisional designations, because white spaces aren't allowed in the query,
            escape the space with either a '+' or '%20'; e.g., '2014+AA' or '2014%20AA'.
        epoch : str
            The date/time of reference for the current orbital parameters.
        epoch_jd : str
            The Julian Date of the epoch.
        period (years) : str
            Time it takes for the object to complete one orbit around the Sun.
        semimajor_axis : str
            a, one half of the longest diameter of the orbital ellipse. (AU)
        aphelion_distance : str
            The distance when the object is furthest from the Sun in its orbit. (AU)
        perihelion_distance : str
            The distance when the object is nearest to the Sun in its orbit. (AU)
        perihelion_date : str
            Date when the object is at perihelion, i.e., reaches its closest point to
            the Sun.
        perihelion_date_jd : str
            The Julian Date of perihelion.
        argument_of_perihelion (°) : str
            ω, defines the orientation of the ellipse in the orbital plane and is the
            angle from the object's ascending node to its perihelion, measured in the
            direction of motion. Range: 0–360°.
        ascending_node (°) : str
            Ω, the longitude of the ascending node, it defines the horizontal orientation
            of the ellipse with respect to the ecliptic, and is the angle measured
            counterclockwise (as seen from North of the ecliptic) from the First Point of
            Aries to the ascending node. Range: 0–360°.
        inclination (°) : str
            i, the angle between the object's orbit and the ecliptic. Range: 0–180°.
        eccentricity : str
            e, a measure of how far the orbit shape departs from a circle. Range: 0–1,
            with e = 0 being a perfect circle, intermediate values being ellipses ever
            more elongated as e increases, and e = 1 describing a parabola.
        mean_anomaly (°) : str
            M, is related to the position of the object along its orbit at the given
            epoch. Range: 0–360°.
        mean_daily_motion (°/day) : str
            n, a measure of the average speed of the object along its orbit.
        absolute_magnitude : str
            H, apparent magnitude the object would have if it were observed from 1 AU
            away at zero phase, while it was 1 AU away from the Sun. Note this is
            geometrically impossible and is equivalent to observing the object from the
            center of the Sun.
        phase_slope :  str
            G, slope parameter as calculated or assumed by the MPC. The slope parameter
            is a measure of how much brighter the object gets as its phase angle
            decreases. When not known, a value of G = 0.15 is assumed.
        orbit_type : integer
            Asteroids are classified from a dynamics perspective by the area of the Solar
            System in which they orbit. A number identifies each orbit type.
            0: Unclassified (mostly Main Belters)
            1: Atiras
            2: Atens
            3: Apollos
            4: Amors
            5: Mars Crossers
            6: Hungarias
            7: Phocaeas
            8: Hildas
            9: Jupiter Trojans
            10: Distant Objects
        delta_v (km/sec) : float
            Δv, an estimate of the amount of energy necessary to jump from LEO (Low Earth
            Orbit) to the object's orbit.
        tisserand_jupiter : float
            TJ, Tisserand parameter with respect to Jupiter, which is a quasi-invariant
            value for each object and is frequently used to distinguish objects
            (typically TJ > 3) from Jupiter-family comets (typically 2 < TJ < 3).
        neo : bool
            value = 1 flags Near Earth Objects (NEOs).
        km_neo : bool
            value = 1 flags NEOs larger than ~1 km in diameter.
        pha : bool
            value = 1 flags Potentially Hazardous Asteroids (PHAs).
        mercury_moid : float
            Minimum Orbit Intersection Distance with respect to Mercury. (AU)
        venus_moid : float
            Minimum Orbit Intersection Distance with respect to Venus. (AU)
        earth_moid : float
            Minimum Orbit Intersection Distance with respect to Earth. (AU)
        mars_moid : float
            Minimum Orbit Intersection Distance with respect to Mars. (AU)
        jupiter_moid : float
            Minimum Orbit Intersection Distance with respect to Jupiter. (AU)
        saturn_moid : float
            Minimum Orbit Intersection Distance with respect to Saturn. (AU)
        uranus_moid : float
            Minimum Orbit Intersection Distance with respect to Uranus. (AU)
        neptune_moid : float
            Minimum Orbit Intersection Distance with respect to Neptune. (AU)
        limit : integer
            Limit the number of results to the given value

        """
        mpc_endpoint = self._get_mpc_object_endpoint(target_type)

        if (target_type == 'comet'):
            kwargs['order_by_desc'] = "epoch"
        request_args = self._args_to_object_payload(**kwargs)

        # Return payload if requested
        if get_query_payload:
            return request_args

        self.query_type = 'object'
        auth = (self.MPC_USERNAME, self.MPC_PASSWORD)
        return self._request('GET', mpc_endpoint, params=request_args, auth=auth)

    def _get_mpc_object_endpoint(self, target_type):
        mpc_endpoint = self.MPC_URL
        if target_type == 'asteroid':
            mpc_endpoint = mpc_endpoint + '/search_orbits'
        elif target_type == 'comet':
            mpc_endpoint = mpc_endpoint + '/search_comet_orbits'
        return mpc_endpoint

    @class_or_instance
    def get_ephemeris_async(self, target, *, location='500', start=None, step='1d',
                            number=None, ut_offset=0, eph_type='equatorial',
                            ra_format=None, dec_format=None,
                            proper_motion='total', proper_motion_unit='arcsec/h',
                            suppress_daytime=False, suppress_set=False,
                            perturbed=True, unc_links=False,
                            get_query_payload=False, cache=False):
        r"""
        Object ephemerides from the Minor Planet Ephemeris Service.


        Parameters
        ----------
        target : str
            Designation of the object of interest.  See Notes for
            acceptable formats.

        location : str, array-like, or `~astropy.coordinates.EarthLocation`, optional
            Observer's location as an IAU observatory code, a
            3-element array of Earth longitude, latitude, altitude, or
            a `~astropy.coordinates.EarthLocation`.  Longitude and
            latitude should be anything that initializes an
            `~astropy.coordinates.Angle` object, and altitude should
            initialize an `~astropy.units.Quantity` object (with units
            of length).  If ``None``, then the geocenter (code 500) is
            used.

        start : str or `~astropy.time.Time`, optional
            First epoch of the ephemeris as a string (UT), or astropy
            `~astropy.time.Time`.  Strings are parsed by
            `~astropy.time.Time`.  If ``None``, then today is used.
            Valid dates span the time period 1900 Jan 1 - 2099 Dec 31
            [MPES]_.

        step : str or `~astropy.units.Quantity`, optional
            The ephemeris step size or interval in units of days,
            hours, minutes, or seconds.  Strings are parsed by
            `~astropy.units.Quantity`.  All inputs are rounded to the
            nearest integer.  Default is 1 day.

        number : int, optional
            The number of ephemeris dates to compute.  Must be ≤1441.
            If ``None``, the value depends on the units of ``step``: 21
            for days, 49 for hours, 121 for minutes, or 301 for
            seconds.

        ut_offset : int, optional
            Number of hours to offset from 0 UT for daily ephemerides.

        eph_type : str, optional
            Specify the type of ephemeris::

                equatorial: RA and Dec (default)
                heliocentric: heliocentric position and velocity vectors
                geocentric: geocentric position vector

        ra_format : dict, optional
            Format the RA column with
            `~astropy.coordinates.Angle.to_string` using these keyword
            arguments, e.g.,
            ``{'sep': ':', 'unit': 'hourangle', 'precision': 1}``.

        dec_format : dict, optional
            Format the Dec column with
            `~astropy.coordinates.Angle.to_string` using these keyword
            arguments, e.g., ``{'sep': ':', 'precision': 0}``.

        proper_motion : str, optional
            total: total motion and direction (default)
            coordinate: separate RA and Dec coordinate motion
            sky: separate RA and Dec sky motion (i.e., includes a
            cos(Dec) term).

        proper_motion_unit : string or Unit, optional
            Convert proper motion to this unit.  Must be an angular
            rate.  Default is 'arcsec/h'.

        suppress_daytime : bool, optional
            Suppress output when the Sun is above the local
            horizon. (default ``False``)

        suppress_set : bool, optional
            Suppress output when the object is below the local
            horizon. (default ``False``)

        perturbed : bool, optional
            Generate perturbed ephemerides for unperturbed orbits
            (default ``True``).

        unc_links : bool, optional
            Return columns with uncertainty map and offset links, if
            available.

        get_query_payload : bool, optional
            Return the HTTP request parameters as a dictionary
            (default: ``False``).

        cache : bool
            Defaults to False. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.


        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.


        Notes
        -----
        See the MPES user's guide [MPES]_ for details on options and
        implementation.

        MPES allows azimuths to be measured eastwards from the north
        meridian, or westwards from the south meridian.  However, the
        `~astropy.coordinates.AltAz` coordinate frame assumes
        eastwards of north.  To remain consistent with Astropy,
        eastwards of north is used.

        Acceptable target names [MPES]_ are listed in the tables below.

        .. attention:: Asteroid designations in the text version of the
           documentation may be prefixed with a backslash, which
           should be ignored.  This is to force correct rendering of
           the designation in the rendered versions of the
           documentation (e.g., HTML).

        +------------+-----------------------------------+
        | Target     | Description                       |
        +============+===================================+
        | \(3202)    | Numbered minor planet (3202)      |
        +------------+-----------------------------------+
        | 14829      | Numbered minor planet (14829)     |
        +------------+-----------------------------------+
        | 1997 XF11  | Unnumbered minor planet 1997 XF11 |
        +------------+-----------------------------------+
        | 1P         | Comet 1P/Halley                   |
        +------------+-----------------------------------+
        | C/2003 A2  | Comet C/2003 A2 (Gleason)         |
        +------------+-----------------------------------+
        | P/2003 CP7 | Comet P/2003 CP7 (LINEAR-NEAT)    |
        +------------+-----------------------------------+

        For comets, P/ and C/ are interchangeable.  The designation
        may also be in a packed format:

        +------------+-----------------------------------+
        | Target     | Description                       |
        +============+===================================+
        | 00233      | Numbered minor planet (233)       |
        +------------+-----------------------------------+
        | K03A07A    | Unnumbered minor planet 2003 AA7  |
        +------------+-----------------------------------+
        | PK03C07P   | Comet P/2003 CP7 (LINEAR-NEAT)    |
        +------------+-----------------------------------+
        | 0039P      | Comet 39P/Oterma                  |
        +------------+-----------------------------------+

        You may also search by name:

        +------------+-----------------------------------+
        | Target     | Description                       |
        +============+===================================+
        | Encke      | \(9134) Encke                     |
        +------------+-----------------------------------+
        | Africa     | \(1193) Africa                    |
        +------------+-----------------------------------+
        | Africano   | \(6391) Africano                  |
        +------------+-----------------------------------+
        | P/Encke    | 2P/Encke                          |
        +------------+-----------------------------------+
        | C/Encke    | 2P/Encke                          |
        +------------+-----------------------------------+
        | C/Gleason  | C/2003 A2 (Gleason)               |
        +------------+-----------------------------------+

        If a comet name is not unique, the first match will be
        returned.


        References
        ----------

        .. [MPES] Williams, G. The Minor Planet Ephemeris Service.
           https://minorplanetcenter.net/iau/info/MPES.pdf (retrieved
           2018 June 19).

        .. IAU Minor Planet Center.  List of Observatory codes.
           https://minorplanetcenter.net/iau/lists/ObsCodesF.html
           (retrieved 2018 June 19).


        Examples
        --------
        >>> from astroquery.mpc import MPC
        >>> tab = astroquery.mpc.MPC.get_ephemeris('(24)', location=568,
        ...            start='2003-02-26', step='100d', number=3)  # doctest: +SKIP
        >>> print(tab)  # doctest: +SKIP

        """

        # parameter checks
        if type(location) not in (str, int, EarthLocation):
            if hasattr(location, '__iter__'):
                if len(location) != 3:
                    raise ValueError(
                        "location arrays require three values:"
                        " longitude, latitude, and altitude")
            else:
                raise TypeError(
                    "location must be a string, integer, array-like,"
                    " or astropy EarthLocation")

        if start is not None:
            _start = Time(start)
        else:
            _start = None

        # step must be one of these units, and must be an integer (we
        # will convert to an integer later).  MPES fails for large
        # integers, so we cannot just convert everything to seconds.
        _step = u.Quantity(step)
        if _step.unit not in [u.d, u.h, u.min, u.s]:
            raise ValueError(
                'step must have units of days, hours, minutes, or seconds.')

        if number is not None:
            if number > 1441:
                raise ValueError('number must be <=1441')

        if eph_type not in self._ephemeris_types.keys():
            raise ValueError("eph_type must be one of {}".format(
                self._ephemeris_types.keys()))

        if proper_motion not in self._proper_motions.keys():
            raise ValueError("proper_motion must be one of {}".format(
                self._proper_motions.keys()))

        if not u.Unit(proper_motion_unit).is_equivalent('rad/s'):
            raise ValueError("proper_motion_unit must be an angular rate.")

        # setup payload
        request_args = self._args_to_ephemeris_payload(
            target=target, ut_offset=ut_offset, suppress_daytime=suppress_daytime,
            suppress_set=suppress_set, perturbed=perturbed, location=location,
            start=_start, step=_step, number=number, eph_type=eph_type,
            proper_motion=proper_motion)

        # store for retrieval in _parse_result
        self._ra_format = ra_format
        self._dec_format = dec_format
        self._proper_motion_unit = u.Unit(proper_motion_unit)
        self._unc_links = unc_links

        if get_query_payload:
            return request_args

        self.query_type = 'ephemeris'
        response = self._request('POST', self.MPES_URL, data=request_args, cache=cache)

        return response

    @class_or_instance
    def get_observatory_codes_async(self, *, cache=True):
        """
        Table of observatory codes from the IAU Minor Planet Center.


        Parameters
        ----------

        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.


        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.


        References
        ----------
        .. IAU Minor Planet Center.  List of Observatory codes.
           https://minorplanetcenter.net/iau/lists/ObsCodesF.html
           (retrieved 2018 June 19).


        Examples
        --------
        >>> from astroquery.mpc import MPC
        >>> obs = MPC.get_observatory_codes()  # doctest: +SKIP
        >>> print(obs[295])  # doctest: +SKIP
        Code Longitude   cos       sin         Name
        ---- --------- -------- --------- -------------
        309 289.59569 0.909943 -0.414336 Cerro Paranal

        """

        self.query_type = 'observatory_code'
        response = self._request('GET', self.OBSERVATORY_CODES_URL,
                                 timeout=self.TIMEOUT, cache=cache)

        return response

    @class_or_instance
    def get_observatory_location(self, code, *, cache=True):
        """
        IAU observatory location.


        Parameters
        ----------
        code : string
            Three-character IAU observatory code.

        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.


        Returns
        -------
        longitude : Angle
            Observatory longitude (east of Greenwich).

        cos : float
            Parallax constant ``rho * cos(phi)`` where ``rho`` is the
            geocentric distance in earth radii, and ``phi`` is the
            geocentric latitude.

        sin : float
            Parallax constant ``rho * sin(phi)``.

        name : string
            The name of the observatory.


        Raises
        ------
        LookupError
            If `code` is not found in the MPC table.


        Examples
        --------
        >>> from astroquery.mpc import MPC
        >>> obs = MPC.get_observatory_location('000')
        >>> print(obs)  # doctest: +SKIP
        (<Angle 0. deg>, 0.62411, 0.77873, 'Greenwich')

        """

        if not isinstance(code, str):
            raise TypeError('code must be a string')
        if len(code) != 3:
            raise ValueError('code must be three charaters long')
        tab = self.get_observatory_codes(cache=cache)
        for row in tab:
            if row[0] == code:
                return Angle(row[1], 'deg'), row[2], row[3], row[4]
        raise LookupError('{} not found'.format(code))

    def _args_to_object_payload(self, **kwargs):
        request_args = kwargs
        kwargs['json'] = 1
        return_fields = kwargs.pop('return_fields', None)
        if return_fields:
            kwargs['return'] = return_fields

        return request_args

    def _args_to_ephemeris_payload(self, **kwargs):
        request_args = {
            'ty': 'e',
            'TextArea': str(kwargs['target']),
            'uto': str(kwargs['ut_offset']),
            'igd': 'y' if kwargs['suppress_daytime'] else 'n',
            'ibh': 'y' if kwargs['suppress_set'] else 'n',
            'fp': 'y' if kwargs['perturbed'] else 'n',
            'adir': 'N',  # always measure azimuth eastward from north
            'tit': '',  # dummy page title
            'bu': ''  # dummy base URL
        }

        location = kwargs['location']
        if isinstance(location, str):
            request_args['c'] = location
        elif isinstance(location, int):
            request_args['c'] = '{:03d}'.format(location)
        elif isinstance(location, EarthLocation):
            loc = location.geodetic
            request_args['long'] = loc[0].deg
            request_args['lat'] = loc[1].deg
            request_args['alt'] = loc[2].to(u.m).value
        elif hasattr(location, '__iter__'):
            request_args['long'] = Angle(location[0]).deg
            request_args['lat'] = Angle(location[1]).deg
            request_args['alt'] = u.Quantity(location[2]).to('m').value

        if kwargs['start'] is None:
            _start = Time.now()
            _start.precision = 0  # integer seconds
            request_args['d'] = _start.iso.replace(':', '')
        else:
            _start = Time(kwargs['start'], precision=0,
                          scale='utc')  # integer seconds
            request_args['d'] = _start.iso.replace(':', '')

        request_args['i'] = str(int(round(kwargs['step'].value)))
        request_args['u'] = str(kwargs['step'].unit)[:1]
        if kwargs['number'] is None:
            request_args['l'] = self._default_number_of_steps[
                request_args['u']]
        else:
            request_args['l'] = kwargs['number']

        request_args['raty'] = self._ephemeris_types[kwargs['eph_type']]
        request_args['s'] = self._proper_motions[kwargs['proper_motion']]
        request_args['m'] = 'h'  # always return proper_motion as arcsec/hr

        return request_args

    @class_or_instance
    @deprecated_renamed_argument("get_raw_response", None, since="0.4.8",
                                 alternative="async methods")
    def get_observations_async(self, targetid, *,
                               id_type=None,
                               get_mpcformat=False,
                               get_raw_response=False,
                               get_query_payload=False,
                               cache=True):
        """
        Obtain all reported observations for an asteroid or a comet
        from the `Minor Planet Center observations database
        <https://minorplanetcenter.net/db_search>`_.

        .. deprecated:: 0.4.8
           The ``get_raw_response`` keyword argument is deprecated.  The
           `~MPCClass.get_observations_async` method will return a raw response.


        Parameters
        ----------
        targetid : int or str
            Official target number or
            designation. If a number is provided (either as int or
            str), the input is interpreted as an asteroid number;
            asteroid designations are interpreted as such (note that a
            whitespace between the year and the remainder of the
            designation is required and no packed designations are
            allowed). To query a periodic comet number, you have to
            append ``'P'``, e.g., ``'234P'``. To query any comet
            designation, the designation has to start with a letter
            describing the comet type and a slash, e.g., ``'C/2018 E1'``.
            Comet or asteroid names, Palomar-Leiden Survey
            designations, and individual comet fragments cannot be
            queried.

        id_type : str, optional
            Manual override for identifier type. If ``None``, the
            identifier type is derived by parsing ``targetid``; if this
            automated classification fails, it can be set manually using
            this parameter. Possible values are ``'asteroid number'``,
            ``'asteroid designation'``, ``'comet number'``, and
            ``'comet designation'``. Default: ``None``

        get_mpcformat : bool, optional
            If ``True``, this method will return an `~astropy.table.QTable`
            with only a single column holding the original MPC 80-column
            observation format. Default: ``False``

        get_raw_response : bool, optional
            If ``True``, this method will return the raw output from the
            MPC servers (json). Default: ``False``

        get_query_payload : bool, optional
            Return the HTTP request parameters as a dictionary
            (default: ``False``).

        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.


        Raises
        ------
        RuntimeError
            If query did not return any data.

        ValueError
            If target name could not be parsed properly and target type
            could not be identified.


        Notes
        -----
        The following quantities are included in the output table

        +-------------------+--------------------------------------------+
        | Column Name       | Definition                                 |
        +===================+============================================+
        | ``number``        | official IAU target number (int)           |
        +-------------------+--------------------------------------------+
        | ``desig``         | provisional target designation (str)       |
        +-------------------+--------------------------------------------+
        | ``discovery`` (*) | target discovery flag (str)                |
        +-------------------+--------------------------------------------+
        | ``comettype`` (*) | orbital type of comet (str)                |
        +-------------------+--------------------------------------------+
        | ``note1`` (#)     | Note1 (str)                                |
        +-------------------+--------------------------------------------+
        | ``note2`` (#)     | Note2 (str)                                |
        +-------------------+--------------------------------------------+
        | ``epoch``         | epoch of observation (Julian Date, float)  |
        +-------------------+--------------------------------------------+
        | ``RA``            | RA reported (J2000, deg, float)            |
        +-------------------+--------------------------------------------+
        | ``DEC``           | declination reported (J2000, deg, float)   |
        +-------------------+--------------------------------------------+
        | ``mag``           | reported magnitude (mag, float)            |
        +-------------------+--------------------------------------------+
        | ``band`` (*)      | photometric band for ``mag`` (str)         |
        +-------------------+--------------------------------------------+
        | ``phottype`` (*)  | comet photometry type (nuclear/total, str) |
        +-------------------+--------------------------------------------+
        | ``catalog`` (!)   | star catalog used in the observation (str) |
        +-------------------+--------------------------------------------+
        | ``observatory``   | IAU observatory code (str)                 |
        +-------------------+--------------------------------------------+

        (*): Column names are optional and
        depend on whether an asteroid or a comet has been queried.

        (#): Parameters ``Note1`` and ``Note2`` are defined in the
        `MPC 80-column format description
        <https://minorplanetcenter.net/iau/info/OpticalObs.html>`_

        (!): `Description of star catalog codes
        <https://minorplanetcenter.net/iau/info/OpticalObs.html>`_


        Examples
        --------
        >>> from astroquery.mpc import MPC
        >>> MPC.get_observations(12893)  # doctest: +SKIP
        <QTable length=2772>
        number   desig   discovery note1 ... band catalog observatory
                                         ...
        int32     str9      str1    str1 ... str1   str1      str3
        ------ --------- --------- ----- ... ---- ------- -----------
         12893 1998 QS55        --    -- ...   --      --         413
         12893 1998 QS55        --    -- ...   --      --         413
         12893 1998 QS55         *     4 ...   --      --         809
         12893 1998 QS55        --     4 ...   --      --         809
         12893 1998 QS55        --     4 ...   --      --         809
           ...       ...       ...   ... ...  ...     ...         ...
         12893 1998 QS55        --    -- ...    o       V         T05
         12893 1998 QS55        --    -- ...    o       V         M22
         12893 1998 QS55        --    -- ...    o       V         M22
         12893 1998 QS55        --    -- ...    o       V         M22
         12893 1998 QS55        --    -- ...    o       V         M22
        """

        request_payload = {'table': 'observations'}

        if id_type is None:

            pat = ('(^[0-9]*$)|'  # [0] asteroid number
                   '(^[0-9]{1,3}[PIA]$)'  # [1] periodic comet number
                   '(-[1-9A-Z]{0,2})?$|'  # [2] fragment
                   '(^[PDCXAI]/[- 0-9A-Za-z]*)'
                   # [3] comet designation
                   '(-[1-9A-Z]{0,2})?$|'  # [4] fragment
                   '(^([1A][8-9][0-9]{2}[ _][A-Z]{2}[0-9]{0,3}$|'
                   '^20[0-9]{2}[ _][A-Z]{2}[0-9]{0,3}$)|'
                   '(^[1-9][0-9]{3}[ _](P-L|T-[1-3]))$)'
                   # asteroid designation [5] (old/new/Palomar-Leiden style)
                   )

            # comet fragments are extracted here, but the MPC server does
            # not allow for fragment-based queries

            m = re.findall(pat, str(targetid))

            if len(m) == 0:
                raise ValueError(('Cannot interpret target '
                                  'identifier "{}".').format(targetid))
            else:
                m = m[0]

            request_payload['object_type'] = 'M'
            if m[1] != '':
                request_payload['object_type'] = 'P'
            if m[3] != '':
                request_payload['object_type'] = m[3][0]

            if m[0] != '':
                request_payload['number'] = m[0]  # asteroid number
            elif m[1] != '':
                request_payload['number'] = m[1][:-1]  # per.  comet number
            elif m[3] != '':
                request_payload['designation'] = m[3]  # comet designation
            elif m[5] != '':
                request_payload['designation'] = m[5]  # ast. designation
        else:
            if 'asteroid' in id_type:
                request_payload['object_type'] = 'M'
                if 'number' in id_type:
                    request_payload['number'] = str(targetid)
                elif 'designation' in id_type:
                    request_payload['designation'] = targetid
            if 'comet' in id_type:
                pat = ('(^[0-9]{1,3}[PIA])|'  # [0] number
                       '(^[PDCXAI]/[- 0-9A-Za-z]*)'  # [1] designation
                       )
                m = re.findall(pat, str(targetid))

                if len(m) == 0:
                    raise ValueError(('Cannot parse comet type '
                                      'from "{}".').format(targetid))
                else:
                    m = m[0]

                if m[0] != '':
                    request_payload['object_type'] = m[0][-1]
                elif m[1] != '':
                    request_payload['object_type'] = m[1][0]

                if 'number' in id_type:
                    request_payload['number'] = targetid[:-1]
                elif 'designation' in id_type:
                    request_payload['designation'] = targetid

        self.query_type = 'observations'

        if get_query_payload:
            return request_payload

        response = self._request('GET', url=self.MPCOBS_URL,
                                 params=request_payload,
                                 auth=(self.MPC_USERNAME,
                                       self.MPC_PASSWORD),
                                 timeout=self.TIMEOUT, cache=cache)

        if get_mpcformat:
            self.obsformat = 'mpc'
        else:
            self.obsformat = 'table'

        if get_raw_response:
            self.get_raw_response = True
        else:
            self.get_raw_response = False

        return response

    def _parse_result(self, result, **kwargs):
        if self.query_type == 'object':
            try:
                data = result.json()
            except ValueError:
                raise InvalidQueryError(result.text)
            return data
        elif self.query_type == 'observatory_code':
            root = BeautifulSoup(result.content, 'html.parser')
            text_table = root.find('pre').text
            start = text_table.index('000')
            text_table = text_table[start:]

            # parse table ourselves to make sure the code column is a
            # string and that blank cells are masked
            rows = []
            for line in text_table.splitlines():
                lon = line[4:13]
                if len(lon.strip()) == 0:
                    lon = np.nan
                else:
                    lon = float(lon)

                c = line[13:21]
                if len(c.strip()) == 0:
                    c = np.nan
                else:
                    c = float(c)

                s = line[21:30]
                if len(s.strip()) == 0:
                    s = np.nan
                else:
                    s = float(s)

                rows.append((line[:3], lon, c, s, line[30:]))

            tab = Table(rows=rows,
                        names=('Code', 'Longitude', 'cos', 'sin', 'Name'),
                        dtype=(str, float, float, float, str),
                        masked=True)
            tab['Longitude'].mask = ~np.isfinite(tab['Longitude'])
            tab['cos'].mask = ~np.isfinite(tab['cos'])
            tab['sin'].mask = ~np.isfinite(tab['sin'])

            return tab
        elif self.query_type == 'ephemeris':
            content = result.content.decode()
            table_start = content.find('<pre>')
            if table_start == -1:
                raise InvalidQueryError(BeautifulSoup(content, "html.parser").get_text())
            table_end = content.find('</pre>')
            text_table = content[table_start + 5:table_end]
            SKY = 'raty=a' in result.request.body
            HELIOCENTRIC = 'raty=s' in result.request.body
            GEOCENTRIC = 'raty=G' in result.request.body

            # columns = '\n'.join(text_table.splitlines()[:2])
            # find column headings
            if SKY:
                # slurp to newline after "h m s"
                # raise EmptyResponseError if no ephemeris lines are found in the query response
                try:
                    i = text_table.index('\n', text_table.index('h m s')) + 1
                except ValueError:
                    raise EmptyResponseError(content)
                columns = text_table[:i]
                data_start = columns.count('\n') - 1
            else:
                # slurp to newline after "JD_TT"
                # raise EmptyResponseError if no ephemeris lines are found in the query response
                try:
                    i = text_table.index('\n', text_table.index('JD_TT')) + 1
                except ValueError:
                    raise EmptyResponseError(content)
                columns = text_table[:i]
                data_start = columns.count('\n') - 1

            first_row = text_table.splitlines()[data_start + 1]

            if SKY:
                names = ('Date', 'RA', 'Dec', 'Delta',
                         'r', 'Elongation', 'Phase', 'V')
                col_starts = (0, 18, 29, 39, 47, 56, 62, 69)
                col_ends = (17, 28, 38, 46, 55, 61, 68, 72)
                units = (None, None, None, 'au', 'au', 'deg', 'deg', 'mag')

                if 's=t' in result.request.body:    # total motion
                    names += ('Proper motion', 'Direction')
                    units += ('arcsec/h', 'deg')
                elif 's=c' in result.request.body:  # coord Motion
                    names += ('dRA', 'dDec')
                    units += ('arcsec/h', 'arcsec/h')
                elif 's=s' in result.request.body:  # sky Motion
                    names += ('dRA cos(Dec)', 'dDec')
                    units += ('arcsec/h', 'arcsec/h')
                col_starts += (73, 82)
                col_ends += (81, 91)

                if 'Moon' in columns:
                    # table includes Alt, Az, Sun and Moon geometry
                    names += ('Azimuth', 'Altitude', 'Sun altitude', 'Moon phase',
                              'Moon distance', 'Moon altitude')
                    col_starts += tuple((col_ends[-1] + offset for offset in
                                        (1, 8, 13, 19, 26, 32)))
                    col_ends += tuple((col_ends[-1] + offset for offset in
                                      (7, 12, 18, 25, 31, 36)))
                    units += ('deg', 'deg', 'deg', None, 'deg', 'deg')
                if 'Uncertainty' in columns:
                    names += ('Uncertainty 3sig', 'Unc. P.A.')
                    col_starts += tuple((col_ends[-1] + offset for offset in
                                         (1, 10)))
                    col_ends += tuple((col_ends[-1] + offset for offset in
                                       (9, 15)))
                    units += ('arcsec', 'deg')
                if ">Map</a>" in first_row and self._unc_links:
                    names += ('Unc. map', 'Unc. offsets')
                    col_starts += (first_row.index(' / <a') + 3, )
                    col_starts += (
                        first_row.index(' / <a', col_starts[-1]) + 3, )
                    # Unc. offsets is always last
                    col_ends += (col_starts[-1] - 3,
                                 first_row.rindex('</a>') + 4)
                    units += (None, None)
            elif HELIOCENTRIC:
                names = ('Object', 'JD', 'X', 'Y', 'Z', "X'", "Y'", "Z'")
                col_starts = (0, 12, 28, 45, 61, 77, 92, 108)
                col_ends = None
                units = (None, None, 'au', 'au', 'au', 'au/d', 'au/d', 'au/d')
            elif GEOCENTRIC:
                names = ('Object', 'JD', 'X', 'Y', 'Z')
                col_starts = (0, 12, 28, 45, 61)
                col_ends = None
                units = (None, None, 'au', 'au', 'au')

            tab = ascii.read(text_table, format='fixed_width_no_header',
                             names=names, col_starts=col_starts,
                             col_ends=col_ends, data_start=data_start,
                             fill_values=(('N/A', np.nan),), fast_reader=False)

            for col, unit in zip(names, units):
                tab[col].unit = unit

            # Time for dates, Angle for RA and Dec; convert columns at user's request
            if SKY:
                # convert from MPES string to Time, MPES uses UT timescale
                tab['Date'] = Time(['{}-{}-{} {}:{}:{}'.format(
                    d[:4], d[5:7], d[8:10], d[11:13], d[13:15], d[15:17])
                    for d in tab['Date']], scale='utc')

                # convert from MPES string:
                ra = Angle(tab['RA'], unit='hourangle').to('deg')
                dec = Angle(tab['Dec'], unit='deg')

                # optionally convert back to a string
                if self._ra_format is not None:
                    ra_unit = self._ra_format.get('unit', ra.unit)
                    ra = ra.to_string(**self._ra_format)
                else:
                    ra_unit = ra.unit

                if self._dec_format is not None:
                    dec_unit = self._dec_format.get('unit', dec.unit)
                    dec = dec.to_string(**self._dec_format)
                else:
                    dec_unit = dec.unit

                # replace columns
                tab.remove_columns(('RA', 'Dec'))
                tab.add_column(Column(ra, name='RA', unit=ra_unit), index=1)
                tab.add_column(Column(dec, name='Dec', unit=dec_unit), index=2)

                # convert proper motion columns
                for col in ('Proper motion', 'dRA', 'dRA cos(Dec)', 'dDec'):
                    if col in tab.colnames:
                        tab[col].convert_unit_to(self._proper_motion_unit)
            else:
                # convert from MPES string to Time
                tab['JD'] = Time(tab['JD'], format='jd', scale='tt')
            return tab

        elif self.query_type == 'observations':

            warnings.simplefilter("ignore", ErfaWarning)

            try:
                src = json.loads(result.text)
            except (ValueError, json.decoder.JSONDecodeError):
                raise RuntimeError(
                    'Server response not readable: "{}"'.format(
                        result.text))

            if len(src) == 0:
                raise EmptyResponseError(('No data queried. Are the target '
                                          'identifiers correct?  Is the MPC '
                                          'database search working for your '
                                          'object? The service is hosted at '
                                          'https://www.minorplanetcenter.net/'
                                          'search_db'))

            # return raw response if requested
            if self.get_raw_response:
                return src

            # return raw 80-column observation format if requested
            if self.obsformat == 'mpc':
                tab = Table([[o['original_record'] for o in src]])
                tab.rename_column('col0', 'obs')
                return tab

            if all([o['object_type'] == 'M' for o in src]):
                # minor planets (asteroids)
                data = ascii.read("\n".join([o['original_record']
                                             for o in src]),
                                  format='fixed_width_no_header',
                                  names=('number', 'pdesig', 'discovery',
                                         'note1', 'note2', 'epoch',
                                         'RA', 'DEC', 'mag', 'band',
                                         'catalog', 'observatory'),
                                  col_starts=(0, 5, 12, 13, 14, 15,
                                              32, 44, 65, 70, 71, 77),
                                  col_ends=(4, 11, 12, 13, 14, 31,
                                            43, 55, 69, 70, 71, 79),
                                  fast_reader=False)

                # convert asteroid designations
                # old designation style, e.g.: 1989AB
                ident = data['pdesig'][0]
                if isinstance(ident, np.ma.masked_array) and ident.mask:
                    ident = ''
                elif (len(ident) < 7 and ident[:4].isdigit()
                        and ident[4:6].isalpha()):
                    ident = ident[:4]+' '+ident[4:6]
                # Palomar Survey
                elif 'PLS' in ident:
                    ident = ident[3:] + " P-L"
                # Trojan Surveys
                elif 'T1S' in ident:
                    ident = ident[3:] + " T-1"
                elif 'T2S' in ident:
                    ident = ident[3:] + " T-2"
                elif 'T3S' in ident:
                    ident = ident[3:] + " T-3"
                # standard MPC packed 7-digit designation
                elif (ident[0].isalpha() and ident[1:3].isdigit()
                      and ident[-1].isalpha() and ident[-2].isdigit()):
                    yr = str(conf.pkd.find(ident[0]))+ident[1:3]
                    let = ident[3]+ident[-1]
                    num = str(conf.pkd.find(ident[4]))+ident[5]
                    num = num.lstrip("0")
                    ident = yr+' '+let+num
                data.add_column(Column([ident]*len(data), name='desig'),
                                index=1)
                data.remove_column('pdesig')

            elif all([o['object_type'] != 'M' for o in src]):
                # comets
                data = ascii.read("\n".join([o['original_record']
                                             for o in src]),
                                  format='fixed_width_no_header',
                                  names=('number', 'comettype', 'desig',
                                         'note1', 'note2', 'epoch',
                                         'RA', 'DEC', 'mag', 'phottype',
                                         'catalog', 'observatory'),
                                  col_starts=(0, 4, 5, 13, 14, 15,
                                              32, 44, 65, 70, 71, 77),
                                  col_ends=(3, 4, 12, 13, 14, 31,
                                            43, 55, 69, 70, 71, 79),
                                  fast_reader=False)

                # convert comet designations
                ident = data['desig'][0]

                if (not isinstance(ident, (np.ma.masked_array,
                                           np.ma.core.MaskedConstant))
                        or not ident.mask):
                    yr = str(conf.pkd.find(ident[0]))+ident[1:3]
                    let = ident[3]
                    # patch to parse asteroid designations
                    if len(ident) == 7 and str.isalpha(ident[6]):
                        let += ident[6]
                        ident = ident[:6] + ident[7:]
                    num = str(conf.pkd.find(ident[4]))+ident[5]
                    num = num.lstrip("0")
                    if len(ident) >= 7:
                        frag = ident[6] if ident[6] != '0' else ''
                    else:
                        frag = ''
                    ident = yr+' '+let+num+frag
                    # remove and add desig column to overcome length limit
                    data.remove_column('desig')
                    data.add_column(Column([ident]*len(data),
                                           name='desig'), index=3)
            else:
                raise ValueError(('Object type is ambiguous. "{}" '
                                  'are present.').format(
                                      set([o['object_type'] for o in src])))

            # convert dates to Julian Dates
            dates = [d[:10].replace(' ', '-') for d in data['epoch']]
            times = np.array([float(d[10:]) for d in data['epoch']])
            jds = Time(dates, format='iso').jd+times
            data['epoch'] = jds

            # convert ra and dec to degrees
            coo = SkyCoord(ra=data['RA'], dec=data['DEC'],
                           unit=(u.hourangle, u.deg),
                           frame='icrs')
            data['RA'] = coo.ra.deg
            data['DEC'] = coo.dec.deg

        # convert Table to QTable
        data = QTable(data)
        data['epoch'].unit = u.d
        data['RA'].unit = u.deg
        data['DEC'].unit = u.deg

        # Masked quantities are not supported in older astropy, warnings are raised for <v5.0
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='dropping mask in Quantity column',
                                    category=UserWarning)
            data['mag'].unit = u.mag

        return data


MPC = MPCClass()
