# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

import numpy as np
from astropy.io import ascii
from astropy.time import Time
from astropy.table import Table, Column
import astropy.units as u
from astropy.coordinates import EarthLocation, Angle

from ..query import BaseQuery
from . import conf
from ..utils import async_to_sync, class_or_instance
from ..exceptions import InvalidQueryError


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
    OBSERVATORY_CODES_URL = ('https://' + conf.web_service_server +
                             '/iau/lists/ObsCodes.html')
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
        super(MPCClass, self).__init__()

    def query_object_async(self, target_type, get_query_payload=False, *args, **kwargs):
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

        mpc_endpoint = self.get_mpc_object_endpoint(target_type)

        kwargs['limit'] = 1
        return self.query_objects_async(target_type, get_query_payload, *args, **kwargs)

    def query_objects_async(self, target_type, get_query_payload=False, *args, **kwargs):
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
        mpc_endpoint = self.get_mpc_object_endpoint(target_type)

        if (target_type == 'comet'):
            kwargs['order_by_desc'] = "epoch"
        request_args = self._args_to_object_payload(**kwargs)

        # Return payload if requested
        if get_query_payload:
            return request_args

        self.query_type = 'object'
        auth = (self.MPC_USERNAME, self.MPC_PASSWORD)
        return self._request('GET', mpc_endpoint, params=request_args, auth=auth)

    def get_mpc_object_endpoint(self, target_type):
        mpc_endpoint = self.MPC_URL
        if target_type == 'asteroid':
            mpc_endpoint = mpc_endpoint + '/search_orbits'
        elif target_type == 'comet':
            mpc_endpoint = mpc_endpoint + '/search_comet_orbits'
        return mpc_endpoint

    @class_or_instance
    def get_ephemeris_async(self, target, location='500', start=None, step='1d',
                            number=None, ut_offset=0, eph_type='equatorial',
                            ra_format=None, dec_format=None,
                            proper_motion='total', proper_motion_unit='arcsec/h',
                            suppress_daytime=False, suppress_set=False,
                            perturbed=True, unc_links=False,
                            get_query_payload=False,
                            get_raw_response=False, cache=False):
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

        get_raw_response : bool, optional
            Return raw data without parsing into a table (default:
            ``False``).

        cache : bool, optional
            Cache results or use cached results (default: ``False``).


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

        For comets, P/ and C/ are interchangable.  The designation
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
        response = self._request('POST', self.MPES_URL, data=request_args)

        return response

    @class_or_instance
    def get_observatory_codes_async(self, get_raw_response=False, cache=True):
        """
        Table of observatory codes from the IAU Minor Planet Center.


        Parameters
        ----------
        get_raw_response : bool, optional
            Return raw data without parsing into a table (default:
            `False`).

        cache : bool, optional
            Cache results or use cached results (default: `True`).


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
    def get_observatory_location(self, code, cache=True):
        """
        IAU observatory location.


        Parameters
        ----------
        code : string
            Three-character IAU observatory code.

        cache : bool, optional
            Cache observatory table or use cached results (default:
            `True`).


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
                raise InvalidQueryError(content)
            table_end = content.find('</pre>')
            text_table = content[table_start + 5:table_end]

            SKY = 'raty=a' in result.request.body
            HELIOCENTRIC = 'raty=s' in result.request.body
            GEOCENTRIC = 'raty=G' in result.request.body

            # columns = '\n'.join(text_table.splitlines()[:2])
            # find column headings
            if SKY:
                # slurp to newline after "h m s"
                i = text_table.index('\n', text_table.index('h m s')) + 1
                columns = text_table[:i]
                data_start = columns.count('\n') - 1
            else:
                # slurp to newline after "JD_TT"
                i = text_table.index('\n', text_table.index('JD_TT')) + 1
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
                col_starts += (73, 81)
                col_ends += (80, 89)

                if 'Moon' in columns:
                    # table includes Alt, Az, Sun and Moon geometry
                    names += ('Azimuth', 'Altitude', 'Sun altitude', 'Moon phase',
                              'Moon distance', 'Moon altitude')
                    col_starts += tuple((col_ends[-1] + offset for offset in
                                         (2, 9, 14, 20, 27, 33)))
                    col_ends += tuple((col_ends[-1] + offset for offset in
                                       (8, 13, 19, 26, 32, 37)))
                    units += ('deg', 'deg', 'deg', None, 'deg', 'deg')
                if 'Uncertainty' in columns:
                    names += ('Uncertainty 3sig', 'Unc. P.A.')
                    col_starts += tuple((col_ends[-1] + offset for offset in
                                         (2, 11)))
                    col_ends += tuple((col_ends[-1] + offset for offset in
                                       (10, 16)))
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
                             fill_values=(('N/A', np.nan),))

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


MPC = MPCClass()
