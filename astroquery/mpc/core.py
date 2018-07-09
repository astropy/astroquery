# -*- coding: utf-8 -*-

from ..query import BaseQuery
from . import conf
from ..utils import async_to_sync

__all__ = ['MPCClass']


@async_to_sync
class MPCClass(BaseQuery):
    MPC_URL = 'http://' + conf.server + '/web_service'
    # The authentication credentials for the MPC web service are publicly
    # available and can be openly viewed on the documentation page at
    # https://minorplanetcenter.net/web_service/
    MPC_USERNAME = 'mpc_ws'
    MPC_PASSWORD = 'mpc!!ws'

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

        mpc_endpoint = self.get_mpc_endpoint(target_type)

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
        mpc_endpoint = self.get_mpc_endpoint(target_type)

        if (target_type == 'comet'):
            kwargs['order_by_desc'] = "epoch"
        request_args = self._args_to_payload(**kwargs)

        # Return payload if requested
        if get_query_payload:
            return request_args

        auth = (self.MPC_USERNAME, self.MPC_PASSWORD)
        return self._request('GET', mpc_endpoint, params=request_args, auth=auth)

    def _args_to_payload(self, **kwargs):
        request_args = kwargs
        kwargs['json'] = 1
        return_fields = kwargs.pop('return_fields', None)
        if return_fields:
            kwargs['return'] = return_fields
        return request_args

    def get_mpc_endpoint(self, target_type):
        mpc_endpoint = self.MPC_URL
        if target_type == 'asteroid':
            mpc_endpoint = mpc_endpoint + '/search_orbits'
        elif target_type == 'comet':
            mpc_endpoint = mpc_endpoint + '/search_comet_orbits'
        return mpc_endpoint

    _ephemeris_types = {
        'equatorial': 'a',
        'heliocentric': 's',
        'geocentric': 'G'
    }

    _default_number_of_steps = {
        'd': 21,
        'h': 49,
        'm': 121,
        's': 301
    }

    _proper_motions = {
        'total': 't',
        'coordinate': 'c',
        'sky': 's'
    }

    def query_ephemeris_async(self, target, location='500', start=None, step='1d',
                              number=None, utoffset=0, eph_type='equatorial',
                              proper_motion='total', suppress_daytime=False,
                              suppress_set=False, perturbed=True, **kwargs):
        """Query the Minor Planet Ephemeris Service for ephemerides.

        Parameters
        ----------
        target : str
            Designation of the object of interest.  See Notes for
            acceptable formats.

        location : str, array-like, or EarthLocation, optional
            Observer's location as an IAU observatory code[2]_, a
            3-element array of Earth longitude, latitude, altitude
            (degrees and meters, or astropy units), or an astropy
            `EarthLocation`.  If `None`, then the geocenter (code 500)
            is used.

        start : str or Time, optional
            First epoch of the ephemeris as a string (UT), or astropy
            `Time`.  If `None`, then today is used.  Valid dates span
            the time period 1900 Jan 1 - 2099 Dec 31 [1]_.  See Notes
            for acceptable string forms.

        step : str or Quantity, optional
            The ephemeris step size or interval in units of days,
            hours, minutes, or seconds.  Strings are parsed by
            `astropy.units.Quantity`.  All inputs are rounded to the
            nearest integer.  Default is 1 day.

        number : int, optional
            The number of ephemeris dates to compute.  Must be ≤1441.
            If `None`, the value depends on the units of `step`: 21
            for days, 49 for hours, 121 for minutes, or 301 for
            seconds.

        utoffset : int, optional
            Number of hours to offset from 0 UT for daily ephemerides.

        eph_type : str, optional
            Specify the type of ephemeris:
                equatorial: RA and Dec (default)
                heliocentric: heliocentric position and velocity
                    vectors
                geocentric: geocentric position vector

        proper_motion : str, optional
            total: total motion and direction (default)
            coordinate: separate RA and Dec coordinate motion
            sky: separate RA and Dec sky motion (i.e., includes a
                cos(Dec) term).

        suppress_daytime : bool, optional
            Suppress output when the Sun is above the local
            horizon. (default `False`)

        suppress_set : bool, optional
            Suppress output when the object is below the local
            horizon. (default `False`)

        perturbed : bool, optional
            Generate perturbed ephemerides for unperturbed orbits
            (default `False`).

        Notes
        -----
        See the MPES user's guide[1]_ for details on options and
        implementation.

        MPES allows azimuths to be measured eastwards from the north
        meridian, or westwards from the south meridian.  However,
        `astropy`'s `AltAz` coordinate frame assumes eastwards of
        north.  To remain consistent with `astropy`, eastwards of
        north is used.

        Acceptable target names:

            +------------+-----------------------------------+
            | Target     | Description                       |
            +============+===================================+
            | (3202)     | Numbered minor planet (3202)      |
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
            | Encke      | (9134) Encke                      |
            +------------+-----------------------------------+
            | Africa     | (1193) Africa                     |
            +------------+-----------------------------------+
            | Africano   | (6391) Africano                   |
            +------------+-----------------------------------+
            | P/Encke    | 2P/Encke                          |
            +------------+-----------------------------------+
            | C/Encke    | 2P/Encke                          |
            +------------+-----------------------------------+
            | C/Gleason  | C/2003 A2 (Gleason)               |
            +------------+-----------------------------------+

            If a comet name is not unique, the first match will be
            returned.

        Acceptable date strings:

            +---------------------+------------------------------+
            | Start               | Date                         |
            +=====================+==============================+
            | 2003 06 10          | 0h UT on 2003 June 10        |
            +---------------------+------------------------------+
            | 1965 12 10.5        | 12h UT on 1965 Dec. 10       |
            +---------------------+------------------------------+
            | 1903 09 10 12       | 12h UT on 1903 Sept. 10      |
            +---------------------+------------------------------+
            | 2003 July 10        | 0h UT on 2003 July 10        |
            +---------------------+------------------------------+
            | 2023 June 10.75     | 18h UT on 2023 June 10       |
            +---------------------+------------------------------+
            | 1998 Jan. 10 121314 | 12h13m14s UT on 1998 Jan. 10 |
            +---------------------+------------------------------+
            | 1923-06-23          | 0h UT on 1923 June 23        |
            +---------------------+------------------------------+
            | 1930-Feb-18 19      | 19h UT on 1930 Feb. 18       |
            +---------------------+------------------------------+
            | 1997/03/31          | 0h UT on 1997 Mar. 31        |
            +---------------------+------------------------------+
            | 1945/11/05.5        | 12h UT on 1945 Nov. 5        |
            +---------------------+------------------------------+
            | 1986/Jan/28 05      | 5h UT on 1986 Jan. 28        |
            +---------------------+------------------------------+
            | 1956:05:16 1734     | 17h34m UT on 1956 May 16     |
            +---------------------+------------------------------+
            | 1965:May:16 1922    | 19h22m UT on 1965 May 16     |
            +---------------------+------------------------------+
            | JD 2451000.5        | 0h UT on 1998 July 6         |
            +---------------------+------------------------------+
            | MJD 51000           | 0h UT on 1998 July 6         |
            +---------------------+------------------------------+

        References
        ----------

        .. [1] Williams, G. The Minor Planet Ephemeris Service.
           https://minorplanetcenter.net/iau/info/MPES.pdf (retrieved
           2018 June 19).

           [2] IAU Minor Planet Center.  List of Observatory codes.
           https://minorplanetcenter.net/iau/lists/ObsCodesF.html
           (retrieved 2018 June 19).

        """

        from astropy.time import Time
        import astropy.units as u
        from astropy.coordinates import EarthLocation

        # HTTP POST data containing MPES parameters
        data = {
            'ty': 'e',
            'TextArea': str(target),
            'uto': int(utoffset),
            'igd': 'y' if suppress_daytime else 'n',
            'ibh': 'y' if suppress_set else 'n',
            'fp': 'y' if perturbed else 'n',
            'adir': 'N'  # always measure azimuth eastward from north
        }

        if isinstance(location, str):
            data['c'] = location
        elif isinstance(location, int):
            data['c'] = '{:03d}'.format(location)
        elif isinstance(location, EarthLocation):
            loc = location.geodetic
            data['long'] = loc.lon.deg
            data['lat'] = loc.lat.deg
            data['alt'] = loc.height.to(u.m).value
        elif np.isiterable(location):
            data['long'] = u.Quantity(loc[0], u.deg).value
            data['lat'] = u.Quantity(loc[1], u.deg).value
            data['alt'] = u.Quantity(loc[2], u.m).value

        if start is None:
            data['d'] = Time.now().iso[:10]
        elif isinstance(start, Time):
            data['d'] = start.iso.replace(':', '').replace('-', ':')[:15]
        else:
            data['d'] = start

        _step = u.Quantity(step)
        assert _step.unit in [
            u.d, u.h, u.min, u.s], 'step must have units of days, hours, minutues, or seconds.'
        data['i'] = int(round(step.value))
        data['u'] = str(step.unit)[:1]
        data['l'] = self._default_number_of_steps.get(interval_unit, number)

        data['raty'] = self._ephemeris_types[eph_type]
        data['s'] = self._proper_motions[proper_motion]
        data['m'] = 'h'  # proper motion always arcsec/hr


MPC = MPCClass()
