# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from ... import fermi
from astropy.tests.helper import pytest
import requests
import os

DATA_FILES = {'async':"query_result_m31.html",
        'result':'result_page_m31.html',
        #'http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/QueryResults.cgi?id=L13090110364329E469B418',
        'fits': ['http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110364329E469B418_PH00.fits',
                 'http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110364329E469B418_SC00.fits']}

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class MockResponse(object):

    def __init__(self, content):
        self.content = content
        self.text = content

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

def post_mockreturn(url, data=None, timeout=50):
    if data is not None:
        with open(data_path(DATA_FILES['async']),'r') as r:
            response = MockResponse(r.read())
    else:
        with open(data_path(DATA_FILES['result']),'r') as r:
            response = MockResponse(r.read())
    return response

def test_FermiLAT_query(patch_post):

    # Make a query that results in small SC and PH file sizes
    result = fermi.FermiLAT.query_object('M31', energyrange_MeV='1000, 100000',
                                         obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    assert result == DATA_FILES['fits']


def test_FermiLAT_DelayedQuery():
    pass
    # result_url = 'http://www.google.com'
    # query = fermi.FermiLAT_DelayedQuery(result_url)
    # TODO
    # print query

if __name__ == '__main__':
    test_FermiLAT_query()
