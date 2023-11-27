# Licensed under a 3-clause BSD style license - see LICENSE.rst
from contextlib import contextmanager
import os
import requests
from astropy import coordinates
import pytest
from ...utils import commons
from astroquery.utils.mocks import MockResponse
from ... import alfalfa

DATA_FILES = {'catalog': 'alfalfa_cat_small.txt',
              'spectrum': 'alfalfa_sp.fits'}


class MockResponseAlfalfa(MockResponse):

    def __init__(self, content, **kwargs):
        super().__init__(content, **kwargs)

    def iter_lines(self):
        for line in self.text.split("\n"):
            yield line

    def close(self):
        pass


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests, 'get', get_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectrum'])  # TODO: add images option
        # read as bytes, assuming FITS
        with open(file_obj, 'rb') as inputfile:
            yield inputfile

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES['catalog'])
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponseAlfalfa(content)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# Test Case: A Seyfert 1 galaxy
coords = coordinates.SkyCoord('0h8m05.63s +14d50m23.3s')
coordsOC = coordinates.SkyCoord(0.59583, 27.21056, unit='deg')

ALFALFA = alfalfa.core.Alfalfa()


def test_alfalfa_catalog(patch_get, patch_get_readable_fileobj, coords=coords):
    cat = ALFALFA.get_catalog()
    assert len(cat) > 0


def test_alfalfa_crossID(patch_get, patch_get_readable_fileobj, coords=coords):
    agc = ALFALFA.query_region(coords, optical_counterpart=True)
    assert agc == 100051
    agc = ALFALFA.query_region(coordsOC, optical_counterpart=False)
    assert agc == 12920
    agc = ALFALFA.query_region(coordsOC, optical_counterpart=False, radius='0 arcmin')
    assert agc is None
