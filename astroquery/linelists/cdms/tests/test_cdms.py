import numpy as np
import pytest

import os

from astropy import units as u
from astropy.table import Table
from astroquery.linelists.cdms.core import CDMS, parse_letternumber, build_lookup
from astroquery.utils.mocks import MockResponse

colname_set = set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP', 'TAG', 'QNFMT',
                   'Ju', 'Jl', "vu", "F1u", "F2u", "F3u", "vl", "Ku", "Kl",
                   "F1l", "F2l", "F3l", "name", "MOLWT", "Lab"])


def data_path(filename):

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def mockreturn(*args, method='GET', data={}, url='', **kwargs):
    if method == 'GET':
        molecule = url.split('cdmstab')[1].split('.')[0]
        with open(data_path(molecule+".data"), 'rb') as fh:
            content = fh.read()
        return MockResponse(content=content)
    elif method == 'POST':
        molecule = dict(data)['Molecules']
        with open(data_path("post_response.html"), 'r') as fh:
            content = fh.read().format(replace=molecule).encode()
        return MockResponse(content=content)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(CDMS, '_request', mockreturn)
    return mp


def test_input_async():

    response = CDMS.query_lines_async(min_frequency=100 * u.GHz,
                                      max_frequency=1000 * u.GHz,
                                      min_strength=-500,
                                      molecule="028503 CO, v=0",
                                      get_query_payload=True)
    response = dict(response)
    assert response['Molecules'] == "028503 CO, v=0"
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


def test_query(patch_post):

    tbl = CDMS.query_lines(min_frequency=100 * u.GHz,
                           max_frequency=1000 * u.GHz,
                           min_strength=-500,
                           molecule='028503 CO, v=0'
                           )
    assert isinstance(tbl, Table)
    assert len(tbl) == 8
    assert set(tbl.keys()) == colname_set

    assert tbl['FREQ'][0] == 115271.2018
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -7.1425
    assert tbl['GUP'][0] == 3
    assert tbl['GUP'][7] == 17


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


def test_hc7s(patch_post):
    """
    Test for a very complicated molecule

    CDMS.query_lines_async(100*u.GHz, 100.755608*u.GHz, molecule='HC7S', parse_name_locally=True)
    """

    tbl = CDMS.query_lines(100*u.GHz, 100.755608*u.GHz, molecule='117501 HC7S',)
    assert isinstance(tbl, Table)
    assert len(tbl) == 5
    assert set(tbl.keys()) == colname_set

    assert tbl['FREQ'][0] == 100694.065
    assert tbl['ERR'][0] == 0.4909
    assert tbl['LGINT'][0] == -3.9202
    assert tbl['MOLWT'][0] == 117

    assert tbl['GUP'][0] == 255
    assert tbl['Ju'][0] == 126
    assert tbl['Jl'][0] == 125
    assert tbl['vu'][0] == 127
    assert tbl['vl'][0] == 126
    assert tbl['Ku'][0] == -1
    assert tbl['Kl'][0] == 1
    assert tbl['F1u'][0] == 127
    assert tbl['F1l'][0] == 126


def test_hc7n(patch_post):
    """
    Regression test for 2409, specifically that GUP>1000 was not being
    processed correctly b/c the first digit of GUP was being included in the
    previous column (frequency)

    CDMS.query_lines(200*u.GHz, 230.755608*u.GHz, molecule='HC7N',parse_name_locally=True)
    """

    tbl = CDMS.query_lines(200*u.GHz, 230.755608*u.GHz, molecule='099501 HC7N, v=0')
    assert isinstance(tbl, Table)
    assert len(tbl) == 27
    assert set(tbl.keys()) == colname_set

    assert tbl['FREQ'][0] == 200693.406
    assert tbl['ERR'][0] == 0.01
    assert tbl['LGINT'][0] == -2.241
    assert tbl['MOLWT'][0] == 99

    assert tbl['GUP'][0] == 1071
    assert tbl['Ju'][0] == 178
    assert tbl['Jl'][0] == 177
    assert tbl['vu'][0].mask
    assert tbl['vl'][0].mask
    assert tbl['Ku'][0].mask
    assert tbl['Kl'][0].mask
    assert tbl['F1u'][0].mask
    assert tbl['F1l'][0].mask
    assert tbl['Lab'][0]


def test_retrieve_species_table_local():
    species_table = CDMS.get_species_table(use_cached=True)
    assert len(species_table) == 1300
    assert 'int' in species_table['tag'].dtype.name
    assert 'int' in species_table['#lines'].dtype.name
    assert 'float' in species_table['lg(Q(1000))'].dtype.name


def test_lut_multitable():
    # Regression test for the different names used in the partition table and the other tables
    lut = build_lookup()

    assert lut.find('ethyl formate', 0)['ethyl formate'] == 74514
    assert lut.find('C2H5OCHO', 0)['C2H5OCHO'] == 74514
    assert lut.find('C2H4O', 0)['c-C2H4O'] == 44504
    assert lut.find('Ethylene oxide', 0)['Ethylene oxide'] == 44504


def test_lut_literal():
    # regression for 2901
    lut = build_lookup()

    hcop = lut.find('HCO+', 0)
    assert len(hcop) >= 16

    hcopv0 = lut.find('HCO+, v=0', 0)
    assert len(hcopv0) == 1
    assert hcopv0['HCO+, v=0'] == 29507

    # two spacings exist in the tables
    hcopv0 = lut.find('HCO+, v = 0', 0)
    assert len(hcopv0) == 1
    assert hcopv0['HCO+, v = 0'] == 29507

    thirteenco = lut.find('13CO', 0)
    assert len(thirteenco) == 1
    assert thirteenco['13CO'] == 29501
    thirteencostar = lut.find('13CO*', 0)
    assert len(thirteencostar) >= 252
