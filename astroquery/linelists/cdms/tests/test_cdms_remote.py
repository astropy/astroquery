import pytest
import numpy as np
from astropy import units as u
from astropy.table import Table

from astroquery.linelists.cdms import CDMS
from .test_cdms import colname_set


@pytest.mark.remote_data
def test_remote():
    tbl = CDMS.query_lines(min_frequency=500 * u.GHz,
                           max_frequency=1000 * u.GHz,
                           min_strength=-500,
                           temperature_for_intensity=0,
                           molecule="018505 H2O+")
    assert isinstance(tbl, Table)
    assert len(tbl) == 116
    # when 'temperature_for_intensity = 0', we use LGAIJ instead of LGINT
    assert set(tbl.keys()) == (colname_set | {'LGAIJ'}) - {'LGINT'}

    assert tbl['FREQ'][0] == 505366.7875
    assert tbl['ERR'][0] == 49.13
    assert tbl['LGAIJ'][0] == -4.3903


@pytest.mark.remote_data
def test_remote_300K():
    tbl = CDMS.query_lines(min_frequency=500 * u.GHz,
                           max_frequency=1000 * u.GHz,
                           min_strength=-500,
                           temperature_for_intensity=300,  # default
                           molecule="018505 H2O+")
    assert isinstance(tbl, Table)
    assert len(tbl) == 116
    assert set(tbl.keys()) == colname_set

    assert tbl['FREQ'][0] == 505366.7875
    assert tbl['ERR'][0] == 49.13
    assert tbl['LGINT'][0] == -4.2182
    assert tbl['MOLWT'][0] == 18
    assert tbl['TAG'][0] == 18505


@pytest.mark.remote_data
def test_co_basics():
    tbl = CDMS.get_molecule('028503')
    assert tbl['Q1'][0] == 1
    assert tbl['Q7'][0] == 0
    assert tbl['Q1'][10] == 11
    assert tbl['Q7'][10] == 10
    assert tbl['MOLWT'][0] == 28
    assert tbl['TAG'][0] == -28503


@pytest.mark.remote_data
def test_ch3cn_negqn():
    # 041505 = CH3CN on 2025-05-21
    tbl = CDMS.get_molecule('041505')
    assert tbl.meta['molecule'] == 'CH3CN, v=0'
    fourtominusthree = tbl[(tbl['Q1'] == 4) & (tbl['Q2'] == -3)]
    assert len(fourtominusthree) >= 1

    # check specifically for -21, which is encoded as `b1`
    twentytwominustwentyone = tbl[(tbl['Q1'] == 22) & (tbl['Q2'] == -21)]
    assert len(twentytwominustwentyone) >= 1

    assert tbl['TAG'][0] == 41505

    twentythreeminustwentyone = tbl[(tbl['Q1'] == 23) & (tbl['Q2'] == -21)]
    assert len(twentythreeminustwentyone) >= 1
    assert twentythreeminustwentyone['TAG'][0] == -41505


@pytest.mark.remote_data
def test_propanediol():
    tbl1 = CDMS.get_molecule('076513')
    assert 'int' in tbl1['Q2'].dtype.name

    tbl = CDMS.query_lines(min_frequency=100.3 * u.GHz,
                           max_frequency=100.5 * u.GHz,
                           molecule='076513')
    assert isinstance(tbl, Table)
    assert len(tbl) >= 1
    assert 'aG\'g-1,2-Propanediol' in tbl['name']
    # check that the parser worked - this will be string or obj otherwise
    assert 'int' in tbl['Ku'].dtype.name
    assert tbl['MOLWT'][0] == 76
    assert tbl['TAG'][0] == 76513


@pytest.mark.remote_data
def test_remote_regex():

    tbl = CDMS.query_lines(min_frequency=500 * u.GHz,
                           max_frequency=600 * u.GHz,
                           min_strength=-500,
                           molecule=('028501 HC-13-N, v=0', '028502 H2CN' '028503 CO, v=0'))

    assert isinstance(tbl, Table)
    assert len(tbl) == 557
    assert set(tbl.keys()) == colname_set

    assert set(tbl['name']) == {'H2CN', 'HC-13-N, v=0'}


@pytest.mark.remote_data
def test_molecule_with_parens():
    """
    Regression test for 2375
    """
    tbl = CDMS.query_lines(232567.224454 * u.MHz, 234435.809432 * u.MHz, molecule='H2C(CN)2', parse_name_locally=True)

    assert len(tbl) == 49

    MC = np.ma.core.MaskedConstant()

    for col, val in zip(tbl[0].colnames, (232588.7246, 0.2828, -4.1005, 3, 293.8540, 445, 66506,
                        303, 44, 14, 30, MC, MC, MC, 45, 13, 33, MC, MC, MC, 'H2C(CN)2', 66, False)):
        if val is MC:
            assert tbl[0][col].mask
        else:
            assert tbl[0][col] == val

    # this test row includes degeneracy = 1225, which covers one of the weird letter-is-number parser cases
    for col, val in zip(tbl[16].colnames, (233373.369, 10.26, -4.8704, 3, 1229.0674, 1125, 66506,
                        303, 112, 10, 102, MC, MC, MC, 112, 9, 103, MC, MC, MC, 'H2C(CN)2', 66, False),):
        if val is MC:
            assert tbl[16][col].mask
        else:
            assert tbl[16][col] == val


@pytest.mark.remote_data
def test_complex_molecule_remote():
    """
    Part of the regression test for 2409.  See "test_hc7n" in the non-remote
    tests.  This version covers both the local name parsing and checks whether
    there are upstream changes.
    """
    tbl = CDMS.query_lines(200*u.GHz, 230.755608*u.GHz, molecule='HC7N', parse_name_locally=True)
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


@pytest.mark.remote_data
def test_retrieve_species_table():
    species_table = CDMS.get_species_table(use_cached=False, write_new_species_cache=False)
    # as of 2025/01/16
    assert len(species_table) >= 1293
    assert 'int' in species_table['tag'].dtype.name
    assert 'int' in species_table['#lines'].dtype.name
    assert 'float' in species_table['lg(Q(1000))'].dtype.name


@pytest.mark.remote_data
def test_remote_all_species():
    tbl = CDMS.query_lines(min_frequency=100.3 * u.GHz,
                           max_frequency=100.5 * u.GHz,
                           min_strength=-5)
    assert isinstance(tbl, Table)

    AlS_is_in_table = (tbl['name'] == 'AlS').sum() > 0
    Propanediol_is_in_table = (tbl['name'] == "aG'g-1,2-Propanediol").sum() > 0

    assert AlS_is_in_table
    assert Propanediol_is_in_table


@pytest.mark.bigdata
@pytest.mark.remote_data
class TestRegressionAllCats:
    species_table = CDMS.get_species_table(write_new_species_cache=False)

    @pytest.mark.parametrize('row', species_table)
    def test_regression_allcats(self, row):
        """
        Expensive test - try all the molecules
        """
        tag = f"{row['tag']:06d}"
        result = CDMS.get_molecule(tag)
        assert len(result) >= 1
