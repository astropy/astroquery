import os
import unittest
import json
from astropy.tests.helper import remote_data
from astroquery.dace import Dace

HARPS_PUBLICATION = '2009A&A...493..639M'


@remote_data
class TestDaceClass(unittest.TestCase):

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

    def test_transform_data_as_dict(self):
        expected_parameter_dict = {'ccf_noise': [0.005320016177906, 0.00393390440796704, 0.0032324617496158],
                                   'ins_name': ['CORALIE98', 'CORALIE98', 'HARPS'],
                                   'drs_qc': [True, True, False],
                                   'rjd': [51031, 51039, 51088],
                                   'rv': [31300.4226771379, 31295.5671320506, 31294.3391634734],
                                   'rv_err': [5.420218247708816, 4.0697289792344185, 3.4386352834851026]}
        with open(self._data_path('parameter_list.json'), 'r') as file:
            parameter_list = json.load(file)
        parameter_dict = Dace._transform_data_as_dict(parameter_list)
        assert parameter_dict == expected_parameter_dict

    @staticmethod
    def _data_path(filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)


if __name__ == "__main__":
    unittest.main()
