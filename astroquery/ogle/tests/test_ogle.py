# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import ogle

import os
import requests
from astropy.tests.helper import pytest
from astropy import coordinates as coord
from astropy import units as u

DATA_FILES = {'gal_0_3':'gal_0_3.txt',
              }

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

def post_mockreturn(url, data, timeout, files=None):
    if files is not None:
        response = MockResponse(open(data_path(DATA_FILES['gal_0_3']),'r').read())
    else:
        raise ValueError("Unsupported post request.")
    return response


class MockResponse(object):

    def __init__(self, content):
        self.content = self.text = content

    def raise_for_status(self):
        pass


def test_ogle_single(patch_post):
    """
    Test a single pointing using an astropy coordinate instance
    """
    co = coord.GalacticCoordinates(0, 3, unit=(u.degree, u.degree))
    ogle.core.Ogle.query_region(coord=co)


def test_ogle_list(patch_post):
    """
    Test multiple pointings using a list of astropy coordinate instances
    """
    co = coord.GalacticCoordinates(0, 3, unit=(u.degree, u.degree))
    co_list = [co, co, co]
    ogle.core.Ogle.query_region(coord=co_list)


def test_ogle_list_values(patch_post):
    """
    Test multiple pointings using a nested-list of decimal degree Galactic
    coordinates
    """
    co_list = [[0, 0, 0], [3, 3, 3]]
    ogle.core.Ogle.query_region(coord=co_list)
