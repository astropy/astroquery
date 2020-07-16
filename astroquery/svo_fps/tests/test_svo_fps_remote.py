import pytest
import astropy.io.votable.exceptions

from ..core import SvoFps


@pytest.mark.remote_data
class TestSvoFpsClass:

    def test_get_filter_index(self):
        table = SvoFps.get_filter_index()
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

    # Test for failing case (a dummy invalid query)
    def test_IndexError_in_data_from_svo(self):
        invalid_query = {'Invalid_param': 0}
        with pytest.raises(astropy.io.votable.exceptions.E09) as exc:
            SvoFps.data_from_svo(invalid_query)

        assert 'must have a value attribute' in str(exc)
