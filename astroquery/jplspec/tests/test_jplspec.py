import numpy as np

import os

from astropy import units as u
from astropy.table import Table
from ...jplspec import JPLSpec

file1 = 'CO.data'
file2 = 'CO_6.data'
file3 = 'multi.data'


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

    response = JPLSpec.query_lines_async(min_frequency=100 * u.GHz,
                                         max_frequency=1000 * u.GHz,
                                         min_strength=-500,
                                         molecule="28001 CO",
                                         get_query_payload=True)
    response = dict(response)
    assert response['Mol'] == "28001 CO"
    np.testing.assert_almost_equal(response['MinNu'], 100.)
    np.testing.assert_almost_equal(response['MaxNu'], 1000.)


def test_input_maxlines_async():

    response = JPLSpec.query_lines_async(min_frequency=100 * u.GHz,
                                         max_frequency=1000 * u.GHz,
                                         min_strength=-500,
                                         molecule="28001 CO",
                                         max_lines=6,
                                         get_query_payload=True)
    response = dict(response)
    assert response['Mol'] == "28001 CO"
    assert response['MaxLines'] == 6.
    np.testing.assert_almost_equal(response['MinNu'], 100.)
    np.testing.assert_almost_equal(response['MaxNu'], 1000.)


def test_input_multi():

    response = JPLSpec.query_lines_async(min_frequency=500 * u.GHz,
                                         max_frequency=1000 * u.GHz,
                                         min_strength=-500,
                                         molecule=r"^H[2D]O(-\d\d|)$",
                                         parse_name_locally=True,
                                         get_query_payload=True)
    response = dict(response)
    assert set(response['Mol']) == set((18003, 19002, 19003, 20003, 21001))
    np.testing.assert_almost_equal(response['MinNu'], 500.)
    np.testing.assert_almost_equal(response['MaxNu'], 1000.)


def test_query():

    response = MockResponseSpec(file1)
    tbl = JPLSpec._parse_result(response)
    assert isinstance(tbl, Table)
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


def test_query_truncated():

    response = MockResponseSpec(file2)
    tbl = JPLSpec._parse_result(response)
    assert isinstance(tbl, Table)
    assert len(tbl) == 6
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"'])

    assert tbl['FREQ'][0] == 115271.2018
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -5.0105
    assert tbl['ELO'][1] == 3.8450


def test_query_multi():

    response = MockResponseSpec(file3)
    tbl = JPLSpec._parse_result(response)
    assert isinstance(tbl, Table)
    assert len(tbl) == 208
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"'])

    assert tbl['FREQ'][0] == 503568.5200
    assert tbl['ERR'][0] == 0.0200
    assert tbl['LGINT'][0] == -4.9916
    assert tbl['TAG'][0] == -18003
    assert tbl['TAG'][38] == -19002
    assert tbl['TAG'][207] == 21001
