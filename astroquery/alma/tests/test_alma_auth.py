# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ..core import AlmaAuth
from ...exceptions import LoginError

import pytest
from unittest.mock import Mock


def test_host():
    def _requests_mock_ok(method, url, **kwargs):
        response = Mock()
        response.status_code = 200
        return response

    test_subject = AlmaAuth()
    test_subject.auth_hosts = ['almaexample.com']
    test_subject._request = Mock(side_effect=_requests_mock_ok)
    assert test_subject.get_valid_host() == 'almaexample.com'


def test_host_default():
    def _requests_mock_ok(method, url, **kwargs):
        response = Mock()
        response.status_code = 200
        return response

    test_subject = AlmaAuth()
    test_subject._request = Mock(side_effect=_requests_mock_ok)
    assert test_subject.get_valid_host() == 'asa.alma.cl'


def test_host_err():
    def _requests_mock_err(method, url, **kwargs):
        response = Mock()
        response.status_code = 404
        return response

    test_subject = AlmaAuth()
    test_subject.auth_hosts = ['almaexample.com']
    test_subject._request = Mock(side_effect=_requests_mock_err)
    with pytest.raises(LoginError):
        test_subject.get_valid_host()


def test_login_bad_error():
    def _response_json():
        return {
            'error': 'Badness',
            'error_description': 'Something very bad'
        }

    def _requests_mock_err(method, url, **kwargs):
        response = Mock()
        if test_subject._VERIFY_WELL_KNOWN_ENDPOINT in url:
            response.status_code = 200
        elif test_subject._LOGIN_ENDPOINT in url:
            response.json = _response_json
        return response

    test_subject = AlmaAuth()
    test_subject.auth_hosts = ['almaexample.com']
    test_subject._request = Mock(side_effect=_requests_mock_err)
    with pytest.raises(LoginError) as e:
        test_subject.login('TESTUSER', 'TESTPASS')
    assert 'Could not log in to ALMA authorization portal' in e.value.args[0]


def test_login_missing_token():
    def _response_json():
        return {
            'irrlevant': 'Weird',
        }

    def _requests_mock_err(method, url, **kwargs):
        response = Mock()
        if test_subject._VERIFY_WELL_KNOWN_ENDPOINT in url:
            response.status_code = 200
        elif test_subject._LOGIN_ENDPOINT in url:
            response.json = _response_json
        return response

    test_subject = AlmaAuth()
    test_subject.auth_hosts = ['almaexample.com']
    test_subject._request = Mock(side_effect=_requests_mock_err)
    with pytest.raises(LoginError) as e:
        test_subject.login('TESTUSER', 'TESTPASS')

    assert 'No error from server, but missing access token from host' in e.value.args[0]


def test_login_success():
    def _response_json():
        return {
            'access_token': 'MYTOKEN'
        }

    def _requests_mock_good(method, url, **kwargs):
        response = Mock()
        print(f'URL is {url}')
        if test_subject._VERIFY_WELL_KNOWN_ENDPOINT in url:
            response.status_code = 200
        elif test_subject._LOGIN_ENDPOINT in url:
            response.json = _response_json
        return response

    test_subject = AlmaAuth()
    test_subject.auth_hosts = ['almaexample.com']
    test_subject._request = Mock(side_effect=_requests_mock_good)
    test_subject.login('TESTUSER', 'TESTPASS')
