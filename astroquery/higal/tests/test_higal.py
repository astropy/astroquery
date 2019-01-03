# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest

import os
import requests

from numpy import testing as npt
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u

from ...utils.testing_tools import MockResponse

from ... import higal
from ...higal import conf

DATA_FILES = {'POST':
              {'https://tools.ssdc.asi.it/HiGALSearch.jsp':
               'g49.html'},
              'GET':
              {'https://tools.ssdc.asi.it/MMCAjaxFunction':
               'g49.html',
               'https://tools.ssdc.asi.it/HiGALSearch.jsp':
               'frontpage.html',
              }
             }


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# define a monkeypatch replacement request function that returns the
# dummy HTTP response for the dummy 'get' function, by
# reading in data from some data file:
def nonremote_request(self, request_type, url, **kwargs):
    # kwargs are ignored in this case, but they don't have to be
    # (you could use them to define which data file to read)
    with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(higal.core.HiGalClass, '_request',
               nonremote_request)
    return mp

class FakeCookieJar(list):
    def values(self):
        return self

    def clear(self, arg1, arg2, arg3, **kwargs):
        return

class FakeCookie(object):
    def __init__(self):
        self.name = "JSESSIONID"
        self.path = '/cas/'
        self.domain = ""


def test_query_region(patch_request):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic', unit=(u.deg, u.deg))
    hg = higal.core.HiGalClass()
    hg._session.cookies = FakeCookieJar([FakeCookie()]*2)

    result = hg.query_region(coordinates=target, radius=0.25*u.deg, catalog_query=True)
    assert isinstance(result, Table)

    result = hg.query_region(coordinates=target, radius=0.25*u.deg, catalog_query=False)
    assert isinstance(result, Table)

# these tests are challenging to do locally; we'll rely on the remote ones for
# now =(
# def test_get_images(patch_request):
#     target = coord.SkyCoord(49.5, -0.3, frame='galactic', unit=(u.deg, u.deg))
#     result = higal.core.HiGalClass().get_images(coordinates=target,
#                                                 radius=0.25*u.deg)
#     assert isinstance(result, Table)
