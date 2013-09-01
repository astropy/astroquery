# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from ... import fermi
from astropy.tests.helper import pytest
import requests

data = {'async':'http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/QueryResults.cgi?id=L13090110364329E469B418',
        'sync':['http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110261929E469B426_PH00.fits',
                'http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110261929E469B426_SC00.fits']}

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

def post_mockreturn(url, data, timeout):
    response = MockResponse(data['async'])
    return response

def test_FermiLAT_query(patch_post):

    # Make a query that results in small SC and PH file sizes
    result = fermi.FermiLAT.query_object('M31', energyrange_MeV='1000, 100000',
                                         obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    assert result == ['http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110261929E469B426_PH00.fits',
                      'http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110261929E469B426_SC00.fits']
    


def test_FermiLAT_DelayedQuery():
    pass
    # result_url = 'http://www.google.com'
    # query = fermi.FermiLAT_DelayedQuery(result_url)
    # TODO
    # print query

if __name__ == '__main__':
    test_FermiLAT_query()
