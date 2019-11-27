""" Test Gemini Astroquery module.

For information on how/why this test is built the way it is, see the astroquery
documentation at:

https://astroquery.readthedocs.io/en/latest/testing.html
"""
import os
import pytest
import requests
from astropy import units
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroquery import gemini

DATA_FILES = {"m101": "m101.json"}


class MockResponse(object):

    def __init__(self, text):
        self.text = text


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def get_mockreturn(url, *args, **kwargs):
    filename = data_path(DATA_FILES['m101'])
    f = open(filename, 'r')
    text = f.read()
    retval = MockResponse(text)
    f.close()
    return retval


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


coords = SkyCoord(210.80242917, 54.34875, unit="deg")


def test_observations_query_region(patch_get):
    result = gemini.Observations.query_region(coords, radius=0.3 * units.deg)
    assert isinstance(result, Table)


def test_observations_query_criteria(patch_get):
    result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-CAL20191122', observation_type='BIAS')
    assert isinstance(result, Table)


def test_observations_query_raw(patch_get):
    result = gemini.Observations.query_raw('GMOS-N', 'BIAS', progid='GN-CAL20191122')
    assert isinstance(result, Table)
