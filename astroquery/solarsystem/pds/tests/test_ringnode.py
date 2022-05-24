import pytest
import os
import numpy as np

from astropy.tests.helper import assert_quantity_allclose
import astropy.units as u

from astroquery.utils.mocks import MockResponse
from ... import pds

# files in data/ for different planets
DATA_FILES = {'Uranus': 'uranus_ephemeris.html',
              'Pluto': 'pluto_ephemeris.html',
              'Neptune': 'neptune_ephemeris.html',
              'Saturn': 'saturn_ephemeris.html',
              }


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, request_type, url, **kwargs):

    planet_name = kwargs['params']['center_body']
    with open(data_path(DATA_FILES[planet_name.capitalize()]), "rb") as f:
        response = MockResponse(content=f.read(), url=url)

    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(pds.core.RingNodeClass, "_request", nonremote_request)
    return mp


# --------------------------------- actual test functions

def test_ephemeris_query_Uranus(patch_request):

    systemtable, bodytable, ringtable = pds.RingNode.ephemeris(
        planet="Uranus",
        epoch="2022-05-03 00:00",
        location=(10.0 * u.deg, -120.355 * u.deg, 1000 * u.m),
    )
    # check system table
    assert_quantity_allclose(
        [
            -56.12233,
            -56.13586,
            -56.13586,
            -56.01577,
            0.10924,
            354.11072,
            354.12204,
            2947896667.0,
            3098568884.0,
            10335.713263,
        ],
        [
            systemtable["sub_sun_lat"].to(u.deg).value,
            systemtable["sub_sun_lat_min"].to(u.deg).value,
            systemtable["sub_sun_lat_max"].to(u.deg).value,
            systemtable["opening_angle"].to(u.deg).value,
            systemtable["phase_angle"].to(u.deg).value,
            systemtable["sub_sun_lon"].to(u.deg).value,
            systemtable["sub_obs_lon"].to(u.deg).value,
            systemtable["d_sun"].to(u.km).value,
            systemtable["d_obs"].to(u.km).value,
            systemtable["light_time"].to(u.second).value,
        ],
        rtol=1e-2,
    )

    # check a moon in body table
    mab = bodytable[bodytable.loc_indices["Mab"]]
    assert mab["NAIF ID"] == 726
    assert mab["Body"] == "Mab"
    assert_quantity_allclose(
        [
            42.011201,
            15.801323,
            5.368,
            0.623,
            223.976,
            55.906,
            223.969,
            56.013,
            0.10932,
            3098.514,
        ],
        [
            mab["RA (deg)"].to(u.deg).value,
            mab["Dec (deg)"].to(u.deg).value,
            mab["dRA"].to(u.arcsec).value,
            mab["dDec"].to(u.arcsec).value,
            mab["sub_obs_lon"].to(u.deg).value,
            mab["sub_obs_lat"].to(u.deg).value,
            mab["sub_sun_lon"].to(u.deg).value,
            mab["sub_sun_lat"].to(u.deg).value,
            mab["phase"].to(u.deg).value,
            mab["distance"].to(u.km * 1e6).value,
        ],
        rtol=1e-2,
    )

    # check a ring in ringtable
    beta = ringtable[ringtable.loc_indices["Beta"]]
    assert np.isclose(beta["pericenter"].to(u.deg).value, 231.051, rtol=1e-3)
    assert np.isclose(beta["ascending node"].to(u.deg).value, 353.6, rtol=1e-2)


def test_ephemeris_query_Pluto(patch_request):

    systemtable, bodytable, ringtable = pds.RingNode.ephemeris(
        planet="Pluto",
        epoch="2021-10-07 07:25",
    )
    print(systemtable)
    print(bodytable[bodytable.loc_indices["Styx"]])
    # check system table
    assert_quantity_allclose(
        [
            57.57737,
             57.56961,
            57.56961,
            56.50534,
            1.64048,
            116.55873,
            118.8369,
            5142696000,
            5114486810,
            17060.091666,
        ],
        [
            systemtable["sub_sun_lat"].to(u.deg).value,
            systemtable["sub_sun_lat_min"].to(u.deg).value,
            systemtable["sub_sun_lat_max"].to(u.deg).value,
            systemtable["opening_angle"].to(u.deg).value,
            systemtable["phase_angle"].to(u.deg).value,
            systemtable["sub_sun_lon"].to(u.deg).value,
            systemtable["sub_obs_lon"].to(u.deg).value,
            systemtable["d_sun"].to(u.km).value,
            systemtable["d_obs"].to(u.km).value,
            systemtable["light_time"].to(u.second).value,
        ],
        rtol=1e-2,
    )

    # check a moon in body table
    styx = bodytable[bodytable.loc_indices["Styx"]]
    assert styx["NAIF ID"] == 905
    assert styx["Body"] == "Styx"
    assert_quantity_allclose(
        [
            296.212477,
            -22.93533,
            -0.557,
            -1.259,
            350.443,
            56.472,
            352.72,
            57.544,
            1.64047,
            5114.509238,
        ],
        [
            styx["RA (deg)"].to(u.deg).value,
            styx["Dec (deg)"].to(u.deg).value,
            styx["dRA"].to(u.arcsec).value,
            styx["dDec"].to(u.arcsec).value,
            styx["sub_obs_lon"].to(u.deg).value,
            styx["sub_obs_lat"].to(u.deg).value,
            styx["sub_sun_lon"].to(u.deg).value,
            styx["sub_sun_lat"].to(u.deg).value,
            styx["phase"].to(u.deg).value,
            styx["distance"].to(u.km * 1e6).value,
        ],
        rtol=1e-2,
    )

    # check ringtable is None
    assert ringtable is None


def test_ephemeris_query_Neptune(patch_request):
    '''Verify that the Neptune ring arcs are queried properly'''

    systemtable, bodytable, ringtable = pds.RingNode.ephemeris(
        planet="Neptune",
        epoch="2021-10-07 07:25",
        neptune_arcmodel=2
    )

    print(ringtable[ringtable.loc_indices["Courage"]])

    assert_quantity_allclose(
                    [63.81977,
                     55.01978,
                     44.21976,
                     40.41978,
                     26.41978,
                     64.81977,
                     59.11976,
                     45.21976,
                     43.41978,
                     36.01978],
                     [ringtable[ringtable.loc_indices["Courage"]]["min_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Liberte"]]["min_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Egalite A"]]["min_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Egalite B"]]["min_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Fraternite"]]["min_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Courage"]]["max_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Liberte"]]["max_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Egalite A"]]["max_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Egalite B"]]["max_angle"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["Fraternite"]]["max_angle"].to(u.deg).value,
                      ], rtol=1e-3)


def test_ephemeris_query_Saturn(patch_request):
    '''Check Saturn F ring is queried properly'''
    systemtable, bodytable, ringtable = pds.RingNode.ephemeris(
        planet="Saturn",
        epoch="2021-10-07 07:25",
    )
    print(ringtable)

    assert_quantity_allclose(
                    [249.23097,
                     250.34081
                     ],
                     [
                     ringtable[ringtable.loc_indices["F"]]["pericenter"].to(u.deg).value,
                     ringtable[ringtable.loc_indices["F"]]["ascending node"].to(u.deg).value
                     ], rtol=1e-3)


def test_ephemeris_query_payload():
    res = pds.RingNode.ephemeris(
        planet="Neptune",
        epoch="2022-05-03 00:00",
        neptune_arcmodel=1,
        location=(10.0 * u.deg, -120.355 * u.deg, 1000 * u.m),
        get_query_payload=True,
    )

    assert res == dict(
        [
            ("abbrev", "nep"),
            ("ephem", "000 NEP081 + NEP095 + DE440"),
            (
                "time",
                "2022-05-03 00:00",
            ),  # UTC. this should be enforced when checking inputs
            ("fov", 10),  # next few are figure options, can be hardcoded and ignored
            ("fov_unit", "Neptune radii"),
            ("center", "body"),
            ("center_body", "Neptune"),
            ("center_ansa", "Adams Ring"),
            ("center_ew", "east"),
            ("center_ra", ""),
            ("center_ra_type", "hours"),
            ("center_dec", ""),
            ("center_star", ""),
            ("viewpoint", "latlon"),
            (
                "observatory",
                "Earth's center",
            ),
            ("latitude", 10),
            ("longitude", -120.355),
            ("lon_dir", "east"),
            ("altitude", 1000),
            ("moons", "814 All inner moons (N1-N8,N14)"),
            ("rings", "Galle, LeVerrier, Arago, Adams"),
            ("arcmodel", "#1 (820.1194 deg/day)"),
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
