# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib2
import requests
import astropy.coordinates as coord
import astropy.units as u
from ...utils import chunk_read, chunk_report
from ...utils import class_or_instance
from ...utils import commons
from astropy.tests.helper import pytest, remote_data

class SimpleQueryClass(object):
    @class_or_instance
    def query(self):
        """ docstring """
        if self is SimpleQueryClass:
            print("Calling query as class method")
            return "class"
        else:
            print("Calling query as instance method")
            return "instance"

@remote_data
def test_utils():
    response = urllib2.urlopen('http://www.ebay.com')
    C = chunk_read(response, report_hook=chunk_report)
    print C

def test_class_or_instance():
    assert SimpleQueryClass.query() == "class"
    U = SimpleQueryClass()
    assert U.query() == "instance"
    assert SimpleQueryClass.query.__doc__ == " docstring "

@pytest.mark.parametrize(('coordinates'),
                         [coord.ICRSCoordinates(ra=148,
                                                dec=69,
                                                unit=(u.deg, u.deg)),
                          "00h42m44.3s +41d16m9s"
                          ])
def test_parse_coordinates_1(coordinates):
    c = commons.parse_coordinates(coordinates)
    assert c != None

@remote_data
def test_parse_coordinates_2():
    c = commons.parse_coordinates("m81")
    assert c != None

def test_parse_coordinates_3():
    with pytest.raises(Exception):
        commons.parse_coordinates(9.8 * u.kg)

@pytest.mark.parametrize(('radius'),
                         ['5d0m0s',
                          5 * u.deg
                          ])
def test_parse_radius_1(radius):
    assert commons.parse_radius(radius).degrees == 5

@pytest.mark.parametrize(('radius'),
                         [5,
                          9.8 * u.kg
                          ])
def test_parse_radius_2(radius):
    with pytest.raises(Exception):
        commons.parse_radius(radius)

def test_send_request_post(monkeypatch):
    def mock_post(url, data, timeout):
        class MockResponse(object):
            def __init__(self, url, data):
                self.url = url
                self.data = data
        return MockResponse(url, data)
    monkeypatch.setattr(requests, 'post', mock_post)

    response = commons.send_request('https://github.com/astropy/astroquery',
                                    data=dict(msg='ok'), timeout=30)
    assert response.url == 'https://github.com/astropy/astroquery'
    assert response.data == dict(msg='ok')

def test_send_request_get(monkeypatch):
    def mock_get(url, params, timeout):
        req = requests.Request('GET', url, params=params).prepare()
        return req
    monkeypatch.setattr(requests, 'get', mock_get)
    response = commons.send_request('https://github.com/astropy/astroquery',
                                    dict(a='b'), 60, request_type='GET')
    assert response.url == 'https://github.com/astropy/astroquery?a=b'
