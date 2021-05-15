# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import numpy as np

from astropy import units as u
from astropy.table import Table

from ...hitran import Hitran

HITRAN_DATA = 'H2O.data'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class MockResponseHitran:
    def __init__(self):
        self.filename = data_path(HITRAN_DATA)

    @property
    def text(self):
        with open(self.filename) as f:
            return f.read()


def test_query_async():
    response = Hitran.query_lines_async(molecule_number=1,
                                        isotopologue_number=1,
                                        min_frequency=0. / u.cm,
                                        max_frequency=10. / u.cm,
                                        get_query_payload=True)
    assert response['iso_ids_list'] == '1'
    np.testing.assert_almost_equal(response['numin'], 0.)
    np.testing.assert_almost_equal(response['numax'], 10.)


def test_query():
    hitran = Hitran()
    response = MockResponseHitran()
    tbl = hitran._parse_result(response)
    assert isinstance(tbl, Table)
    assert len(tbl) == 122
    assert set(tbl.keys()) == set(['molec_id', 'local_iso_id', 'nu', 'sw', 'a',
                                   'gamma_air', 'gamma_self', 'elower',
                                   'n_air', 'delta_air', 'global_upper_quanta',
                                   'global_lower_quanta', 'local_upper_quanta',
                                   'local_lower_quanta', 'ierr1', 'ierr2',
                                   'ierr3', 'ierr4', 'ierr5', 'ierr6', 'iref1',
                                   'iref2', 'iref3', 'iref4', 'iref5', 'iref6',
                                   'line_mixing_flag', 'gp', 'gpp'])
    assert tbl['molec_id'][0] == 1
    np.testing.assert_almost_equal(tbl['nu'][0], 0.072059)
