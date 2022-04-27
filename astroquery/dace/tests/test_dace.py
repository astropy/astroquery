import os
import json
from astroquery.dace import Dace

DATA_FILES = {
    'parameter_list': 'parameter_list.json',
}


def test_transform_data_as_dict():
    expected_parameter_dict = {'ccf_noise': [0.005320016177906, 0.00393390440796704, 0.0032324617496158],
                               'ins_name': ['CORALIE98', 'CORALIE98', 'HARPS'],
                               'drs_qc': [True, True, False],
                               'rjd': [51031, 51039, 51088],
                               'rv': [31300.4226771379, 31295.5671320506, 31294.3391634734],
                               'rv_err': [5.420218247708816, 4.0697289792344185, 3.4386352834851026]}
    with open(_data_path('parameter_list.json'), 'r') as file:
        parameter_list = json.load(file)
    parameter_dict = Dace.transform_data_as_dict(parameter_list)
    assert parameter_dict == expected_parameter_dict


def _data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)
