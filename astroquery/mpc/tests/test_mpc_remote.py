# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import re
import pytest
import requests

from astropy.tests.helper import remote_data
from ... import mpc

@remote_data
class TestMPC(object):

    def read_data_file(self, filename):
        query_args = dict()
        with open(os.path.join(os.getcwd(), 'tests/data', filename), 'r') as data:
            for line in data:
                curr_line = line.split(',')
                query_args[curr_line[0]] = curr_line[1]
        return query_args

    def test_query_object_valid_object_by_name_json_response(self):
        response = mpc.core.MPC.query_object_async(name="ceres", json=1)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert response.json()[0]['name'].lower() == 'ceres'

    def test_quest_object_valid_object_by_name_xml_response(self):
        response = mpc.core.MPC.query_object_async(name="ceres", json=0)
        assert response.status_code == requests.codes.ok

    def test_query_object_by_nonexistent_name(self):
        response = mpc.core.MPC.query_object_async(name="invalid object", json=1)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 0

    #queries by all parameters save for designation
    def test_query_object_valid_object_all_parameters(self):
        query_args = self.read_data_file('complete_query_by_name.data')
        response = mpc.core.MPC.query_object_async(query_args)