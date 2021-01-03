""" Test Gemini Astroquery module.

For information on how/why this test is built the way it is, see the astroquery
documentation at:

https://astroquery.readthedocs.io/en/latest/testing.html
"""
from datetime import date
import json
import os
import pytest
import requests
from astropy import units
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroquery import gemini
from astroquery.gemini.urlhelper import URLHelper

DATA_FILES = {"m101": "m101.json"}


class MockResponse:

    def __init__(self, text):
        self.text = text

    def json(self):
        return json.loads(self.text)


@pytest.fixture
def patch_get(request):
    """ mock get requests so they return our canned JSON to mimic Gemini's archive website """
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def get_mockreturn(url, *args, **kwargs):
    """ generate the actual mock textual data from our included datafile with json results """
    filename = data_path(DATA_FILES['m101'])
    f = open(filename, 'r')
    text = f.read()
    retval = MockResponse(text)
    f.close()
    return retval


def data_path(filename):
    """ determine the path to our sample data file """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


""" Coordinates to use for testing """
coords = SkyCoord(210.80242917, 54.34875, unit="deg")


def test_observations_query_region(patch_get):
    """ test query against a region of the sky """
    result = gemini.Observations.query_region(coords, radius=0.3 * units.deg)
    assert isinstance(result, Table)
    assert len(result) > 0


def test_observations_query_criteria(patch_get):
    """ test query against an instrument/program via criteria """
    result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-CAL20191122',
                                                observation_type='BIAS',
                                                utc_date=(date(2019, 10, 1), date(2019, 11, 25)))
    assert isinstance(result, Table)
    assert len(result) > 0


def test_observations_query_raw(patch_get):
    """ test querying raw """
    result = gemini.Observations.query_raw('GMOS-N', 'BIAS', progid='GN-CAL20191122')
    assert isinstance(result, Table)
    assert len(result) > 0


def test_url_helper_arg():
    """ test the urlhelper logic """
    urlh = URLHelper()
    args = ["foo"]
    kwargs = {}
    url = urlh.build_url(*args, **kwargs)
    assert url == "https://archive.gemini.edu/jsonsummary/notengineering/NotFail/foo"


def test_url_helper_kwarg():
    """ test the urlhelper logic """
    urlh = URLHelper()
    args = []
    kwargs = {"foo": "bar"}
    url = urlh.build_url(*args, **kwargs)
    assert url == "https://archive.gemini.edu/jsonsummary/notengineering/NotFail/foo=bar"


def test_url_helper_radius():
    """ test the urlhelper logic """
    urlh = URLHelper()
    args = []
    kwargs = {"radius": "0.4d"}
    url = urlh.build_url(*args, **kwargs)
    assert url == "https://archive.gemini.edu/jsonsummary/notengineering/NotFail/sr=0.400000d"


def test_url_helper_coordinates():
    """ test the urlhelper logic """
    urlh = URLHelper()
    args = []
    kwargs = {"coordinates": "210.80242917 54.348753"}
    url = urlh.build_url(*args, **kwargs)
    assert url == "https://archive.gemini.edu/jsonsummary/notengineering/NotFail/ra=210.802429/dec=54.348753"
