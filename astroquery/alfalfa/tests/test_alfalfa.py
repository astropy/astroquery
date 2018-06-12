# Licensed under a 3-clause BSD style license - see LICENSE.rst
from contextlib import contextmanager
import os
import requests
from astropy import coordinates
import pytest
from ...utils import commons
from ...utils.testing_tools import MockResponse
from ... import alfalfa

DATA_FILES = {'catalog': 'alfalfa_cat_small.txt',
              'spectrum': 'alfalfa_sp.fits'}


class MockResponseAlfalfa(MockResponse):

    def __init__(self, content, **kwargs):
        super(MockResponseAlfalfa, self).__init__(content, **kwargs)

    def iter_lines(self):
        for l in self.text.split("\n"):
            yield l

    def close(self):
        pass


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectrum'])  # TODO: add images option
        yield open(file_obj, 'rb')  # read as bytes, assuming FITS
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES['catalog'])
    content = open(filename, 'rb').read()
    return MockResponseAlfalfa(content)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# Test Case: A Seyfert 1 galaxy
coords = coordinates.SkyCoord('0h8m05.63s +14d50m23.3s')

ALFALFA = alfalfa.core.Alfalfa()


def test_alfalfa_catalog(patch_get, patch_get_readable_fileobj, coords=coords):
    cat = ALFALFA.get_catalog()
    assert len(cat) > 0


def test_alfalfa_crossID(patch_get, patch_get_readable_fileobj, coords=coords):
    agc = ALFALFA.query_region(coords, optical_counterpart=True)
    assert agc == 100051


def test_alfalfa_spectrum(patch_get, patch_get_readable_fileobj,
                          coords=coords):
    agc = ALFALFA.query_region(coords, optical_counterpart=True)
    sp = ALFALFA.get_spectrum(agc)
    assert len(sp) == 3
