# 1. standard library imports

from collections import OrderedDict
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
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ...query import BaseQuery
from ...utils import async_to_sync

# import configurable items declared in __init__.py, e.g. hardcoded dictionaries
from . import conf


@async_to_sync
class RingNodeClass(BaseQuery):
    """
    for querying the Planetary Ring Node ephemeris tools
    <https://pds-rings.seti.org/tools/>

    """

    TIMEOUT = conf.timeout

    def __init__(self, planet=None, obs_time=None):
        """Instantiate Planetary Ring Node query

        Parameters
        ----------

        """

        super().__init__()

    def __str__(self):
        """
        String representation of RingNodeClass object instance

        Examples
        --------
        >>> from astroquery.solarsystem.pds import RingNode
        >>> nodeobj = RingNode()
        >>> print(nodeobj)  # doctest: +SKIP
        PDSRingNode instance
        """
        return "PDSRingNode instance"

    # --- pretty stuff above this line, get it working below this line ---

    def ephemeris_async(
        self,
        planet,
        obs_time=None,
        location=None,
        neptune_arcmodel=3,
        get_query_payload=False,
        get_raw_response=False,
        cache=True,
    ):
        """
        send query to server

        note this interacts with utils.async_to_sync to be called as ephemeris()

        Parameters
        ----------
        self : RingNodeClass instance
        planet : str, required. one of Mars, Jupiter, Saturn, Uranus, Neptune, or Pluto
        obs_time : astropy.Time object, or str in format YYYY-MM-DD hh:mm, optional.
                If str is provided then UTC is assumed. If no obs_time is provided,
                the current time is used.
        location : array-like, or `~astropy.coordinates.EarthLocation`, optional
            Observer's location as a
            3-element array of Earth longitude, latitude, altitude, or
            a `~astropy.coordinates.EarthLocation`.  Longitude and
            latitude should be anything that initializes an
            `~astropy.coordinates.Angle` object, and altitude should
            initialize an `~astropy.units.Quantity` object (with units
            of length).  If ``None``, then the geocenter (code 500) is
            used.
        neptune_arcmodel : float, optional. which ephemeris to assume for Neptune's ring arcs
            must be one of 1, 2, or 3 (see https://pds-rings.seti.org/tools/viewer3_nep.shtml for details)
            has no effect if planet != 'Neptune'

        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.

        Examples
        --------
        >>> from astroquery.solarsystem.pds import RingNode
        >>> nodeobj = RingNode()
        >>> eph = obj.ephemeris(planet='Uranus',
        ...                 obs_time='2017-01-01 00:00')  # doctest: +SKIP
        >>> print(eph)  # doctest: +SKIP
            table here...
        """
        planet = planet
        obs_time = obs_time

        URL = conf.pds_server
        # URL = 'https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?'

        # check inputs and set defaults for optional inputs
        if planet is None:
            raise ValueError("'planet' parameter not set. Query aborted.")
        else:
            planet = planet.lower()
            if planet not in [
                "mars",
                "jupiter",
                "saturn",
                "uranus",
                "neptune",
                "pluto",
            ]:
                raise ValueError(
                    "illegal value for 'planet' parameter (must be 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', or 'Pluto'"
                )

        if obs_time is None:
            obs_time = Time.now().strftime("%Y-%m-%d %H:%M")
            warnings.warn("obs_time not set. using current time instead.")
        elif type(obs_time) == str:
            try:
                Time.strptime(obs_time, "%Y-%m-%d %H:%M").jd
            except Exception as e:
                raise ValueError(
                    "illegal value for 'obs_time' parameter. string must have format 'yyyy-mm-dd hh:mm'"
                )
        elif type(obs_time) == Time:
            try:
                obs_time = obs_time.utc.to_value("iso", subfmt="date_hm")
            except Exception as e:
                raise ValueError(
                    "illegal value for 'obs_time' parameter. could not parse astropy.time.core.Time object into format 'yyyy-mm-dd hh:mm' (UTC)"
                )

        if location is None:
            viewpoint = "observatory"
            latitude, longitude, altitude = "", "", ""
            print("Observatory coordinates not set. Using center of Earth.")
        else:
            viewpoint = "latlon"
            if type(location) != EarthLocation:
                if hasattr(location, "__iter__"):
                    if len(location) != 3:
                        raise ValueError(
                            "location arrays require three values:"
                            " longitude, latitude, and altitude"
                        )
                else:
                    raise TypeError(
                        "location must be array-like or astropy EarthLocation"
                    )

            if isinstance(location, EarthLocation):
                loc = location.geodetic
                longitude = loc[0].deg
                latitude = loc[1].deg
                altitude = loc[2].to(u.m).value
            elif hasattr(location, "__iter__"):
                latitude = Angle(location[0]).deg
                longitude = Angle(location[1]).deg
                altitude = u.Quantity(location[2]).to("m").value

        if int(neptune_arcmodel) not in [1, 2, 3]:
            raise ValueError(
                f"Illegal Neptune arc model {neptune_arcmodel}. must be one of 1, 2, or 3 (see https://pds-rings.seti.org/tools/viewer3_nep.shtml for details)"
            )

        # configure request_payload for ephemeris query
        # start with successful query and incrementally de-hardcode stuff
        # thankfully, adding extra planet-specific keywords here does not break query for other planets
        request_payload = OrderedDict(
            [
                ("abbrev", planet.lower()[:3]),
                ("ephem", conf.planet_defaults[planet]["ephem"],),
                ("time", obs_time),  # UTC. this should be enforced when checking inputs
                (
                    "fov",
                    10,
                ),  # next few are figure options, can be hardcoded and ignored
                ("fov_unit", planet.capitalize() + " radii"),
                ("center", "body"),
                ("center_body", planet.capitalize()),
                ("center_ansa", conf.planet_defaults[planet]["center_ansa"]),
                ("center_ew", "east"),
                ("center_ra", ""),
                ("center_ra_type", "hours"),
                ("center_dec", ""),
                ("center_star", ""),
                ("viewpoint", viewpoint),
                (
                    "observatory",
                    "Earth's center",
                ),  # has no effect if viewpoint != observatory so can hardcode. no plans to implement calling observatories by name since ring node only names like 8 observatories
                ("latitude", latitude),
                ("longitude", longitude),
                ("lon_dir", "east"),
                ("altitude", altitude),
                ("moons", conf.planet_defaults[planet]["moons"]),
                ("rings", conf.planet_defaults[planet]["rings"]),
                ("arcmodel", conf.neptune_arcmodels[int(neptune_arcmodel)]),
                (
                    "extra_ra",
                    "",
                ),  # figure options below this line, can all be hardcoded and ignored
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

        # set return_raw flag, if raw response desired
        if get_raw_response:
            self.return_raw = True

        # query and parse
        response = self._request(
            "GET", URL, params=request_payload, timeout=self.TIMEOUT, cache=cache
        )
        self.uri = response.url

        return response

    def _parse_ringnode(self, src):
        """
        Routine for parsing data from ring node

        Parameters
        ----------
        self : RingNodeClass instance
        src : list
            raw response from server


        Returns
        -------
        data : `astropy.Table`
        """

        self.raw_response = src
        soup = BeautifulSoup(src, "html.parser")
        text = soup.get_text()
        # print(repr(text))
        textgroups = re.split("\n\n|\n \n", text)
        ringtable = None
        for group in textgroups:
            group = group.strip(", \n")

            # input parameters. only thing needed is obs_time
            if group.startswith("Observation"):
                obs_time = group.split("\n")[0].split("e: ")[-1].strip(", \n")

            # minor body table part 1
            elif group.startswith("Body"):
                group = "NAIF " + group  # fixing lack of header for NAIF ID
                bodytable = ascii.read(
                    group,
                    format="fixed_width",
                    col_starts=(0, 4, 18, 35, 54, 68, 80, 91),
                    col_ends=(4, 18, 35, 54, 68, 80, 91, 102),
                    names=(
                        "NAIF ID",
                        "Body",
                        "RA",
                        "Dec",
                        "RA (deg)",
                        "Dec (deg)",
                        "dRA",
                        "dDec",
                    ),
                )
                units_list = [None, None, None, None, u.deg, u.deg, u.arcsec, u.arcsec]
                bodytable = table.QTable(bodytable, units=units_list)
                # for i in range(len(bodytable.colnames)):
                #    bodytable[bodytable.colnames[i]].unit = units_list[i]
            # minor body table part 2
            elif group.startswith("Sub-"):
                group = "\n".join(group.split("\n")[1:])  # fixing two-row header
                group = "NAIF" + group[4:]
                bodytable2 = ascii.read(
                    group,
                    format="fixed_width",
                    col_starts=(0, 4, 18, 28, 37, 49, 57, 71),
                    col_ends=(4, 18, 28, 37, 49, 57, 71, 90),
                    names=(
                        "NAIF ID",
                        "Body",
                        "sub_obs_lon",
                        "sub_obs_lat",
                        "sub_sun_lon",
                        "sub_sun_lat",
                        "phase",
                        "distance",
                    ),
                )
                units_list = [None, None, u.deg, u.deg, u.deg, u.deg, u.deg, u.km * 1e6]
                bodytable2 = table.QTable(bodytable2, units=units_list)
                # for i in range(len(bodytable2.colnames)):
                #    bodytable2[bodytable2.colnames[i]].unit = units_list[i]

            # ring plane data
            elif group.startswith("Ring s"):
                lines = group.split("\n")
                for line in lines:
                    l = line.split(":")
                    if "Ring sub-solar latitude" in l[0]:
                        [sub_sun_lat, sub_sun_lat_min, sub_sun_lat_max] = [
                            float(s.strip(", \n()")) for s in re.split("\(|to", l[1])
                        ]
                        # systemtable = table.Table([[sub_sun_lat], [sub_sun_lat_max], [sub_sun_lat_min]],
                        #                         names = ('sub_sun_lat', 'sub_sun_lat_max', 'sub_sun_lat_min'))
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
                        # systemtable["d_sun_AU"] = float(l[1].strip(", \n"))
                        pass
                    elif "Observer-planet distance (AU)" in l[0]:
                        # systemtable["d_obs_AU"] = float(l[1].strip(", \n"))
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
                ringtable = ascii.read(
                    "     " + group,
                    format="fixed_width",
                    col_starts=(5, 18, 29),
                    col_ends=(18, 29, 36),
                    names=("ring", "pericenter", "ascending node"),
                )

                units_list = [None, u.deg, u.deg]
                ringtable = table.QTable(ringtable, units=units_list)

            # Saturn F-ring data
            elif group.startswith("F Ring"):
                lines = group.split("\n")
                for line in lines:
                    l = line.split(":")
                    if "F Ring pericenter" in l[0]:
                        peri = float(re.sub("[a-zA-Z]+", "", l[1]).strip(", \n()"))
                    elif "F Ring ascending node" in l[0]:
                        ascn = float(l[1].strip(", \n"))
                ringtable = table.Table(
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
                        ringtable = table.Table(
                            [[ring], [min_angle], [max_angle]],
                            names=("ring", "min_angle", "max_angle"),
                            units=(None, u.deg, u.deg),
                        )
                    else:
                        ringtable.add_row([ring, min_angle, max_angle])

            else:
                pass

        # do some cleanup from the parsing job
        ringtable.add_index("ring")

        bodytable = table.join(bodytable, bodytable2)  # concatenate minor body table
        bodytable.add_index("Body")

        systemtable["obs_time"] = Time(
            obs_time, format="iso", scale="utc"
        )  # add obs time to systemtable

        return systemtable, bodytable, ringtable

    def _parse_result(self, response, verbose=None):
        """
        Routine for managing parser calls
        note this MUST be named exactly _parse_result so it interacts with async_to_sync properly

        Parameters
        ----------
        self :  RingNodeClass instance
        response : string
            raw response from server

        Returns
        -------
        data : `astropy.Table`
        """
        self.last_response = response
        try:
            systemtable, bodytable, ringtable = self._parse_ringnode(response.text)
        except Exception as e:
            try:
                self._last_query.remove_cache_file(self.cache_location)
            except OSError:
                # this is allowed: if `cache` was set to False, this
                # won't be needed
                pass
            raise
        return (
            systemtable,
            bodytable,
            ringtable,
        )  # astropy table, astropy table, astropy table


RingNode = RingNodeClass()
