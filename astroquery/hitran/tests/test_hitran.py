# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import numpy as np

from astropy import units as u
from astropy.table import Table

from ...hitran import Hitran, parse_hitran_text

HITRAN_DATA = 'H2O.data'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class MockResponseHitran:
    def __init__(self):
        self.filename = data_path(HITRAN_DATA)

    @property
    def text(self):
        with open(self.filename) as fh:
            return fh.read()


def test_query_async():
    response = Hitran.query_lines_async(molecule_number=1,
                                        isotopologue_number=1,
                                        min_frequency=0. / u.cm,
                                        max_frequency=10. / u.cm,
                                        get_query_payload=True)
    assert response['iso_ids_list'] == '1'
    np.testing.assert_almost_equal(response['numin'], 0.)
    np.testing.assert_almost_equal(response['numax'], 10.)


EXPECTED_KEYS = {'molec_id', 'local_iso_id', 'nu', 'sw', 'a',
                 'gamma_air', 'gamma_self', 'elower',
                 'n_air', 'delta_air', 'global_upper_quanta',
                 'global_lower_quanta', 'local_upper_quanta',
                 'local_lower_quanta', 'ierr1', 'ierr2',
                 'ierr3', 'ierr4', 'ierr5', 'ierr6', 'iref1',
                 'iref2', 'iref3', 'iref4', 'iref5', 'iref6',
                 'line_mixing_flag', 'gp', 'gpp'}


def test_query():
    hitran = Hitran()
    response = MockResponseHitran()
    tbl = hitran._parse_result(response)
    assert isinstance(tbl, Table)
    assert len(tbl) == 122
    assert set(tbl.keys()) == EXPECTED_KEYS
    assert tbl['molec_id'][0] == 1
    np.testing.assert_almost_equal(tbl['nu'][0], 0.072059)


def test_parse_hitran_text():
    with open(data_path(HITRAN_DATA)) as fh:
        text = fh.read()
    tbl = parse_hitran_text(text)
    assert isinstance(tbl, Table)
    assert len(tbl) == 122
    assert set(tbl.keys()) == EXPECTED_KEYS
    assert tbl['molec_id'][0] == 1
    np.testing.assert_almost_equal(tbl['nu'][0], 0.072059)


def test_parse_hitran_text_matches_parse_result():
    """parse_hitran_text and _parse_result must produce identical tables."""
    response = MockResponseHitran()
    tbl_from_response = Hitran._parse_result(response)
    tbl_from_text = parse_hitran_text(response.text)
    assert len(tbl_from_response) == len(tbl_from_text)
    assert tbl_from_response.keys() == tbl_from_text.keys()
    for key in tbl_from_response.keys():
        np.testing.assert_array_equal(tbl_from_response[key],
                                      tbl_from_text[key])


def test_read_par_file():
    tbl = Hitran.read(data_path(HITRAN_DATA))
    assert isinstance(tbl, Table)
    assert len(tbl) == 122
    assert set(tbl.keys()) == EXPECTED_KEYS
    assert tbl['molec_id'][0] == 1
    np.testing.assert_almost_equal(tbl['nu'][0], 0.072059)
