import pytest
from astropy import units as u

from ..core import SvoFps


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
        table = SvoFps.get_filter_list(test_facility, test_instrument)
        # Check if column for Filter ID (named 'filterID') exists in table
        assert 'filterID' in table.colnames
