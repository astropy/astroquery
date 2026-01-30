import numpy as np
import pytest

import os

from astropy import units as u
from astropy.table import Table
from astroquery.linelists.cdms.core import CDMS, parse_letternumber, build_lookup
from astroquery.utils.mocks import MockResponse
from astroquery.exceptions import InvalidQueryError

colname_set = set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP', 'TAG', 'QNFMT',
                   'Ju', 'Jl', "vu", "F1u", "F2u", "F3u", "vl", "Ku", "Kl",
                   "F1l", "F2l", "F3l", "name", "MOLWT", "Lab"])


def data_path(filename):

    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def mockreturn(*args, method='GET', data={}, url='', **kwargs):
    if method == 'GET':
        # Handle get_molecule requests (classic URL format)
        if '/entries/c' in url:
            molecule = url.split('/entries/c')[1].split('.')[0]
            with open(data_path(f"c{molecule}.cat"), 'rb') as fh:
                content = fh.read()
            return MockResponse(content=content)
        # Handle regular query_lines requests
        else:
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
    assert tbl['MOLWT'][0] == 28


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
    assert parse_letternumber("a0") == -10
    assert parse_letternumber("b0") == -20
    assert parse_letternumber("ZZ") == 3535

    assert parse_letternumber(np.ma.masked) == -999999


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
    assert len(species_table) == 1306
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


def test_malformatted_molecule_raises_error(patch_post):
    """
    Test that querying a malformatted molecule raises an error when
    fallback_to_getmolecule is False (default behavior)
    """
    # H2C2S is in the MALFORMATTED_MOLECULE_LIST
    with pytest.raises(ValueError, match="is known not to comply with standard CDMS format"):
        CDMS.query_lines(min_frequency=100 * u.GHz,
                         max_frequency=300 * u.GHz,
                         molecule='058501 H2C2S',
                         fallback_to_getmolecule=False)


def test_malformatted_molecule_with_fallback(patch_post):
    """
    Test that querying a malformatted molecule with fallback_to_getmolecule=True
    successfully falls back to get_molecule
    """
    # H2C2S is in the MALFORMATTED_MOLECULE_LIST
    tbl = CDMS.query_lines(min_frequency=100 * u.GHz,
                           max_frequency=300 * u.GHz,
                           molecule='058501 H2C2S',
                           fallback_to_getmolecule=True)

    assert isinstance(tbl, Table)
    assert len(tbl) == 3
    assert tbl['FREQ'][0] == 114.9627
    assert tbl['FREQ'][1] == 344.8868
    assert tbl['FREQ'][2] == 689.7699
    assert tbl['TAG'][0] == 58501
    assert tbl['GUP'][0] == 9


def test_malformatted_molecule_id_only_with_fallback(patch_post):
    """
    Test that querying with just the molecule ID (058501) also works with fallback
    """
    # Just the ID is also in the badlist
    tbl = CDMS.query_lines(min_frequency=100 * u.GHz,
                           max_frequency=300 * u.GHz,
                           molecule='058501',
                           fallback_to_getmolecule=True)

    assert isinstance(tbl, Table)
    assert len(tbl) == 3
    assert tbl['FREQ'][0] == 114.9627


def test_malformatted_molecule_name_only_with_fallback_error(patch_post):
    """
    Test that querying with just the molecule name (H2C2S) without parse_name_locally
    raises an error because H2C2S (5 chars) is not a valid 6-digit molecule ID.

    When parse_name_locally=False, "H2C2S" is passed as-is to _mol_to_payload,
    which returns "H2C2S". This is in the badlist, so fallback is triggered,
    but get_molecule("H2C2S") fails because it's not a 6-digit ID.
    """
    # Just the name is also in the badlist, but it's not a 6-digit ID
    with pytest.raises(ValueError, match="needs to be formatted as.*6-digit string ID"):
        CDMS.query_lines(min_frequency=100 * u.GHz,
                         max_frequency=300 * u.GHz,
                         molecule='H2C2S',
                         parse_name_locally=False,
                         fallback_to_getmolecule=True)


def test_malformatted_molecule_name_with_parse_locally_success(patch_post):
    """
    Test that querying with just the molecule name (H2C2S) WITH parse_name_locally=True
    successfully resolves to "058501 H2C2S" and then falls back to get_molecule.

    When parse_name_locally=True, "H2C2S" is looked up and converted to "058501 H2C2S",
    which is in the badlist, so fallback is triggered and succeeds.
    """
    tbl = CDMS.query_lines(min_frequency=100 * u.GHz,
                           max_frequency=300 * u.GHz,
                           molecule='H2C2S',
                           parse_name_locally=True,
                           fallback_to_getmolecule=True)

    assert isinstance(tbl, Table)
    assert len(tbl) == 3
    assert tbl['TAG'][0] == 58501


def test_get_query_payload_skips_fallback(patch_post):
    """
    Test that when get_query_payload=True, the fallback is not triggered
    even for malformatted molecules
    """
    # This should return the payload without triggering fallback or error
    payload = CDMS.query_lines(min_frequency=100 * u.GHz,
                               max_frequency=300 * u.GHz,
                               molecule='058501 H2C2S',
                               get_query_payload=True)

    assert isinstance(payload, dict)
    assert 'Molecules' in payload
    assert payload['Molecules'] == '058501 H2C2S'


def test_malformatted_with_parse_name_locally_and_fallback_error():
    """
    Test that when parse_name_locally=True with a malformatted molecule
    and fallback is enabled, but molecule can't be resolved, we get
    proper error message about parsing failure
    """
    # First, the lookup will fail to find 'NOTREALMOLECULE' and raise InvalidQueryError
    # before we even get to the fallback logic
    with pytest.raises(InvalidQueryError, match="No matching species found"):
        CDMS.query_lines(min_frequency=100 * u.GHz,
                         max_frequency=300 * u.GHz,
                         molecule='NOTREALMOLECULE',
                         parse_name_locally=True,
                         fallback_to_getmolecule=True)
