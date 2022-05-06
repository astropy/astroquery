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

    for col, val in zip(tbl[0].colnames,
                        (232588.7246, 0.2828, -4.1005, 3, '293.85404', 45, 66, 506, 303, 44, 14, 30, MC, MC, MC, 45, 13, 33, MC, MC, MC, 'H2C(CN)2', False)):
        if val is MC:
            assert tbl[0][col].mask
        else:
            assert tbl[0][col] == val
