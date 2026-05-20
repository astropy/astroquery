from io import BytesIO

import pytest
from astropy import units as u
from astropy.io.votable import parse

from astroquery.svo_fps import conf, SvoFps
from astroquery.svo_fps.core import QUERY_PARAMETERS, SVO_PARAM_NAMES


@pytest.mark.remote_data
class TestSvoFpsClass:

    def test_get_filter_index(self):
        table = SvoFps.get_filter_index(12_000*u.angstrom, 12_100*u.angstrom)
        # Check if column for Filter ID (named 'filterID') exists in table
        assert 'filterID' in table.colnames

    @pytest.mark.parametrize('test_filter_id',
                             ['HST/NICMOS1.F113N', 'HST/WFPC2-pc.f218w'])
    def test_get_transmission_data(self, test_filter_id):
        table = SvoFps.get_transmission_data(test_filter_id)
        # Check if data is downloaded properly, with > 0 rows
        assert len(table) > 0

    @pytest.mark.parametrize('test_filter_id',
                             ['NewHorizons/MVIC.Blue', 'Palomar/ZTF.r'])
    def test_get_filter_metadata(self, test_filter_id):
        params = SvoFps.get_filter_metadata(test_filter_id)
        # Check if expected keys are present
        assert "WavelengthEff" in params
        assert "ZeroPoint" in params
        # Check existence and value of what should be a constant
        assert params.get("FilterProfileService") == "ivo://svo/fps"

    @pytest.mark.parametrize('test_facility, test_instrument',
                             [('HST', 'WFPC2'), ('Keck', None)])
    def test_get_filter_list(self, test_facility, test_instrument):
        table = SvoFps.get_filter_list(test_facility, instrument=test_instrument)
        # Check if column for Filter ID (named 'filterID') exists in table
        assert 'filterID' in table.colnames

    @pytest.mark.parametrize('test_filter_id, mag_system, expected_zp_jy', [
        ('2MASS/2MASS.J', 'Vega', 1594.0),
        ('2MASS/2MASS.J', 'AB', 3631.0),
    ])
    def test_get_zeropoint(self, test_filter_id, mag_system, expected_zp_jy):
        zp = SvoFps.get_zeropoint(test_filter_id, mag_system=mag_system)
        # Check all expected keys are present
        assert 'ZeroPoint' in zp
        assert 'MagSys' in zp
        assert 'ZeroPointType' in zp
        assert 'ZeroPointUnit' in zp
        # Check the magnitude system matches what was requested
        assert zp['MagSys'] == mag_system
        # Check zero point has the right unit and an approximately correct value
        assert zp['ZeroPoint'].unit == u.Jy
        assert abs(zp['ZeroPoint'].value - expected_zp_jy) < 10.0

    def test_query_parameter_names(self):
        # Checks if `QUERY_PARAMETERS` (snake_case, lowercase) is up to date
        # against the SVO server's native (CamelCase) parameter names.
        query = {"FORMAT": "metadata"}
        response = BytesIO(
            SvoFps._request(
                "GET", conf.base_url, params=query, timeout=conf.timeout, cache=False
            ).content
        )
        server_params = {p.name.split(":")[1]
                         for p in parse(response).resources[0].params}
        # Inverse mapping so we can compare server's CamelCase against our
        # snake_case `QUERY_PARAMETERS`.
        svo_to_snake = {v: k for k, v in SVO_PARAM_NAMES.items()}
        # All server-returned parameters should map to something we know about.
        unknown = server_params - set(svo_to_snake)
        assert not unknown, f"server returned unknown params: {unknown}"
        # Translate server-returned names to snake_case.
        server_params_snake = {svo_to_snake[p] for p in server_params}
        # All names we know about should appear on the server (modulo a few
        # we keep in `QUERY_PARAMETERS` but the metadata endpoint doesn't
        # report).
        for p in QUERY_PARAMETERS.difference(server_params_snake):
            # `QUERY_PARAMETERS` also contains base names without "_min" or
            # "_max" ending because "Param_min=a&Param_max=b" can be
            # replaced with "Param=a/b".
            if p + "_min" not in server_params_snake:
                # Server doesn't echo these back in the metadata response.
                assert p in {"verb", "format", "phot_cal_id", "id"}
