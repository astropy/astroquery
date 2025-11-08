import pytest
from astropy import units as u
from astropy.table import Table

from ..core import JPLSpec
from astroquery.exceptions import EmptyResponseError


@pytest.mark.xfail(reason="2025 server problems", raises=EmptyResponseError)
@pytest.mark.remote_data
def test_remote():
    JPLSpec.fallback_to_getmolecule = False
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule="18003 H2O")
    assert isinstance(tbl, Table)
    assert len(tbl) == 36
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"'])

    assert tbl['FREQ'][0] == 503568.5200
    assert tbl['ERR'][0] == 0.0200
    assert tbl['LGINT'][0] == -4.9916
    assert tbl['ERR'][7] == 12.4193
    assert tbl['FREQ'][35] == 987926.7590


@pytest.mark.remote_data
def test_remote_fallback():
    JPLSpec.fallback_to_getmolecule = True
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule="18003 H2O")
    assert isinstance(tbl, Table)
    tbl = tbl[((tbl['FREQ'].quantity > 500*u.GHz) & (tbl['FREQ'].quantity < 1*u.THz))]
    assert len(tbl) == 36
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Lab', 'Name',
                                   'QN"1', 'QN"2', 'QN"3', 'QN"4',
                                   "QN'1", "QN'2", "QN'3", "QN'4"
                                   ])

    assert tbl['FREQ'][0] == 503568.5200
    assert tbl['ERR'][0] == 0.0200
    assert tbl['LGINT'][0] == -4.9916
    assert tbl['ERR'][7] == 12.4193
    assert tbl['FREQ'][35] == 987926.7590


@pytest.mark.remote_data
def test_remote_regex_fallback():
    """
    CO, H13CN, HC15N
    Some of these have different combinations of QNs
    """
    JPLSpec.fallback_to_getmolecule = True
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule=("28001", "28002", "28003"))
    assert isinstance(tbl, Table)
    tbl = tbl[((tbl['FREQ'].quantity > 500*u.GHz) & (tbl['FREQ'].quantity < 1*u.THz))]
    assert len(tbl) == 16
    # there are more QN formats than the original query had
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"', 'Lab',
                                   'QN"1', 'QN"2', "QN'", "QN'1", "QN'2",
                                   'Name'
                                   ])

    assert tbl['FREQ'][0] == 576267.9305
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -3.0118
    assert tbl['ERR'][7] == 8.3063
    assert tbl['FREQ'][15] == 946175.3151


@pytest.mark.xfail(reason="2025 server problems", raises=EmptyResponseError)
@pytest.mark.remote_data
def test_remote_regex():
    JPLSpec.fallback_to_getmolecule = False
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule=("28001", "28002", "28003"))
    assert isinstance(tbl, Table)
    assert len(tbl) == 16
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'QN\'', 'QN"',
                                   ])

    assert tbl['FREQ'][0] == 576267.9305
    assert tbl['ERR'][0] == .0005
    assert tbl['LGINT'][0] == -3.0118
    assert tbl['ERR'][7] == 8.3063
    assert tbl['FREQ'][15] == 946175.3151


@pytest.mark.remote_data
def test_get_molecule_remote():
    """Test get_molecule with remote data retrieval."""
    # Test with H2O
    tbl = JPLSpec.get_molecule(18003)
    
    assert isinstance(tbl, Table)
    assert len(tbl) > 0
    
    # Check expected columns including Lab flag
    expected_cols = {'FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                     'TAG', 'QNFMT', 'Lab',
                     'QN"1', 'QN"2', 'QN"3', 'QN"4',
                     "QN'1", "QN'2", "QN'3", "QN'4"}
    assert set(tbl.keys()) == expected_cols
    
    # Check units
    assert tbl['FREQ'].unit == u.MHz
    assert tbl['ERR'].unit == u.MHz
    assert tbl['LGINT'].unit == u.nm**2 * u.MHz
    assert tbl['ELO'].unit == u.cm**(-1)
    
    # Check metadata was attached
    assert 'NAME' in tbl.meta
    assert tbl.meta['NAME'].strip() == 'H2O'
    assert 'TAG' in tbl.meta
    assert tbl.meta['TAG'] == 18003
    
    # Check Lab flag
    assert 'Lab' in tbl.colnames
    assert tbl['Lab'].dtype == bool
    
    # H2O should have some lab measurements
    assert sum(tbl['Lab']) > 0


@pytest.mark.remote_data
def test_get_molecule_string_id():
    """Test get_molecule with string ID format."""
    # Test with CO using string ID
    tbl = JPLSpec.get_molecule('028001')
    
    assert isinstance(tbl, Table)
    assert len(tbl) > 0
    assert 'NAME' in tbl.meta
    assert 'CO' in tbl.meta['NAME']


@pytest.mark.remote_data
def test_get_molecule_various():
    """Test get_molecule with various molecules."""
    test_molecules = [
        (28001, 'CO'),      # Simple diatomic
        (32003, 'CH3OH'),   # Complex organic
    ]
    
    for mol_id, expected_name in test_molecules:
        tbl = JPLSpec.get_molecule(mol_id)
        assert isinstance(tbl, Table)
        assert len(tbl) > 0
        assert 'NAME' in tbl.meta
        assert expected_name in tbl.meta['NAME']
        
        # Verify TAG values are positive
        assert all(tbl['TAG'] > 0)


@pytest.mark.remote_data
def test_get_molecule_qn1():
    tbl = JPLSpec.get_molecule(28001)
    assert isinstance(tbl, Table)
    assert len(tbl) > 0
    assert 'QN1"' in tbl.colnames
    assert 'QN2"' not in tbl.colnames
    assert "QN1'" in tbl.colnames
    assert "QN2'" not in tbl.colnames


@pytest.mark.remote_data
def test_get_molecule_qn4():
    """ CN has 4 QNs """
    tbl = JPLSpec.get_molecule(26001)
    assert isinstance(tbl, Table)
    assert len(tbl) > 0
    for ii in range(1, 5):
        assert f'QN"{ii}' in tbl.colnames
        assert f"QN'{ii}" in tbl.colnames