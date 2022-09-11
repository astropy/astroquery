import os
import requests
import pytest
from ... import nasa_ads
from astroquery.utils.mocks import MockResponse


class MockResponseADS(MockResponse):
    """
    Fixing the init issues
    """

    def __init__(self, content=None, url=None, headers={},
                 content_type=None, stream=False, auth=None, status_code=200,
                 verify=True):
        self.content = content
        self.raw = content
        self.headers = headers
        if content_type is not None:
            self.headers.update({'Content-Type': content_type})
        self.url = url
        self.auth = auth
        self.status_code = status_code


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests, 'get', get_mockreturn)
    mp.setattr(nasa_ads.ADS, '_request', get_mockreturn)
    return mp


def get_mockreturn(method='GET', url=None, headers=None, timeout=10,
                   **kwargs):
    filename = data_path('test_text.txt')
    with open(filename, 'r') as infile:
        content = infile.read()

    return MockResponseADS(content=content)


def test_url():
    url = nasa_ads.ADS.query_simple(
        "^Persson Origin of water around deeply embedded low-mass protostars", get_query_payload=True)

    assert url == ('https://api.adsabs.harvard.edu/v1/search/query?'
                   'q=%5EPersson%20Origin%20of%20water%20around%20deeply%20embedded%20low-mass%20protostars'
                   '&fl=bibcode,title,author,aff,pub,volume,pubdate,page,citation,citation_count,abstract,doi,eid'
                   '&sort=date%20desc'
                   '&rows=10&start=0')


def test_simple(patch_get):
    testADS = nasa_ads.ADS
    testADS.TOKEN = 'test-token'
    x = testADS.query_simple(
        "^Persson Origin of water around deeply embedded low-mass protostars")
    assert x['author'][0][0] == 'Persson, M. V.'

    assert 'citation' in x.columns
    assert 'citation_count' in x.columns
