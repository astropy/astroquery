# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import re

import pytest
from unittest.mock import patch

from ... import mpc
from ...utils.testing_tools import MockResponse
from ...utils import commons
from ...exceptions import TableParseError


class MockResponseMPC(MockResponse):

    def __init__(self, **kwargs):
        super(MockResponseMPC, self).__init__(**kwargs)


def test_query_object_get_query_payload():
    with patch('astroquery.query.BaseQuery._request') as base_query_mock:
        # This test shouldn't make a remote call, but patching the BaseQuery class is done to ensure that a remote call isn't made for any reason
        base_query_mock.return_value = MockResponseMPC()
        request_payload = mpc.core.MPC.query_object_async(name='ceres', get_query_payload=True)
        assert request_payload == {"name": "ceres", "json": 1, "limit": 1}


def test_args_to_payload():
    test_args = mpc.core.MPC._args_to_payload(name="eros", number=433)
    assert test_args == {"name": "eros", "number": 433, "json": 1}
