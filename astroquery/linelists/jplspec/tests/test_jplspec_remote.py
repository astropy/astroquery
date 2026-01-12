import pytest
from astropy import units as u
from astropy.table import Table

from astroquery.linelists.jplspec import JPLSpec
from astroquery.exceptions import EmptyResponseError


@pytest.mark.xfail(reason="2025 server problems", raises=EmptyResponseError)
@pytest.mark.remote_data
def test_remote():
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule="18003 H2O",
                              fallback_to_getmolecule=False)
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
def test_remote_regex_fallback():
    """
    CO, H13CN, HC15N
    Some of these have different combinations of QNs
    """
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule=("28001", "28002", "28003"),
                              fallback_to_getmolecule=True)
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


# Starting in 2025, the JPL CGI server that did search queries broke totally.  See #3363
@pytest.mark.xfail(reason="2025 server problems", raises=EmptyResponseError)
@pytest.mark.remote_data
def test_remote_regex():
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule=("28001", "28002", "28003"),
                              fallback_to_getmolecule=False)
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
def test_remote_fallback():
    tbl = JPLSpec.query_lines(min_frequency=500 * u.GHz,
                              max_frequency=1000 * u.GHz,
                              min_strength=-500,
                              molecule="18003 H2O",
                              fallback_to_getmolecule=True)
    assert isinstance(tbl, Table)
    tbl = tbl[((tbl['FREQ'].quantity > 500*u.GHz) & (tbl['FREQ'].quantity < 1*u.THz))]
    assert len(tbl) == 36
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Lab',
                                   'QN"1', 'QN"2', 'QN"3', 'QN"4',
                                   "QN'1", "QN'2", "QN'3", "QN'4"
                                   ])

    assert tbl['FREQ'][0] == 503568.5200
    assert tbl['ERR'][0] == 0.0200
    assert tbl['LGINT'][0] == -4.9916
    assert tbl['ERR'][7] == 12.4193
    assert tbl['FREQ'][35] == 987926.7590


@pytest.mark.remote_data
@pytest.mark.parametrize('mol_id,expected_name', [
    (28001, 'CO'),      # Simple diatomic
    (32003, 'CH3OH'),   # Complex organic
    (13002, 'CH'),      # another simple molecule w/5 QNs
    (14004, 'CD'),      # no 2-digit QNs in first col
    (15001, 'NH'),      # incorrect QNFMT, says there are 5 QNs, only 4
    (18004, 'NH2D'),    # highlighted a mismatch between qnlen & n_qns
    # (32001, 'O2'),      # masked second QN set?
])
def test_get_molecule_various(mol_id, expected_name):
    """
    Test get_molecule with various molecules.

    CH & CD are both regression tests for difficult molecules with >4 QNs and
    missing 2-digit QNs (i.e., columns with _only_ 1-digit QNs at the start of
    the columns with QNs).
    """
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
    assert 'QN"' in tbl.colnames
    assert 'QN1"' not in tbl.colnames
    assert "QN'" in tbl.colnames
    assert "QN1'" not in tbl.colnames


@pytest.mark.remote_data
def test_get_molecule_qn4():
    """ CN has 4 QNs """
    tbl = JPLSpec.get_molecule(26001)
    assert isinstance(tbl, Table)
    assert len(tbl) > 0
    for ii in range(1, 5):
        assert f'QN"{ii}' in tbl.colnames
        assert f"QN'{ii}" in tbl.colnames


@pytest.mark.remote_data
def test_get_molecule_parser_details():
    """
    Verifying a known hard-to-parse row
         982.301   0.174 -17.8172 3  464.3000  9  320031304 4-2   2     5-5   2
         991.369   0.003  -9.8234 3  310.3570 37  32003130418 3 - 0    18 3 + 0
    """
    tbl = JPLSpec.get_molecule(32003)
    testrow = tbl[5]
    assert testrow['FREQ'] == 982.301
    assert testrow["QN'1"] == 4
    assert testrow["QN'2"] == -2
    assert testrow["QN'3"] == ''
    assert testrow["QN'4"] == 2

    assert testrow['QN"1'] == 5
    assert testrow['QN"2'] == -5
    assert testrow['QN"3'] == ''
    assert testrow['QN"4'] == 2

    testrow = tbl[6]
    assert testrow['FREQ'] == 991.369
    assert testrow["QN'1"] == 18
    assert testrow["QN'2"] == 3
    assert testrow["QN'3"] == '-'
    assert testrow["QN'4"] == 0

    assert testrow['QN"1'] == 18
    assert testrow['QN"2'] == 3
    assert testrow['QN"3'] == '+'
    assert testrow['QN"4'] == 0


@pytest.mark.bigdata
@pytest.mark.remote_data
class TestRegressionAllMolecules:
    """Test that we can get each molecule in JPL database"""
    species_table = JPLSpec.get_species_table()

    @pytest.mark.parametrize('row', species_table)
    def test_regression_all_molecules(self, row):
        """
        Expensive test - try all the molecules
        """
        mol_id = row['TAG']
        # O2 has masked QNs making it hard to test automatically (32...)
        # 34001, 39003, 44004, 44009, 44012 are missing or corrupt molecules
        # 81001 may be fine? not entirely sure what's wrong
        if mol_id in (32001, 32002, 32005,
                      34001, 39003, 44004, 44009, 44012,
                      81001):
            # N2O = 44009 is just not there
            pytest.skip("Skipping O2 due to masked QNs")
        tbl = JPLSpec.get_molecule(mol_id)
        assert isinstance(tbl, Table)
        assert len(tbl) > 0
