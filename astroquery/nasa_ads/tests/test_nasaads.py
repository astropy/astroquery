import os
import requests
import pytest
from ... import nasa_ads
from ...utils.testing_tools import MockResponse


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


def get_mockreturn(url, params=None, timeout=10):
    filename = data_path('test_text.txt')
    content = open(filename, 'r').read()
    return MockResponse(content)


def test_url():
    url = nasa_ads.ADS.query_simple(
        "^Persson Origin of water around deeply embedded low-mass protostars", get_query_payload=True)
    assert url == 'https://api.adsabs.harvard.edu/v1/search/query?' + \
                  'q=%5EPersson%20Origin%20of%20water%20around%20deeply%20embedded%20low-mass%20protostars' + \
                  '&fl=bibcode,title,author,aff,pub,volume,pubdate,page,citations,abstract,doi,eid&rows=10&start=0'


def test_simple(patch_get):
    testADS = nasa_ads.ADS
    testADS.TOKEN = 'test_token'
    x = testADS.query_simple(
        "^Persson Origin of water around deeply embedded low-mass protostars")
    assert x['author'][0][0] == 'Persson, M. V.'
