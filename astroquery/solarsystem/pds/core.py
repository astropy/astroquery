# 1. standard library imports

import re
import warnings

# 2. third party imports
from astropy.time import Time
from astropy import table
from astropy.io import ascii
import astropy.units as u
from astropy.coordinates import EarthLocation, Angle
from bs4 import BeautifulSoup

# 3. local imports - use relative imports
# all Query classes should inherit from BaseQuery.
from ...query import BaseQuery
from ...utils import async_to_sync

# import configurable items declared in __init__.py, e.g. hardcoded dictionaries
from . import conf

planet_defaults = {
    "mars": {
        "ephem": "000 MAR097 + DE440",
        "moons": "402 Phobos, Deimos",
        "center_ansa": "Phobos Ring",
        "rings": "Phobos, Deimos",
    },
    "jupiter": {
        "ephem": "000 JUP365 + DE440",
        "moons": "516 All inner moons (J1-J5,J14-J16)",
        "center_ansa": "Main Ring",
        "rings": "Main & Gossamer",
    },
    "saturn": {
        "ephem": "000 SAT389 + SAT393 + SAT427 + DE440",
        "moons": "653 All inner moons (S1-S18,S32-S35,S49,S53)",
        "center_ansa": "A",
        "rings": "A,B,C,F,G,E",
    },
    "uranus": {
        "ephem": "000 URA111 + URA115 + DE440",
        "moons": "727 All inner moons (U1-U15,U25-U27)",
        "center_ansa": "Epsilon",
        "rings": "All rings",
    },
    "neptune": {
        "ephem": "000 NEP081 + NEP095 + DE440",
        "moons": "814 All inner moons (N1-N8,N14)",
        "center_ansa": "Adams Ring",
        "rings": "Galle, LeVerrier, Arago, Adams",
    },
    "pluto": {
        "ephem": "000 PLU058 + DE440",
        "moons": "905 All moons (P1-P5)",
        "center_ansa": "Hydra",
        "rings": "Styx, Nix, Kerberos, Hydra",
    },
}

neptune_arcmodels = {
    1: "#1 (820.1194 deg/day)",
    2: "#2 (820.1118 deg/day)",
    3: "#3 (820.1121 deg/day)",
}


@async_to_sync
class RingNodeClass(BaseQuery):
    """
    a class for querying the Planetary Ring Node ephemeris tools
    <https://pds-rings.seti.org/tools/>
    """

    def __init__(self, url='', timeout=None):
        '''
        Instantiate Planetary Ring Node query
        '''
        super().__init__()
        self.url = url
        self.timeout = timeout

    @property
    def _url(self):
        return self.url or conf.url

    @property
    def _timeout(self):
        return conf.timeout if self.timeout is None else self.timeout

    def __str__(self):

        return "PDSRingNode instance"

    def ephemeris_async(self, planet, *, epoch=None, location=None, neptune_arcmodel=3,
                            get_query_payload=False, get_raw_response=False, cache=True):
        """
        send query to Planetary Ring Node server

        Parameters
        ----------
        planet : str, required. one of Mars, Jupiter, Saturn, Uranus, Neptune, or Pluto
        epoch : `~astropy.time.Time` object, or str in format YYYY-MM-DD hh:mm, optional.
                If str is provided then UTC is assumed.
                If no epoch is provided, the current time is used.
        location : array-like, or `~astropy.coordinates.EarthLocation`, optional
            Observer's location as a
            3-element array of Earth longitude, latitude, altitude, or
            `~astropy.coordinates.EarthLocation`.  Longitude and
            latitude should be anything that initializes an
            `~astropy.coordinates.Angle` object, and altitude should
            initialize an `~astropy.units.Quantity` object (with units
            of length).  If ``None``, then the geocenter is used.
        neptune_arcmodel : float, optional. which ephemeris to assume for Neptune's ring arcs
            must be one of 1, 2, or 3 (see https://pds-rings.seti.org/tools/viewer3_nep.shtml for details)
            has no effect if planet != 'Neptune'
        get_query_payload : boolean, optional
            When set to `True` the method returns the HTTP request parameters as
            a dict, default: False


        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.


        Examples
        --------
        >>> from astroquery.solarsystem.pds import RingNode
        >>> import astropy.units as u
        >>> bodytable, ringtable = RingNode.ephemeris(planet='Uranus',
        ...                 epoch='2024-05-08 22:39',
        ...                 location = (-23.029 * u.deg, -67.755 * u.deg, 5000 * u.m))  # doctest: +REMOTE_DATA
        >>> print(ringtable)  # doctest: +REMOTE_DATA
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
        """

        planet = planet.lower()
        if planet not in ["mars", "jupiter", "saturn", "uranus", "neptune", "pluto", ]:
            raise ValueError(
                "illegal value for 'planet' parameter (must be 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', or 'Pluto')"
            )

        if isinstance(epoch, (int, float)):
            epoch = Time(epoch, format='jd')
        elif isinstance(epoch, str):
            epoch = Time(epoch, format='iso')
        elif epoch is None:
            epoch = Time.now()

        if location is None:
            viewpoint = "observatory"
            latitude, longitude, altitude = "", "", ""
        else:
            viewpoint = "latlon"
            if isinstance(location, EarthLocation):
                loc = location.geodetic
                longitude = loc[0].deg
                latitude = loc[1].deg
                altitude = loc[2].to(u.m).value
            elif hasattr(location, "__iter__"):
                longitude = Angle(location[0]).deg
                latitude = Angle(location[1]).deg
                altitude = u.Quantity(location[2]).to("m").value

        if int(neptune_arcmodel) not in [1, 2, 3]:
            raise ValueError(
                f"Illegal Neptune arc model {neptune_arcmodel}. must be one of 1, 2, or 3 (see https://pds-rings.seti.org/tools/viewer3_nep.shtml for details)"
            )

        # configure request_payload for ephemeris query
        # thankfully, adding extra planet-specific keywords here does not break query for other planets
        request_payload = dict(
            [
                ("abbrev", planet[:3]),
                ("ephem", planet_defaults[planet]["ephem"]),
                ("time", epoch.utc.iso[:16]),
                ("fov", 10),  # next few are figure options, can be hardcoded and ignored
                ("fov_unit", planet.capitalize() + " radii"),
                ("center", "body"),
                ("center_body", planet.capitalize()),
                ("center_ansa", planet_defaults[planet]["center_ansa"]),
                ("center_ew", "east"),
                ("center_ra", ""),
                ("center_ra_type", "hours"),
                ("center_dec", ""),
                ("center_star", ""),
                ("viewpoint", viewpoint),
                ("observatory", "Earth's center"),  # has no effect if viewpoint != observatory so can hardcode. no plans to implement calling observatories by name since ring node only names like 8 observatories
                ("latitude", latitude),
                ("longitude", longitude),
                ("lon_dir", "east"),
                ("altitude", altitude),
                ("moons", planet_defaults[planet]["moons"]),
                ("rings", planet_defaults[planet]["rings"]),
                ("arcmodel", neptune_arcmodels[int(neptune_arcmodel)]),
                ("extra_ra", ""),  # figure options below this line, can all be hardcoded and ignored
                ("extra_ra_type", "hours"),
                ("extra_dec", ""),
                ("extra_name", ""),
                ("title", ""),
                ("labels", "Small (6 points)"),
                ("moonpts", "0"),
                ("blank", "No"),
                ("opacity", "Transparent"),
                ("peris", "None"),
                ("peripts", "4"),
                ("arcpts", "4"),
                ("meridians", "Yes"),
                ("output", "html"),
            ]
        )

        # return request_payload if desired
        if get_query_payload:
            return request_payload

        # query and parse
        response = self._request(
            "GET", self._url, params=request_payload, timeout=self._timeout, cache=cache
        )

        return response

    def _parse_result(self, response, verbose=None):
        """
        Routine for parsing data from ring node

        Parameters
        ----------
        self : RingNodeClass instance
        response : list
            raw response from server


        Returns
        -------
        bodytable : `astropy.QTable`
        ringtable : `astropy.QTable`
        """
        self.last_response = response
        try:
            self._last_query.remove_cache_file(self.cache_location)
        except FileNotFoundError:
            # this is allowed: if `cache` was set to False, this
            # won't be needed
            pass

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        textgroups = re.split("\n\n|\n \n", text)
        ringtable = None
        for group in textgroups:
            group = group.strip(", \n")

            # input parameters. only thing needed is epoch
            if group.startswith("Observation"):
                epoch = group.split("\n")[0].split("e: ")[-1].strip(", \n")

            # minor body table part 1
            elif group.startswith("Body"):
                group = "NAIF " + group  # fixing lack of header for NAIF ID
                bodytable = table.QTable.read(group, format="ascii.fixed_width",
                                        col_starts=(0, 4, 18, 35, 54, 68, 80, 91),
                                        col_ends=(4, 18, 35, 54, 68, 80, 91, 102),
                                        names=("NAIF ID", "Body", "RA", "Dec", "RA (deg)", "Dec (deg)", "dRA", "dDec"),
                                        units=([None, None, None, None, u.deg, u.deg, u.arcsec, u.arcsec]))

            # minor body table part 2
            elif group.startswith("Sub-"):
                group = "\n".join(group.split("\n")[1:])  # fixing two-row header
                group = "NAIF" + group[4:]
                bodytable2 = table.QTable.read(group, format="ascii.fixed_width",
                                        col_starts=(0, 4, 18, 28, 37, 49, 57, 71),
                                        col_ends=(4, 18, 28, 37, 49, 57, 71, 90),
                                        names=("NAIF ID", "Body", "sub_obs_lon", "sub_obs_lat", "sub_sun_lon", "sub_sun_lat", "phase", "distance"),
                                        units=([None, None, u.deg, u.deg, u.deg, u.deg, u.deg, u.km * 1e6]))

            # ring plane data
            elif group.startswith("Ring s"):
                lines = group.split("\n")
                for line in lines:
                    l = line.split(":")
                    if "Ring sub-solar latitude" in l[0]:
                        [sub_sun_lat, sub_sun_lat_min, sub_sun_lat_max] = [
                            float(s.strip(", \n()")) for s in re.split("\(|to", l[1])
                        ]
                        systemtable = {
                            "sub_sun_lat": sub_sun_lat * u.deg,
                            "sub_sun_lat_min": sub_sun_lat_min * u.deg,
                            "sub_sun_lat_max": sub_sun_lat_min * u.deg,
                        }

                    elif "Ring plane opening angle" in l[0]:
                        systemtable["opening_angle"] = (
                            float(re.sub("[a-zA-Z]+", "", l[1]).strip(", \n()")) * u.deg
                        )
                    elif "Ring center phase angle" in l[0]:
                        systemtable["phase_angle"] = float(l[1].strip(", \n")) * u.deg
                    elif "Sub-solar longitude" in l[0]:
                        systemtable["sub_sun_lon"] = (
                            float(re.sub("[a-zA-Z]+", "", l[1]).strip(", \n()")) * u.deg
                        )
                    elif "Sub-observer longitude" in l[0]:
                        systemtable["sub_obs_lon"] = float(l[1].strip(", \n")) * u.deg
                    else:
                        pass

            # basic info about the planet
            elif group.startswith("Sun-planet"):
                lines = group.split("\n")
                for line in lines:
                    l = line.split(":")
                    if "Sun-planet distance (AU)" in l[0]:
                        # this is redundant with sun distance in km
                        pass
                    elif "Observer-planet distance (AU)" in l[0]:
                        # this is redundant with observer distance in km
                        pass
                    elif "Sun-planet distance (km)" in l[0]:
                        systemtable["d_sun"] = (
                            float(l[1].split("x")[0].strip(", \n")) * 1e6 * u.km
                        )
                    elif "Observer-planet distance (km)" in l[0]:
                        systemtable["d_obs"] = (
                            float(l[1].split("x")[0].strip(", \n")) * 1e6 * u.km
                        )
                    elif "Light travel time" in l[0]:
                        systemtable["light_time"] = float(l[1].strip(", \n")) * u.second
                    else:
                        pass

            # --------- below this line, planet-specific info ------------
            # Uranus individual rings data
            elif group.startswith("Ring    "):
                ringtable = table.QTable.read("     " + group, format="ascii.fixed_width",
                    col_starts=(5, 18, 29),
                    col_ends=(18, 29, 36),
                    names=("ring", "pericenter", "ascending node"),
                    units=([None, u.deg, u.deg]))

            # Saturn F-ring data
            elif group.startswith("F Ring"):
                lines = group.split("\n")
                for line in lines:
                    l = line.split(":")
                    if "F Ring pericenter" in l[0]:
                        peri = float(re.sub("[a-zA-Z]+", "", l[1]).strip(", \n()"))
                    elif "F Ring ascending node" in l[0]:
                        ascn = float(l[1].strip(", \n"))
                ringtable = table.QTable(
                    [["F"], [peri], [ascn]],
                    names=("ring", "pericenter", "ascending node"),
                    units=(None, u.deg, u.deg),
                )

            # Neptune ring arcs data
            elif group.startswith("Courage"):
                lines = group.split("\n")
                for i in range(len(lines)):
                    l = lines[i].split(":")
                    ring = l[0].split("longitude")[0].strip(", \n")
                    [min_angle, max_angle] = [
                        float(s.strip(", \n"))
                        for s in re.sub("[a-zA-Z]+", "", l[1]).strip(", \n()").split()
                    ]
                    if i == 0:
                        ringtable = table.QTable(
                            [[ring], [min_angle], [max_angle]],
                            names=("ring", "min_angle", "max_angle"),
                            units=(None, u.deg, u.deg),
                        )
                    else:
                        ringtable.add_row([ring, min_angle*u.deg, max_angle*u.deg])

            else:
                pass

        # do some cleanup from the parsing job
        # and make system-wide parameters metadata of bodytable and ringtable
        systemtable["epoch"] = Time(epoch, format="iso", scale="utc")  # add obs time to systemtable
        if ringtable is not None:
            ringtable.add_index("ring")
            ringtable.meta = systemtable

        bodytable = table.join(bodytable, bodytable2)  # concatenate minor body table
        bodytable.add_index("Body")
        bodytable.meta = systemtable

        return bodytable, ringtable


RingNode = RingNodeClass()
