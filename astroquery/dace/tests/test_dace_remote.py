import pytest
from astroquery.dace import Dace

HARPS_PUBLICATION = '2009A&A...493..639M'


@pytest.mark.remote_data
class TestDaceClassRemote:

    def test_should_get_radial_velocities(self):
        radial_velocities_table = Dace.query_radial_velocities('HD40307')
        assert radial_velocities_table is not None and 'rv' in radial_velocities_table.colnames
        # HARPS is a spectrograph and has to be present for this target because HD40307 has been observed and
        # processed by this instrument
        assert 'HARPS' in radial_velocities_table['ins_name']
        assert HARPS_PUBLICATION in radial_velocities_table['pub_bibcode']
        public_harps_data = [row for row in radial_velocities_table['pub_bibcode'] if HARPS_PUBLICATION in row]
        assert len(public_harps_data) > 100
        assert len(radial_velocities_table['rv_err']) > 100
