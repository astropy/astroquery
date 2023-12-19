import pytest
import numpy as np
import astropy.units as u

from ... import pds


@pytest.mark.remote_data
class TestRMSNodeClass:
    def test_ephemeris_query(self):

        bodytable, ringtable = pds.RMSNode.ephemeris(
            planet="Uranus",
            epoch="2022-05-03 00:00",
            location=(-120.355 * u.deg, 10.0 * u.deg, 1000 * u.m),
        )
        # check system table
        systemtable = bodytable.meta
        assert np.allclose(
            [-56.12233, -56.13586, -56.13586, -56.01577, 0.10924, 354.11072, 354.12204,
             2947896667.0, 3098568884.0, 10335.713263, ],
            [systemtable["sub_sun_lat"].to(u.deg).value, systemtable["sub_sun_lat_min"].to(u.deg).value,
             systemtable["sub_sun_lat_max"].to(u.deg).value, systemtable["opening_angle"].to(u.deg).value,
             systemtable["phase_angle"].to(u.deg).value, systemtable["sub_sun_lon"].to(u.deg).value,
             systemtable["sub_obs_lon"].to(u.deg).value, systemtable["d_sun"].to(u.km).value,
             systemtable["d_obs"].to(u.km).value, systemtable["light_time"].to(u.second).value, ],
            rtol=1e-2,
        )

        # check a moon in body table
        mab = bodytable[bodytable.loc_indices["Mab"]]
        assert mab["NAIF ID"] == 726
        assert mab["Body"] == "Mab"
        assert np.allclose(
            [42.011201, 15.801323, 5.368, 0.623, 223.976, 55.906, 223.969, 56.013, 0.10932, 3098.514, ],
            [mab["RA (deg)"].to(u.deg).value, mab["Dec (deg)"].to(u.deg).value, mab["dRA"].to(u.arcsec).value,
             mab["dDec"].to(u.arcsec).value, mab["sub_obs_lon"].to(u.deg).value,
             mab["sub_obs_lat"].to(u.deg).value, mab["sub_sun_lon"].to(u.deg).value, mab["sub_sun_lat"].to(u.deg).value,
             mab["phase"].to(u.deg).value, mab["distance"].to(u.km * 1e6).value, ],
            rtol=1e-2,
        )

        # check a ring in ringtable
        beta = ringtable[ringtable.loc_indices["Beta"]]
        assert np.isclose(beta["pericenter"].to(u.deg).value, 231.051, rtol=1e-3)
        assert np.isclose(beta["ascending node"].to(u.deg).value, 353.6, rtol=1e-2)
