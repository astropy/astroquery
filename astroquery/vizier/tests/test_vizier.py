# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests
from astropy.tests.helper import pytest, remote_data
from ... import vizier

VII258_DATA = "vii258.txt"
II246_DATA = "ii246.txt"

def data(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

class MockResponse(object):
    def __init__(self, content):
        self.content = content

def post_mockreturn(url, data=None):
    if "258" in data:
        filename = VII258_DATA
    elif "246" in data:
        filename = II246_DATA
    else:
        raise Exception("Query constructed incorrectly")
    content = open(filename, "r").read()
    return MockResponse(content)

def test_simple_local(patch_post):
    # Find all AGNs in Veron & Cetty with Vmag in [5.0; 11.0]
    query = {}
    query["-source"] = "VII/258/vv10"
    query["-out"] = ["Name", "Sp", "Vmag"]
    query["Vmag"] = "5.0..11.0"
    table1 = vizier.vizquery(query)

    # Find sources in 2MASS matching the AGNs positions to within 2 arcsec
    query = {}
    query["-source"] = "II/246/out"
    query["-out"] = ["RAJ2000", "DEJ2000", "2MASS", "Kmag"]
    query["-c.rs"] = "2"
    query["-c"] = table1
    table2 = vizier.vizquery(query)

    assert table1 != None
    assert table2 != None

    print(table1)
    print(table2)

@remote_data
def test_simple():
    # Find all AGNs in Veron & Cetty with Vmag in [5.0; 11.0]
    query = {}
    query["-source"] = "VII/258/vv10"
    query["-out"] = ["Name", "Sp", "Vmag"]
    query["Vmag"] = "5.0..11.0"
    table1 = vizier.vizquery(query)

    # Find sources in 2MASS matching the AGNs positions to within 2 arcsec
    query = {}
    query["-source"] = "II/246/out"
    query["-out"] = ["RAJ2000", "DEJ2000", "2MASS", "Kmag"]
    query["-c.rs"] = "2"
    query["-c"] = table1
    table2 = vizier.vizquery(query)

    print(table1)
    print(table2)

# get this error from Table(data,names)...
# ValueError: masked should be one of True, False, None
