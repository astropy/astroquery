# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import splatalogue
from astropy import units as u
from astropy.tests.helper import pytest
import requests
import os

SPLAT_DATA = 'CO_colons.csv'

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

class MockResponse(object):
    def __init__(self, content):
        self.content = content

def post_mockreturn(url, data=None, timeout=10):
    filename = data_path(SPLAT_DATA)
    content = open(filename, "r").read()
    return MockResponse(content)

def test_simple():
    x = splatalogue.Splatalogue.query_species(114*u.GHz,116*u.GHz,chemical_name=' CO ')
