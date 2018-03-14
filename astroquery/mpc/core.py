# -*- coding: utf-8 -*-

from ..query import BaseQuery
from . import conf
from ..utils import async_to_sync

__all__ = ['MPCClass']


@async_to_sync
class MPCClass(BaseQuery):
    MPC_URL = 'http://' + conf.server + '/web_service/search_orbits'
    # The authentication credentials for the MPC web service are publicly available and
    # can be openly viewed on the documentation page at https://minorplanetcenter.net/web_service/
    MPC_USERNAME = 'mpc_ws'
    MPC_PASSWORD = 'mpc!!ws'

    def __init__(self):
        super(MPCClass, self).__init__()

    def query_object_async(self, *args, **kwargs):
        """
        Query around a specific object within a given mission catalog

        The following are valid query parameters for the MPC API search. The params list and
        description are from https://minorplanetcenter.net/web_service/ and are accurate
        as of 3/6/2018:

        Parameters
        ----------
        **kwargs :
            updated_at :
                Date-time when the Orbits table was last updated (YYYY-MM-DDThh:mm:ssZ). Note:
                the documentation lists this field as "orbit-updated-at", but the service
                response contained "updated_at", which appears to correlate and can also be
                used as a query parameter.
            name :
                The asteroid's name; e.g., Eros. This can be queried as 'Eros' or 'eros'. If
                the asteroid has not yet been named, this field will be 'null'.
            number :
                The asteroid's number; e.g., 433. If the asteroid has not yet been numbered,
                this field will be 'null'.
            designation :
                The asteroid's provisional designation (e.g., 2014 AA) if it has not been
                numbered yet. If the asteroid has been numbered, this number is its permanent
                designation and is what the 'designation' parameter will return, padded with
                leading zeroes for a total of 7 digits; e.g., '0000433'. When querying for
                provisional designations, because white spaces aren't allowed in the query,
                escape the space with either a '+' or '%20'; e.g., '2014+AA' or '2014%20AA'.
            epoch :
                The date/time of reference for the current orbital parameters.
            epoch_jd :
                The Julian Date of the epoch.
            period (years) :
                Time it takes for the asteroid to complete one orbit around the Sun.
            semimajor_axis :
                a, one half of the longest diameter of the orbital ellipse. (AU)
            aphelion_distance :
                The distance when the asteroid is furthest from the Sun in its orbit. (AU)
            perihelion_distance :
                The distance when the asteroid is nearest to the Sun in its orbit. (AU)
            perihelion_date :
                Date when the asteroid is at perihelion, i.e., reaches its closest point to
                the Sun.
            perihelion_date_jd :
                The Julian Date of perihelion.
            argument_of_perihelion (°) :
                ω, defines the orientation of the ellipse in the orbital plane and is the
                angle from the asteroid's ascending node to its perihelion, measured in the
                direction of motion. Range: 0–360°.
            ascending_node (°) :
                Ω, the longitude of the ascending node, it defines the horizontal orientation
                of the ellipse with respect to the ecliptic, and is the angle measured
                counterclockwise (as seen from North of the ecliptic) from the First Point of
                Aries to the ascending node. Range: 0–360°.
            inclination (°) :
                i, the angle between the asteroid's orbit and the ecliptic. Range: 0–180°.
            eccentricity :
                e, a measure of how far the orbit shape departs from a circle. Range: 0–1,
                with e = 0 being a perfect circle, intermediate values being ellipses ever
                more elongated as e increases, and e = 1 describing a parabola.
            mean_anomaly (°) :
                M, is related to the position of the asteroid along its orbit at the given
                epoch. Range: 0–360°.
            mean_daily_motion (°/day) :
                n, a measure of the average speed of the asteroid along its orbit.
            absolute_magnitude :
                H, apparent magnitude the asteroid would have if it were observed from 1 AU
                away at zero phase, while it was 1 AU away from the Sun. Note this is
                geometrically impossible and is equivalent to observing the asteroid from the
                center of the Sun.
            phase_slope :
                G, slope parameter as calculated or assumed by the MPC. The slope parameter
                is a measure of how much brighter the asteroid gets as its phase angle
                decreases. When not known, a value of G = 0.15 is assumed.
            orbit_type :
                Asteroids are classified from a dynamics perspective by the area of the Solar
                System in which they orbit. A number identifies each orbit type:
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
            delta_v (km/sec) :
                Δv, an estimate of the amount of energy necessary to jump from LEO (Low Earth
                Orbit) to the asteroid's orbit.
            tisserand_jupiter :
                TJ, Tisserand parameter with respect to Jupiter, which is a quasi-invariant
                value for each asteroid and is frequently used to distinguish asteroids
                (typically TJ > 3) from Jupiter-family comets (typically 2 < TJ < 3).
            neo :
                value = 1 flags Near Earth Objects (NEOs).
            km_neo :
                value = 1 flags NEOs larger than ~1 km in diameter.
            pha :
                value = 1 flags Potentially Hazardous Asteroids (PHAs).
            mercury_moid :
                Minimum Orbit Intersection Distance with respect to Mercury. (AU)
            venus_moid :
                Minimum Orbit Intersection Distance with respect to Venus. (AU)
            earth_moid :
                Minimum Orbit Intersection Distance with respect to Earth. (AU)
            mars_moid :
                Minimum Orbit Intersection Distance with respect to Mars. (AU)
            jupiter_moid :
                Minimum Orbit Intersection Distance with respect to Jupiter. (AU)
            saturn_moid :
                Minimum Orbit Intersection Distance with respect to Saturn. (AU)
            uranus_moid :
                Minimum Orbit Intersection Distance with respect to Uranus. (AU)
            neptune_moid :
                Minimum Orbit Intersection Distance with respect to Neptune. (AU)

        """

        get_query_payload = kwargs.get('get_query_payload', False)
        kwargs.pop('get_query_payload', None)
        kwargs['limit'] = 1
        request_args = self._args_to_payload(**kwargs)

        # Return payload if requested
        if get_query_payload:
            return request_args

        auth = (self.MPC_USERNAME, self.MPC_PASSWORD)
        return self._request('GET', self.MPC_URL, params=request_args, auth=auth)

    def query_objects_async(self, *args, **kwargs):
        """
        Query around a specific object within a given mission catalog

        The following are valid query parameters for the MPC API search. The params list and
        description are from https://minorplanetcenter.net/web_service/ and are accurate
        as of 3/6/2018:

        Parameters
        ----------
        **kwargs :
            updated_at :
                Date-time when the Orbits table was last updated (YYYY-MM-DDThh:mm:ssZ). Note:
                the documentation lists this field as "orbit-updated-at", but the service
                response contained "updated_at", which appears to correlate and can also be
                used as a query parameter.
            name :
                The asteroid's name; e.g., Eros. This can be queried as 'Eros' or 'eros'. If
                the asteroid has not yet been named, this field will be 'null'.
            number :
                The asteroid's number; e.g., 433. If the asteroid has not yet been numbered,
                this field will be 'null'.
            designation :
                The asteroid's provisional designation (e.g., 2014 AA) if it has not been
                numbered yet. If the asteroid has been numbered, this number is its permanent
                designation and is what the 'designation' parameter will return, padded with
                leading zeroes for a total of 7 digits; e.g., '0000433'. When querying for
                provisional designations, because white spaces aren't allowed in the query,
                escape the space with either a '+' or '%20'; e.g., '2014+AA' or '2014%20AA'.
            epoch :
                The date/time of reference for the current orbital parameters.
            epoch_jd :
                The Julian Date of the epoch.
            period (years) :
                Time it takes for the asteroid to complete one orbit around the Sun.
            semimajor_axis :
                a, one half of the longest diameter of the orbital ellipse. (AU)
            aphelion_distance :
                The distance when the asteroid is furthest from the Sun in its orbit. (AU)
            perihelion_distance :
                The distance when the asteroid is nearest to the Sun in its orbit. (AU)
            perihelion_date :
                Date when the asteroid is at perihelion, i.e., reaches its closest point to
                the Sun.
            perihelion_date_jd :
                The Julian Date of perihelion.
            argument_of_perihelion (°) :
                ω, defines the orientation of the ellipse in the orbital plane and is the
                angle from the asteroid's ascending node to its perihelion, measured in the
                direction of motion. Range: 0–360°.
            ascending_node (°) :99008912
                Ω, the longitude of the ascending node, it defines the horizontal orientation
                of the ellipse with respect to the ecliptic, and is the angle measured
                counterclockwise (as seen from North of the ecliptic) from the First Point of
                Aries to the ascending node. Range: 0–360°.
            inclination (°) :
                i, the angle between the asteroid's orbit and the ecliptic. Range: 0–180°.
            eccentricity :
                e, a measure of how far the orbit shape departs from a circle. Range: 0–1,
                with e = 0 being a perfect circle, intermediate values being ellipses ever
                more elongated as e increases, and e = 1 describing a parabola.
            mean_anomaly (°) :
                M, is related to the position of the asteroid along its orbit at the given
                epoch. Range: 0–360°.
            mean_daily_motion (°/day) :
                n, a measure of the average speed of the asteroid along its orbit.
            absolute_magnitude :
                H, apparent magnitude the asteroid would have if it were observed from 1 AU
                away at zero phase, while it was 1 AU away from the Sun. Note this is
                geometrically impossible and is equivalent to observing the asteroid from the
                center of the Sun.
            phase_slope :
                G, slope parameter as calculated or assumed by the MPC. The slope parameter
                is a measure of how much brighter the asteroid gets as its phase angle
                decreases. When not known, a value of G = 0.15 is assumed.
            orbit_type :
                Asteroids are classified from a dynamics perspective by the area of the Solar
                System in which they orbit. A number identifies each orbit type:
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
            delta_v (km/sec) :
                Δv, an estimate of the amount of energy necessary to jump from LEO (Low Earth
                Orbit) to the asteroid's orbit.
            tisserand_jupiter :
                TJ, Tisserand parameter with respect to Jupiter, which is a quasi-invariant
                value for each asteroid and is frequently used to distinguish asteroids
                (typically TJ > 3) from Jupiter-family comets (typically 2 < TJ < 3).
            neo :
                value = 1 flags Near Earth Objects (NEOs).
            km_neo :
                value = 1 flags NEOs larger than ~1 km in diameter.
            pha :
                value = 1 flags Potentially Hazardous Asteroids (PHAs).
            mercury_moid :
                Minimum Orbit Intersection Distance with respect to Mercury. (AU)
            venus_moid :
                Minimum Orbit Intersection Distance with respect to Venus. (AU)
            earth_moid :
                Minimum Orbit Intersection Distance with respect to Earth. (AU)
            mars_moid :
                Minimum Orbit Intersection Distance with respect to Mars. (AU)
            jupiter_moid :
                Minimum Orbit Intersection Distance with respect to Jupiter. (AU)
            saturn_moid :
                Minimum Orbit Intersection Distance with respect to Saturn. (AU)
            uranus_moid :
                Minimum Orbit Intersection Distance with respect to Uranus. (AU)
            neptune_moid :
                Minimum Orbit Intersection Distance with respect to Neptune. (AU)
            limit :
                Limit the number of results to the given value
        """

        get_query_payload = kwargs.get('get_query_payload', False)
        kwargs.pop('get_query_payload', None)
        request_args = self._args_to_payload(**kwargs)

        # Return payload if requested
        if get_query_payload:
            return request_args

        auth = (self.MPC_USERNAME, self.MPC_PASSWORD)
        return self._request('GET', self.MPC_URL, params=request_args, auth=auth)

    def _args_to_payload(self, **kwargs):
        request_args = kwargs
        kwargs['json'] = 1
        return_fields = kwargs.pop('return_fields', None)
        if return_fields:
            kwargs['return'] = return_fields
        return request_args


MPC = MPCClass()
