# Licensed under a 3-clause BSD style license - see LICENSE.rst
import requests
import pytest

from astropy.tests.helper import remote_data
from ...exceptions import InvalidQueryError
from ... import mpc


@remote_data
class TestMPC(object):

    @pytest.mark.parametrize('type, name', [
        ('asteroid', 'ceres'),
        ('asteroid', 'eros'),
        ('asteroid', 'pallas')])
    def test_query_object_valid_object_by_name(self, type, name):
        response = mpc.core.MPC.query_object_async(target_type=type, name=name)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert response.json()[0]['name'].lower() == name

    @pytest.mark.parametrize('type, number', [
        ('comet', '103P')])
    def test_query_object_valid_object_by_number(self, type, number):
        response = mpc.core.MPC.query_object_async(
            target_type=type, number=number)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert str(response.json()[0]['number']) + \
            response.json()[0]['object_type'] == number

    @pytest.mark.parametrize('type, designation', [
        ('comet', 'C/2012 S1')])
    def test_query_object_valid_object_by_designation(self, type, designation):
        response = mpc.core.MPC.query_object_async(
            target_type=type, designation=designation)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert response.json()[0]['designation'].lower() == designation.lower()

    @pytest.mark.parametrize('name', [
        ('ceres'),
        ('eros'),
        ('pallas')])
    def test_query_object_get_query_payload_remote(self, name):
        request_payload = mpc.core.MPC.query_object_async(
            get_query_payload=True, target_type='asteroid', name=name)
        assert request_payload == {"name": name, "json": 1, "limit": 1}

    def test_query_multiple_objects(self):
        response = mpc.core.MPC.query_objects_async(
            target_type='asteroid', epoch_jd=2458200.5, limit=5)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 5

    def test_query_object_by_nonexistent_name(self):
        response = mpc.core.MPC.query_object_async(
            target_type='asteroid', name="invalid object")
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 0

    def test_query_object_invalid_parameter(self):
        response = mpc.core.MPC.query_object_async(
            target_type='asteroid', blah="blah")
        assert response.status_code == requests.codes.ok
        assert "Unrecognized parameter" in str(response.content)

    def test_get_observatory_codes(self):
        response = mpc.core.MPC.get_observatory_codes()
        greenwich = ['000', 0.0, 0.62411, 0.77873, 'Greenwich']
        assert all([r == g for r, g in zip(response[0], greenwich)])

    @pytest.mark.parametrize('target', ['(3202)', 'C/2003 A2'])
    def test_get_ephemeris_by_target(self, target):
        # test that query succeeded
        response = mpc.core.MPC.get_ephemeris(target)
        assert len(response) > 0

    def test_get_ephemeris_target_fail(self):
        # test that query failed
        with pytest.raises(InvalidQueryError):
            mpc.core.MPC.get_ephemeris('test fail')
