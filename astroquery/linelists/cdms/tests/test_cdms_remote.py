import pytest
from astropy import units as u
from astropy.table import Table

from astroquery.linelists.cdms import CDMS


@pytest.mark.remote_data
def test_remote():
    tbl = CDMS.query_lines(min_frequency=500 * u.GHz,
                           max_frequency=1000 * u.GHz,
                           min_strength=-500,
                           temperature_for_intensity=0,
                           molecule="018505 H2O+")
    assert isinstance(tbl, Table)
    assert len(tbl) == 116
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGAIJ', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Ju', 'Jl', "vu", "vl", "Ku", "Kl", "F", "name"])

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
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Ju', 'Jl', "vu", "vl", "Ku", "Kl", "F", "name"])

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
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Ju', 'Jl', "vu", "vl", "Ku", "Kl", "F", "name"])

    assert set(tbl['name']) == {'H2CN', 'HC-13-N, v=0'}
