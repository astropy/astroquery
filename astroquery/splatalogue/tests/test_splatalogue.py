# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import splatalogue
from ...utils.testing_tools import MockResponse
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


def post_mockreturn(url, data=None, timeout=10, **kwargs):
    filename = data_path(SPLAT_DATA)
    content = open(filename, "r").read()
    return MockResponse(content, **kwargs)


def test_simple(patch_post):
    x = splatalogue.Splatalogue.query_lines(114*u.GHz,116*u.GHz,chemical_name=' CO ')


def test_init(patch_post):
    x = splatalogue.Splatalogue.query_lines(114*u.GHz,116*u.GHz,chemical_name=' CO ')
    S = splatalogue.Splatalogue(chemical_name=' CO ')
    y = S.query_lines(114*u.GHz,116*u.GHz)
    # it is not currently possible to test equality between tables:
    # masked arrays fail
    # assert y == x
    assert len(x) == len(y)
    assert all(y['Species'] == x['Species'])
    assert all(x['Chemical Name']==y['Chemical Name'])
