import os

import pytest
import requests

from astroquery.utils.mocks import MockResponse


SPLAT_DATA = 'CO.json'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests.Session, 'request', post_mockreturn)
    return mp


def post_mockreturn(self, method, url, data=None, timeout=10, files=None,
                    params=None, headers=None, **kwargs):
    if method != 'POST':
        raise ValueError("A 'post request' was made with method != POST")
    filename = data_path(SPLAT_DATA)
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)
