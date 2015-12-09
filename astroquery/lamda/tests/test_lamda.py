# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
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
