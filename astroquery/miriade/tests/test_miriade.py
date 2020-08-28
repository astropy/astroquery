# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import pytest

from numpy import isclose

from ... import miriade
from ...utils.testing_tools import MockResponse

# files in data/ for different queries
DATA_FILES = {'a:ceres': 'ceres_ephemerides.txt',
              'c:p/halley': 'halley_ephemerides.txt'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, request_type, url, **kwargs):
    with open(data_path(DATA_FILES[kwargs['params']['-name']]),
              'rb') as f:
        response = MockResponse(content=f.read(), url=url)

    return response


# use a pytest fixture to create a dummy requests function,
@pytest.fixture
def patch_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(miriade.core.MiriadeClass, '_request',
               nonremote_request)
    return mp


# test functions

def test_ephemerides_query_ceres(patch_request):
    # check values of Ceres for a given epoch
    res = miriade.Miriade.ephemerides(name='a:ceres', observer='500',
                                      ep=2451544.5)

    assert res['datetime_str'][0] == '2000-01-01T00:00:00.00'
    assert isclose(res['r'][0], 2.263149914)
    assert isclose(res['r_dot'][0], -21.93905)


def test_ephemerides_query_halley(patch_request):
    # check values of Halley for a given epoch
    res = miriade.Miriade.ephemerides(name='c:p/halley', observer='500',
                                      ep=2451544.5)

    assert res['datetime_str'][0] == '2000-01-01T00:00:00.00'
    assert isclose(res['r'][0], 24.700179227)
    assert isclose(res['r_dot'][0], -13.13934)
