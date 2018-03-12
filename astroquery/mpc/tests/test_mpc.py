# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import re

import pytest

from ... import mpc
from ...utils.testing_tools import MockResponse
from ...utils import commons
from ...exceptions import TableParseError

class MockResponseMPC(MockResponse):

    def __init__(self, **kwargs):
        super(MockResponseMPC, self).__init__(**kwargs)

def read_data_file(filename):
    query_args = dict()
    with open(os.path.join(os.getcwd(), 'tests/data', filename), 'r') as data:
        for line in data:
            curr_line = line.split(',')
            query_args[curr_line[0]] = curr_line[1]
    return query_args

def test_query_object_get_query_payload():
    request_payload = mpc.core.MPC.query_object_async(name='ceres', get_query_payload=True)
    assert request_payload == {"name": "ceres", "json": 1, "limit": 1}

def test_args_to_payload():
    test_args = mpc.core.MPC._args_to_payload(name="eros", number=433)
    assert test_args == {"name": "eros", "number": 433, "json": 1}