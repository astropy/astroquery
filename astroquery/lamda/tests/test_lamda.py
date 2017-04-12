# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
import numpy as np
from ...lamda import core

DATA_FILES = {'co': 'co.txt'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_parser():
    collrates, radtransitions, enlevels = core.parse_lamda_datafile(
        data_path('co.txt'))

    assert set(collrates.keys()) == set(['PH2', 'OH2'])
    assert len(enlevels) == 41
    assert len(radtransitions) == 40


def test_writer():
    tables = core.parse_lamda_datafile(data_path('co.txt'))
    coll, radtrans, enlevels = tables

    tmpfd, tmpname = tempfile.mkstemp()
    core.write_lamda_datafile(tmpname, tables)

    coll2, radtrans2, enlevels2 = core.parse_lamda_datafile(tmpname)

    np.testing.assert_almost_equal(enlevels['Energy'], enlevels2['Energy'])
    np.testing.assert_almost_equal(radtrans['EinsteinA'],
                                   radtrans2['EinsteinA'])
    np.testing.assert_almost_equal(radtrans['Frequency'],
                                   radtrans2['Frequency'])
    for k in coll:
        np.testing.assert_almost_equal(coll[k]['C_ij(T=5)'],
                                       coll2[k]['C_ij(T=5)'])
