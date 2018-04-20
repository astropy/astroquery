# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from ... import mpc
from ...utils.testing_tools import MockResponse
from ...utils import commons


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(mpc.MPCClass, '_request', post_mockreturn)
    return mp


def post_mockreturn(self, httpverb, url, params, auth):
    return MockResponse()


def test_query_object_get_query_payload(patch_post):
    request_payload = mpc.core.MPC.query_object_async(get_query_payload=True, target_type='asteroid', name='ceres')
    assert request_payload == {"name": "ceres", "json": 1, "limit": 1}


def test_args_to_payload():
    test_args = mpc.core.MPC._args_to_payload(name="eros", number=433)
    assert test_args == {"name": "eros", "number": 433, "json": 1}


@pytest.mark.parametrize('type, url', [
    ('comet',
        'http://minorplanetcenter.net/web_service/search_comet_orbits'),
    ('asteroid',
        'http://minorplanetcenter.net/web_service/search_orbits')])
def test_get_mpc_endpoint(type, url):
    query_url = mpc.core.MPC.get_mpc_endpoint(target_type=type)
    assert query_url == url
