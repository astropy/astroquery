from io import BytesIO

import pytest
from astropy import units as u
from astropy.io.votable import parse

from astroquery.svo_fps import conf, SvoFps
from astroquery.svo_fps.core import QUERY_PARAMETERS


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

    @pytest.mark.parametrize('test_facility, test_instrument',
                             [('HST', 'WFPC2'), ('Keck', None)])
    def test_get_filter_list(self, test_facility, test_instrument):
        table = SvoFps.get_filter_list(test_facility, instrument=test_instrument)
        # Check if column for Filter ID (named 'filterID') exists in table
        assert 'filterID' in table.colnames

    def test_query_parameter_names(self):
        # Checks if `QUERY_PARAMETERS` is up to date.
        query = {"FORMAT": "metadata"}
        response = BytesIO(
            SvoFps._request(
                "GET", conf.base_url, params=query, timeout=conf.timeout, cache=False
            ).content
        )
        params = {p.name.split(":")[1] for p in parse(response).resources[0].params}
        # All valid parameters should be present in `QUERY_PARAMETERS`.
        assert not params.difference(QUERY_PARAMETERS)
        # Some valid parameter names are not in `params`.
        for p in QUERY_PARAMETERS.difference(params):
            # `QUERY_PARAMETERS` also contains names without "_min" or "_max" ending
            # because "Param_min=a&Param_max=b" can be replaced with "Param=a/b".
            if p + "_min" not in params:
                # There's a few extra parameters we didn't get from the server.
                assert p in {"VERB", "FORMAT", "PhotCalID", "ID"}
