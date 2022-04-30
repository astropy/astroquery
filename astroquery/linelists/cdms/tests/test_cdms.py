import numpy as np

import os

from astropy import units as u
from astropy.table import Table
from astroquery.linelists.cdms.core import CDMS, parse_letternumber

colname_set = set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP', 'TAG', 'QNFMT',
                   'Ju', 'Jl', "vu", "F1u", "F2u", "F3u", "vl", "Ku", "Kl",
                   "F1l", "F2l", "F3l", "name", "MOLWT", "Lab"])

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
    assert set(tbl.keys()) == colname_set

    assert tbl['FREQ'][0] == 115271.2018
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -7.1425


def test_parseletternumber():
    """
    Very Important:
    Exactly two characters are available for each quantum number. Therefore, half
    integer quanta are rounded up ! In addition, capital letters are used to
    indicate quantum numbers larger than 99. E. g. A0 is 100, Z9 is 359. Small
    types are used to signal corresponding negative quantum numbers.
    """

    # examples from the docs
    assert parse_letternumber("A0") == 100
    assert parse_letternumber("Z9") == 359

    # inferred?
    assert parse_letternumber("z9") == -359
    assert parse_letternumber("ZZ") == 3535


def test_hc7s():
    """
    Test for a very complicated molecule

    CDMS.query_lines_async(100*u.GHz, 100.755608*u.GHz, molecule='HC7S', parse_name_locally=True)
    """

    response = MockResponseSpec('HC7S.data')
    tbl = CDMS._parse_result(response)
    assert isinstance(tbl, Table)
    assert len(tbl) == 5
    assert set(tbl.keys()) == colname_set

    assert tbl['FREQ'][0] == 100694.065
    assert tbl['ERR'][0] == 0.4909
    assert tbl['LGINT'][0] == -3.9202
    assert tbl['MOLWT'][0] == 117

    assert tbl['Ju'][0] == 126
    assert tbl['Jl'][0] == 125
    assert tbl['vu'][0] == 127
    assert tbl['vl'][0] == 126
    assert tbl['Ku'][0] == -1
    assert tbl['Kl'][0] == 1
    assert tbl['F1u'][0] == 127
    assert tbl['F1l'][0] == 126
