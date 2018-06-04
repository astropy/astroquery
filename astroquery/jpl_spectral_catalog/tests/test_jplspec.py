

import numpy as np

import os

from astropy import units as u
from astropy.table import Table

from ...jpl_spectral_catalog import JPLSpec

data = 'CO.data'

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir,filename)

class MockResponseSpec(object):

    def __init__(self):
        self.filename = data_path(data)

    @property
    def text(self):
        with open(self.filename) as f:
            return f.read()

def test_input_async():
    response = JPLSpec.query_lines_async(min_frequency = 100 * u.GHz, max_frequency = 1000 * u.GHz,\
    min_strength = -500,molecule = "28001 CO", get_query_payload = True)
    assert response['Mol'] == "28001 CO"
    np.testing.assert_almost_equal(response['MinNu'], 100.)
    np.testing.assert_almost_equal(response['MaxNu'], 1000.)

def test_query():
    jplspec = JPLSpec()
    response = MockResponseSpec()
    tbl = JPLSpec._parse_result(response)
    assert isinstance(tbl,Table)
    assert len(tbl) == 8
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
           'TAG', 'QNFMT', 'QN\'', 'QN"'])

    assert tbl['FREQ'][0] == 115271.2018
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -5.0105
    assert tbl['ERR'][7] == .0050
    assert tbl['FREQ'][7] == 921799.7000
    assert tbl['QN"'][7] == 7
    assert tbl['ELO'][1] == 3.8450
