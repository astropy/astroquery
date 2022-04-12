import pytest
from collections import OrderedDict
from astropy.tests.helper import assert_quantity_allclose

from ... import pds


# Horizons has machinery here to mock request from a text file
# is that necessary? why is that done?
# wouldn't we want to know if the website we are querying changes something that makes code fail?


# --------------------------------- actual test functions


@pytest.mark.remote_data
class TestRingNodeClass:
    def test_ephemeris_query():

        systemtable, bodytable, ringtable = pds.RingNode(
            planet="Uranus", obs_time="2022-05-03 00:00"
        ).ephemeris(observer_coords=(10.0, -120.355, 1000))

        # check system table
        systemclose = assert_quantity_allclose(
            [
                -56.12233,
                -56.13586,
                -56.13586,
                -56.01577,
                0.10924,
                354.11072,
                354.12204,
                19.70547,
                20.71265,
                2947896667.0,
                3098568884.0,
                10335.713263,
            ],
            [
                systemtable["sub_sun_lat"],
                systemtable["sub_sun_lat_min"],
                systemtable["sub_sun_lat_max"],
                systemtable["opening_angle"],
                systemtable["phase_angle"],
                systemtable["sub_sun_lon"],
                systemtable["sub_obs_lon"],
                systemtable["d_sun_AU"],
                systemtable["d_obs_AU"],
                systemtable["d_sun_km"],
                systemtable["d_obs_km"],
                systemtable["light_time"],
            ],
            rtol=1e-3,
        )

        # check a moon in body table
        mab = bodytable[bodytable.loc_indices["Mab"]]
        assert mab["NAIF ID"] == 726
        assert mab["Body"] == "Mab"
        mabclose = assert_quantity_allclose(
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
                mab["RA (deg)"],
                mab["Dec (deg)"],
                mab["dRA"],
                mab["dDec"],
                mab["sub_obs_lon"],
                mab["sub_obs_lat"],
                mab["sub_sun_lon"],
                mab["sub_sun_lat"],
                mab["phase"],
                mab["distance"],
            ],
            rtol=1e-3,
        )

        # check a ring in ringtable
        beta = ringtable[ringtable.loc_indices["Beta"]]
        assert np.isclose(beta["pericenter"], 231.051, rtol=1e-3)
        assert np.isclose(beta["ascending node"], 353.6, rtol=1e-2)

    def test_bad_query_exception_throw():

        with pytest.raises(ValueError):
            pds.RingNode(planet="Mercury", obs_time="2022-05-03 00:00").ephemeris()

        with pytest.raises(ValueError):
            pds.RingNode(planet="Uranus", obs_time="2022-13-03 00:00").ephemeris()

        with pytest.raises(ValueError):
            pds.RingNode(planet="Neptune", obs_time="2022-05-03 00:00").ephemeris(
                observer_coords=(1000, 10.0, -120.355)
            )

        with pytest.raises(ValueError):
            pds.RingNode(planet="Neptune", obs_time="2022-05-03 00:00").ephemeris(
                observer_coords=(10.0, -120.355, 1000), neptune_arcmodel=0
            )
