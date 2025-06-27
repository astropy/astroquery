# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test astroquery.noirlab, but monkeypatch any HTTP requests.
"""
# External packages
import pytest
# from astropy import units as u
# from astropy.coordinates import SkyCoord
# Local packages
from ...utils.mocks import MockResponse
from .. import NOIRLab  #, NOIRLabClass
from . import expected as exp


@pytest.fixture
def patch_request(request):
    def mockreturn(method, url, **kwargs):
        if '/version/' in url:
            content = exp.version.encode('utf-8')
        elif '/get_token/' in url:
            content = f'"{exp.get_token}"'.encode('utf-8')
        return MockResponse(content=content, url=url)

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(NOIRLab, '_request', mockreturn)
    return mp


def test_version(patch_request):
    r = NOIRLab.version()
    assert r >= float(exp.version)


def test_get_token(patch_request):
    actual = NOIRLab.get_token('nobody@university.edu', '123456')
    assert actual == exp.get_token
