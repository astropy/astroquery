# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import requests
import pytest
import astropy.coordinates as coord
from astroquery.utils.mocks import MockResponse
from ... import fermi

DATA_FILES = {'async': "query_result_m31.html",
              'result': 'result_page_m31.html',
              'result_url': 'https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/QueryResults.cgi?id=L13090120163429E469B432',
              'fits': ['https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110364329E469B418_PH00.fits',
                       'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L13090110364329E469B418_SC00.fits']}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(fermi.FermiLAT, '_request', post_mockreturn)
    mp.setattr(requests, 'post', post_mockreturn)
    return mp


def post_mockreturn(method="POST", url=None, data=None, timeout=50, **kwargs):
    if data is not None:
        with open(data_path(DATA_FILES['async']), 'rb') as r:
            response = MockResponse(r.read(), **kwargs)
    else:
        with open(data_path(DATA_FILES['result']), 'rb') as r:
            response = MockResponse(r.read(), **kwargs)
    return response


FK5_COORDINATES = coord.SkyCoord(10.68471, 41.26875, unit=('deg', 'deg'))

# disable waiting so tests run fast
fermi.core.get_fermilat_datafile.TIMEOUT = 1
fermi.core.get_fermilat_datafile.check_frequency = 0


def test_FermiLAT_query_async(patch_post):
    result = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, energyrange_MeV='1000, 100000',
        obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    assert result == DATA_FILES['result_url']


def test_getfermilatdatafile(patch_post):
    result = fermi.core.get_fermilat_datafile(data_path(DATA_FILES['result']),
                                              verbose=True)
    assert result


def test_FermiLAT_query(patch_post):
    # Make a query that results in small SC and PH file sizes
    result = fermi.core.FermiLAT.query_object(
        FK5_COORDINATES, energyrange_MeV='1000, 100000',
        obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    assert result == DATA_FILES['fits']
