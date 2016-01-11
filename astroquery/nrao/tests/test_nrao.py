# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import requests

from astropy.tests.helper import pytest
import astropy.units as u
from astropy.table import Table

from ... import nrao
from ...utils.testing_tools import MockResponse
from ...utils import commons


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

DATA_FILES = {'votable': 'votable.xml'}


@pytest.fixture
def patch_parse_coordinates(request):
    def parse_coordinates_mock_return(c):
        return c
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'parse_coordinates', parse_coordinates_mock_return)
    return mp


@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', post_mockreturn)
    return mp


def post_mockreturn(self, method, url, data=None, timeout=10, files=None,
                    params=None, headers=None, **kwargs):
    if method != 'POST':
        raise ValueError("A 'post request' was made with method != POST")
    filename = data_path(DATA_FILES['votable'])
    content = open(filename, "rb").read()
    return MockResponse(content, **kwargs)


def test_query_region_async(patch_post, patch_parse_coordinates):
    response = nrao.core.Nrao.query_region_async(
        commons.ICRSCoordGenerator("04h33m11.1s 05d21m15.5s"),
        radius='5d0m0s', equinox='B1950',
        freq_low=1000 * u.kHz, freq_up=2000 * u.kHz,
        get_query_payload=True)

    assert response['SRAD'].startswith('5') and response['SRAD'].endswith('d')
    assert response['EQUINOX'] == 'B1950'
    assert response['OBSFREQ1'] == '1.0-2.0'
    response = nrao.core.Nrao.query_region_async(
        commons.ICRSCoordGenerator("04h33m11.1s 05d21m15.5s"))
    assert response is not None


def test_query_region(patch_post, patch_parse_coordinates):
    result = nrao.core.Nrao.query_region(
        commons.ICRSCoordGenerator("04h33m11.1s 05d21m15.5s"))
    assert isinstance(result, Table)
    assert len(result) > 0
    if 'Start Time' in result.colnames:
        assert result['Start Time'][0] == b'83-Sep-27 09:19:30'
    else:
        assert result['Start_Time'][0] == b'83-Sep-27 09:19:30'
    assert result['RA'][0] == b'04h33m11.096s'
