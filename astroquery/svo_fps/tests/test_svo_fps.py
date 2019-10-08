import pytest
from astropy.tests.helper import remote_data

from ..core import SvoFps


@remote_data
class TestSvoFpsClass:

    def test_get_filter_index(self):
        table = SvoFps.get_filter_index()
        # Check if column for Filter ID (named 'filterID') exists in table
        assert 'filterID' in table.to_table().colnames

    @pytest.mark.parametrize('test_filter_id',
                            ['HST/NICMOS1.F113N', 'HST/WFPC2.f218w'])
    def test_get_transmission_data(self, test_filter_id):
        table = SvoFps.get_transmission_data(test_filter_id)
        # Check if data is downloaded properly, with > 0 rows
        assert len(table.to_table()) > 0

    @pytest.mark.parametrize('test_facility, test_instrument',
                            [('HST', 'WFPC2'), ('Keck', None)])
    def test_get_filter_list(self, test_facility, test_instrument):
        table = SvoFps.get_filter_list(test_facility, test_instrument)
        # Check if column for Filter ID (named 'filterID') exists in table
        assert 'filterID' in table.to_table().colnames
