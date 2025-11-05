import numpy as np
import pytest

from unittest.mock import Mock, MagicMock, patch
from astroquery.exceptions import EmptyResponseError

import os

from astropy import units as u
from astropy.table import Table
from astroquery.linelists.jplspec.core import JPLSpec

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


def test_parse_cat():
    """Test parsing of catalog files with _parse_cat method."""

    response = MockResponseSpec('H2O_sample.cat')
    tbl = JPLSpec._parse_cat(response)

    # Check table structure
    assert isinstance(tbl, Table)
    assert len(tbl) > 0
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
                                   'TAG', 'QNFMT', 'Lab',
                                   'QN"1', 'QN"2', 'QN"3', 'QN"4',
                                   "QN'1", "QN'2", "QN'3", "QN'4"
                                   ])

    # Check units
    assert tbl['FREQ'].unit == u.MHz
    assert tbl['ERR'].unit == u.MHz
    assert tbl['LGINT'].unit == u.nm**2 * u.MHz
    assert tbl['ELO'].unit == u.cm**(-1)

    # Check Lab flag exists and is boolean
    assert 'Lab' in tbl.colnames
    assert tbl['Lab'].dtype == bool

    # Check TAG values are positive (absolute values)
    assert all(tbl['TAG'] > 0)


def test_get_molecule_input_validation():
    """Test input validation for get_molecule method."""

    # Test invalid string format
    with pytest.raises(ValueError):
        JPLSpec.get_molecule('invalid')

    # Test invalid type
    with pytest.raises(ValueError):
        JPLSpec.get_molecule(12.34)

    # Test wrong length string
    with pytest.raises(ValueError):
        JPLSpec.get_molecule(1234567)


# Helper functions for fallback tests
def _create_empty_response(molecules):
    """Create a mock response with 'Zero lines were found'."""
    mock_response = Mock()
    mock_response.text = "Zero lines were found"
    mock_request = Mock()
    if isinstance(molecules, str):
        mock_request.body = f"Mol={molecules}"
    else:
        mock_request.body = "&".join(f"Mol={mol}" for mol in molecules)
    mock_response.request = mock_request
    return mock_response


def _setup_fallback_mocks(molecules_dict):
    """
    Set up mocks for fallback testing.

    Parameters
    ----------
    molecules_dict : dict
        Dictionary mapping molecule IDs to (name, table_data) tuples.
        table_data should be a dict with 'FREQ' and optionally other columns.

    Returns
    -------
    mock_get_molecule, mock_build_lookup
        The mock objects that can be used in assertions.
    """
    # Mock build_lookup
    mock_lookup = MagicMock()
    if len(molecules_dict) == 1:
        mol_id = list(molecules_dict.keys())[0]
        mock_lookup.find.return_value = molecules_dict[mol_id][0]
    else:
        mock_lookup.find.side_effect = lambda mol_id, **kwargs: molecules_dict.get(mol_id, (None, None))[0]

    # Mock get_molecule
    def get_molecule_side_effect(mol_id):
        if mol_id not in molecules_dict:
            raise ValueError(f"Unexpected molecule ID: {mol_id}")
        name, table_data = molecules_dict[mol_id]
        mock_table = Table()
        mock_table['FREQ'] = table_data.get('FREQ', [100.0, 200.0])
        mock_table['TAG'] = [int(mol_id)] * len(mock_table['FREQ'])
        # Add any additional columns from table_data
        for key, value in table_data.items():
            if key != 'FREQ' and key not in mock_table.colnames:
                mock_table[key] = value
        mock_table.meta = table_data.get('meta', {})
        return mock_table

    return get_molecule_side_effect, mock_lookup


def test_fallback_to_getmolecule_with_empty_response():
    """Test that fallback_to_getmolecule works when query returns zero lines."""
    mock_response = _create_empty_response('18003')

    # Test with fallback disabled - should raise EmptyResponseError
    with pytest.raises(EmptyResponseError, match="Response was empty"):
        JPLSpec._parse_result(mock_response, fallback_to_getmolecule=False)

    # Test with fallback enabled - should call get_molecule
    molecules = {'18003': ('H2O', {'FREQ': [100.0, 200.0]})}

    with patch.object(JPLSpec, 'get_molecule') as mock_get_molecule, \
         patch('astroquery.linelists.jplspec.core.build_lookup') as mock_build_lookup:

        get_mol_func, mock_lookup = _setup_fallback_mocks(molecules)
        mock_get_molecule.side_effect = get_mol_func
        mock_build_lookup.return_value = mock_lookup

        result = JPLSpec._parse_result(mock_response, fallback_to_getmolecule=True)

        mock_get_molecule.assert_called_once_with('18003')
        assert isinstance(result, Table)
        assert len(result) == 2
        assert result.meta['molecule_id'] == '18003'
        assert result.meta['molecule_name'] == 'H2O'


def test_fallback_to_getmolecule_with_multiple_molecules():
    """Test fallback with multiple molecules in the request."""
    mock_response = _create_empty_response(['18003', '28001'])

    molecules = {
        '18003': ('H2O', {'FREQ': [100.0, 200.0]}),
        '28001': ('CO', {'FREQ': [300.0, 400.0]})
    }

    with patch.object(JPLSpec, 'get_molecule') as mock_get_molecule, \
         patch('astroquery.linelists.jplspec.core.build_lookup') as mock_build_lookup:

        get_mol_func, mock_lookup = _setup_fallback_mocks(molecules)
        mock_get_molecule.side_effect = get_mol_func
        mock_build_lookup.return_value = mock_lookup

        result = JPLSpec._parse_result(mock_response, fallback_to_getmolecule=True)

        assert mock_get_molecule.call_count == 2
        assert isinstance(result, Table)
        assert len(result) == 4  # 2 rows from each molecule
        assert 'molecule_list' in result.meta
        assert 'Name' in result.colnames


def test_query_lines_with_fallback():
    """Test that query_lines uses fallback when server returns empty result."""

    # Test with fallback disabled - should raise EmptyResponseError
    with patch.object(JPLSpec, '_request') as mock_request:
        mock_response = _create_empty_response('28001')
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        with pytest.raises(EmptyResponseError, match="Response was empty"):
            JPLSpec.query_lines(min_frequency=100 * u.GHz,
                                max_frequency=200 * u.GHz,
                                min_strength=-500,
                                molecule="28001 CO",
                                fallback_to_getmolecule=False)

    # Test with fallback enabled - should call get_molecule
    molecules = {'28001': ('CO', {
        'FREQ': [115271.2018, 230538.0000],
        'ERR': [0.0005, 0.0010],
        'LGINT': [-5.0105, -4.5],
        'DR': [2, 2],
        'ELO': [0.0, 3.845],
        'GUP': [3, 5],
        'QNFMT': [1, 1]
    })}

    with patch.object(JPLSpec, '_request') as mock_request, \
         patch.object(JPLSpec, 'get_molecule') as mock_get_molecule, \
         patch('astroquery.linelists.jplspec.core.build_lookup') as mock_build_lookup:

        mock_response = _create_empty_response('28001')
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        get_mol_func, mock_lookup = _setup_fallback_mocks(molecules)
        mock_get_molecule.side_effect = get_mol_func
        mock_build_lookup.return_value = mock_lookup

        result = JPLSpec.query_lines(
            min_frequency=100 * u.GHz,
            max_frequency=200 * u.GHz,
            min_strength=-500,
            molecule="28001 CO",
            fallback_to_getmolecule=True)

        mock_get_molecule.assert_called_once_with('28001')
        assert isinstance(result, Table)
        assert len(result) > 0
        assert 'molecule_id' in result.meta
