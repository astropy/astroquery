# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import ogle

import os
import requests
from astropy.tests.helper import pytest
from astropy import coordinates as coord
from astropy import units as u

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp

DATA_FILES = None

def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES)
    content = open(filename, 'r').read()
    return MockResponse(content)

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

data = None

def post_mockreturn(url, data, timeout):
    response = MockResponse(data)
    return response


class MockResponse(object):
    def __init__(self, content):
        self.content = content

def test_ogle_single(patch_get):
    """
    Test a single pointing using an astropy coordinate instance
    """
    co = coord.GalacticCoordinates(0, 3, unit=(u.degree, u.degree))
    ogle.query(coord=co)

def test_ogle_list(patch_get):
    """
    Test multiple pointings using a list of astropy coordinate instances
    """
    co = coord.GalacticCoordinates(0, 3, unit=(u.degree, u.degree))
    co_list = [co, co, co]
    ogle.query(coord=co_list)

def test_ogle_list_values(patch_get):
    """
    Test multiple pointings using a list of astropy coordinate instances
    """
    co_list = [[0, 0, 0], [3, 3, 3]]
    ogle.query(coord=co_list)
