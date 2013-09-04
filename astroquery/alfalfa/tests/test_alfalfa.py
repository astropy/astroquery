# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import alfalfa
from astropy import coordinates
import astropy.utils.data as aud
from astropy.tests.helper import pytest
import requests
from contextlib import contextmanager
import os

DATA_FILES = {'catalog':'alfalfa_cat_small.txt',
              'spectrum':'alfalfa_sp.fits'}

class MockResponse(object):

    def __init__(self, content):
        self.content = content

    def iter_lines(self):
        for l in self.content.split("\n"):
            yield l

    def close(self):
        pass

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp

@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectrum']) # TODO: add images option
        yield file_obj
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(aud, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp

def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES['catalog'])
    content = open(filename, 'r').read()
    return MockResponse(content)

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

# Test Case: A Seyfert 1 galaxy
coords = coordinates.ICRSCoordinates('0h8m05.63s +14d50m23.3s')

ALFALFA = alfalfa.core.ALFALFA()

def test_alfalfa_catalog(patch_get, patch_get_readable_fileobj, coords=coords):
    cat = ALFALFA.get_catalog()
    assert len(cat) > 0

def test_alfalfa_crossID(patch_get, patch_get_readable_fileobj, coords=coords):
    agc = ALFALFA.query_region(coords, optical_counterpart=True)
    assert agc == 100051

def test_alfalfa_spectrum(patch_get, patch_get_readable_fileobj, coords=coords):
    agc = ALFALFA.query_region(coords, optical_counterpart=True)
    sp = ALFALFA.get_spectrum(agc)
    assert len(sp) == 3

