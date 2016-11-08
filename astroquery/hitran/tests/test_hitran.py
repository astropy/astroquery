# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from ...hitran import read_hitran_file

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

def test_parser():
    tbl = read_hitran_file(data_path('H2O.data'))

    assert len(tbl) == 122
    assert set(tbl.keys()) == set(['molec_id', 'local_iso_id', 'nu', 'sw', 'a',
                                   'gamma_air', 'gamma_self', 'elower', 'n_air',
                                   'delta_air', 'global_upper_quanta',
                                   'global_lower_quanta', 'local_upper_quanta',
                                   'local_lower_quanta', 'ierr1', 'ierr2',
                                   'ierr3', 'ierr4', 'ierr5', 'ierr6', 'iref1',
                                   'iref2', 'iref3', 'iref4', 'iref5', 'iref6',
                                   'line_mixing_flag', 'gp', 'gpp'])
    assert tbl['molec_id'][0] == 1
