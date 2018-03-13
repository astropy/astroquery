# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import re

import pytest

from ... import mpc
from ...utils.testing_tools import MockResponse
from ...utils import commons
from ...exceptions import TableParseError


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
    request_payload = mpc.core.MPC.query_object_async(name='ceres', get_query_payload=True)
    assert request_payload == {"name": "ceres", "json": 1, "limit": 1}


def test_args_to_payload():
    test_args = mpc.core.MPC._args_to_payload(name="eros", number=433)
    assert test_args == {"name": "eros", "number": 433, "json": 1}
