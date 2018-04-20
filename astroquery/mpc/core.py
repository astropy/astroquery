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


MPC = MPCClass()
