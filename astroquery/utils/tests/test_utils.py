# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib2
import requests
import astropy.coordinates as coord
import astropy.units as u
from ...utils import chunk_read, chunk_report
from ...utils import class_or_instance
from ...utils import commons
from astropy.table import Table
from astropy.tests.helper import pytest, remote_data
import astropy.io.votable as votable

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

def test_send_request_err():
    with pytest.raises(ValueError):
        commons.send_request('https://github.com/astropy/astroquery',
                     dict(a='b'), 60, request_type='PUT')

col_1 = [1, 2, 3]
col_2 = [0, 1, 0, 1, 0, 1]
col_3 = ['v','w', 'x', 'y', 'z']
# table t1 with 1 row and 3 cols
t1 = Table([col_1[:1], col_2[:1], col_3[:1]], meta={'name': 't1'})
# table t2 with 3 rows and 1 col
t2 = Table([col_1], meta={'name': 't2'})
# table t3 with 3 cols and 3 rows
t3 = Table([col_1, col_2[:3], col_3[:3]], meta={'name': 't3'})


def test_TableDict():
    in_list  = create_in_list([t1, t2, t3])
    table_list = commons.TableList(in_list)
    repr_str = table_list.__repr__()
    assert repr_str == '<TableList with 3 table(s) and 7 total row(s)>'

def test_TableDict_print_table_list(capsys):
    in_list  = create_in_list([t1, t2, t3])
    table_list = commons.TableList(in_list)
    table_list.print_table_list()
    out, err = capsys.readouterr()
    assert out == ("<TableList with 3 tables:\n\t't1' with 3 column(s) and 1 row(s)"
                   " \n\t't2' with 1 column(s) and 3 row(s)"
                   " \n\t't3' with 3 column(s) and 3 row(s) \n>\n")



def create_in_list(t_list):
    return [(t.meta['name'], t) for t in t_list ]

def test_suppress_vo_warnings(recwarn):
    commons.suppress_vo_warnings()
    votable.exceptions.warn_or_raise(votable.exceptions.W01)
    votable.exceptions.warn_or_raise(votable.exceptions.VOTableChangeWarning)
    votable.exceptions.warn_or_raise(votable.exceptions.VOWarning)
    votable.exceptions.warn_or_raise(votable.exceptions.VOTableSpecWarning)
    with pytest.raises(Exception):
        recwarn.pop(votable.exceptions.VOWarning)
