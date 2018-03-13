# Licensed under a 3-clause BSD style license - see LICENSE.rst
import requests

from astropy.tests.helper import remote_data
from ... import mpc


@remote_data
class TestMPC(object):

    def test_query_object_valid_object_by_name(self):
        response = mpc.core.MPC.query_object_async(name="ceres", get_query_payload=False)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert response.json()[0]['name'].lower() == 'ceres'

    def test_query_multiple_objects(self):
        response = mpc.core.MPC.query_objects_async(epoch_jd=2458200.5, limit=5)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 5

    def test_query_object_by_nonexistent_name(self):
        response = mpc.core.MPC.query_object_async(name="invalid object")
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 0

    def test_query_object_invalid_parameter(self):
        response = mpc.core.MPC.query_object_async(blah="blah")
        assert response.status_code == requests.codes.ok
        assert "Unrecognized parameter" in str(response.content)
