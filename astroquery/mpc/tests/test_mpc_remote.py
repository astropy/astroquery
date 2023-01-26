# Licensed under a 3-clause BSD style license - see LICENSE.rst
import requests
import pytest

from astroquery.exceptions import InvalidQueryError
from astroquery import mpc


@pytest.mark.remote_data
class TestMPC:

    @pytest.mark.parametrize('target_type, name', [
        ('asteroid', 'ceres'),
        ('asteroid', 'eros'),
        ('asteroid', 'vesta'),
        ('asteroid', 'pallas'),
        ('asteroid', 'piszkesteto')])
    def test_query_object_valid_object_by_name(self, target_type, name):
        # Keep all 3 of the objects in the tests, too that used to cause issue
        # https://github.com/astropy/astroquery/issues/2531
        response = mpc.MPC.query_object_async(target_type=target_type, name=name)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert response.json()[0]['name'].lower() == name

    @pytest.mark.parametrize('target_type, number', [
        ('comet', '103P')])
    def test_query_object_valid_object_by_number(self, target_type, number):
        response = mpc.MPC.query_object_async(target_type=target_type, number=number)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert str(response.json()[0]['number']) + \
            response.json()[0]['object_type'] == number

    @pytest.mark.parametrize('target_type, designation', [
        ('comet', 'C/2012 S1')])
    def test_query_object_valid_object_by_designation(self, target_type, designation):
        response = mpc.MPC.query_object_async(target_type=target_type, designation=designation)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 1
        assert response.json()[0]['designation'].lower() == designation.lower()

    @pytest.mark.parametrize('name', [
        ('ceres'),
        ('eros'),
        ('pallas')])
    def test_query_object_get_query_payload_remote(self, name):
        request_payload = mpc.MPC.query_object_async(
            get_query_payload=True, target_type='asteroid', name=name)
        assert request_payload == {"name": name, "json": 1, "limit": 1}

    def test_query_multiple_objects(self):
        response = mpc.MPC.query_objects_async(
            target_type='asteroid', epoch_jd=2458200.5, limit=5)
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 5

    def test_query_object_by_nonexistent_name(self):
        response = mpc.MPC.query_object_async(
            target_type='asteroid', name="invalid object")
        assert response.status_code == requests.codes.ok
        assert len(response.json()) == 0

    def test_query_object_invalid_parameter(self):
        response = mpc.MPC.query_object_async(
            target_type='asteroid', blah="blah")
        assert response.status_code == requests.codes.ok
        assert "Unrecognized parameter" in str(response.content)

    def test_get_observatory_codes(self):
        response = mpc.MPC.get_observatory_codes()
        greenwich = ['000', 0.0, 0.62411, 0.77873, 'Greenwich']
        assert all([r == g for r, g in zip(response[0], greenwich)])

    @pytest.mark.parametrize('target', ['(3202)', 'C/2003 A2'])
    def test_get_ephemeris_by_target(self, target):
        # test that query succeeded
        response = mpc.MPC.get_ephemeris(target)
        assert len(response) > 0

    def test_get_ephemeris_target_fail(self):
        # test that query failed
        with pytest.raises(InvalidQueryError):
            mpc.MPC.get_ephemeris('test fail')

    def test_get_observations(self):
        # asteroids
        a = mpc.MPC.get_observations(2)
        assert a['number'][0] == 2

        a = mpc.MPC.get_observations(12893)
        assert a['number'][0] == 12893
        assert a['desig'][-1] == '1998 QS55'
        a = mpc.MPC.get_observations("2019 AA")
        assert a['desig'][0] == '2019 AA'
        a = mpc.MPC.get_observations("2017 BC136")
        assert a['desig'][0] == '2017 BC136'

        # comets
        a = mpc.MPC.get_observations('2P')
        assert a['number'][0] == 2
        assert a['comettype'][0] == 'P'
        a = mpc.MPC.get_observations('258P')
        assert a['number'][0] == 258
        assert a['comettype'][0] == 'P'
        a = mpc.MPC.get_observations("P/2018 P4")
        assert a['desig'][0] == "2018 P4"
        with pytest.raises(ValueError):
            a = mpc.MPC.get_observations("2018 P4")
        a = mpc.MPC.get_observations("P/2018 P4")
        assert a['desig'][0] == "2018 P4"
        a = mpc.MPC.get_observations("C/2013 K1")
        assert a['desig'][0] == "2013 K1"
        a = mpc.MPC.get_observations("P/2019 A4")
        assert a['desig'][0] == "2019 A4"

        with pytest.raises(TypeError):
            a = mpc.MPC.get_observations()
