import numpy as np

import os

from astropy import units as u
from astropy.table import Table
from astroquery.linelists.cdms import CDMS


def data_path(filename):

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class MockResponseSpec:

    def __init__(self, filename):
        self.filename = data_path(filename)

    @property
    def text(self):
        with open(self.filename) as f:
            return f.read()


def test_input_async():

    response = CDMS.query_lines_async(min_frequency=100 * u.GHz,
                                      max_frequency=1000 * u.GHz,
                                      min_strength=-500,
                                      molecule="028001 CO",
                                      get_query_payload=True)
    response = dict(response)
    assert response['Molecules'] == "028001 CO"
    np.testing.assert_almost_equal(response['MinNu'], 100.)
    np.testing.assert_almost_equal(response['MaxNu'], 1000.)


def test_input_multi():

    response = CDMS.query_lines_async(min_frequency=500 * u.GHz,
                                      max_frequency=1000 * u.GHz,
                                      min_strength=-500,
                                      molecule=r"^H[2D]O(-\d\d|)\+$",
                                      parse_name_locally=True,
                                      get_query_payload=True)
    response = dict(response)
    assert response['Molecules'] == '018505 H2O+'
    np.testing.assert_almost_equal(response['MinNu'], 500.)
    np.testing.assert_almost_equal(response['MaxNu'], 1000.)


def test_query():

    response = MockResponseSpec('CO.data')
    tbl = CDMS._parse_result(response)
    assert isinstance(tbl, Table)
    assert len(tbl) == 8
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Ju', 'Jl', "vu", "vl", "Ku", "Kl", "F", "name"])

    assert tbl['FREQ'][0] == 115271.2018
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -7.1425
