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
        self.headers = {'content-length': str(len(text))}
        self.status_code = 200

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        pass

    def iter_content(self, blocksize):
        yield self.text

    def close(self):
        pass


@pytest.fixture
def patch_get(request):
    """ mock get requests so they return our canned JSON to mimic Gemini's archive website """
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests.Session, 'request', get_mockreturn)


@pytest.fixture
def patch_content(monkeypatch):
    """Mock requests with encoded content."""
    def mock_request(*args, **kwargs):
        return MockResponse(b"mock_content")

    monkeypatch.setattr(requests.Session, 'request', mock_request)


# to inspect behavior, updated when the mock get call is made
saved_request = None


def get_mockreturn(url, *args, **kwargs):
    """ generate the actual mock textual data from our included datafile with json results """
    global saved_request
    saved_request = {'url': url, 'args': args, 'kwargs': kwargs}
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


def test_observations_query_criteria_radius_defaults(patch_get):
    """ test query against an instrument/program via criteria """
    result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-CAL20191122',
                                                observation_type='BIAS')
    global saved_request
    assert (saved_request is not None and 'args' in saved_request and len(saved_request['args']) >= 2)
    assert ('/sr=' not in saved_request['args'][1])
    saved_request = None
    result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-2016A-Q-9',
                                                observation_type='BIAS', coordinates=coords)
    assert len(result) > 0
    assert (saved_request is not None and 'args' in saved_request and len(saved_request['args']) >= 2)
    assert ('/sr=0.300000d' in saved_request['args'][1])
    saved_request = None
    gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-2016A-Q-9',
                                       observation_type='BIAS', objectname='m101')
    assert (saved_request is not None and 'args' in saved_request and len(saved_request['args']) >= 2)
    assert ('/sr=0.300000d' in saved_request['args'][1])


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


# send arg, should it have notengineering?, should it have NotFail?
eng_fail_tests = [
    ('notengineering', True, True),
    ('engineering', False, True),
    ('includeengineering', False, True),
    ('NotFail', True, True),
    ('AnyQA', True, False),
    ('Pass', True, False),
    ('Lucky', True, False),
    ('Win', True, False),
    ('Usable', True, False),
    ('Undefind', True, False),
    ('Fail', True, False),
]


@pytest.mark.parametrize("test_arg", eng_fail_tests)
def test_url_helper_eng_fail(test_arg):
    """ test the urlhelper logic around engineering/fail requests/defaults """
    urlh = URLHelper()
    args = [test_arg[0]]
    should_have_noteng = test_arg[1]
    should_have_notfail = test_arg[2]
    kwargs = {}
    url = urlh.build_url(*args, **kwargs)
    urlsplit = url.split('/')
    assert (('notengineering' in urlsplit) == should_have_noteng)
    assert (('NotFail' in urlsplit) == should_have_notfail)


def test_logout():
    """Test logout functionality."""
    gemini.Observations._session.cookies = {"gemini_archive_session": "some_value"}
    gemini.Observations._authenticated = True
    gemini.Observations.logout()
    assert "gemini_archive_session" not in gemini.Observations._session.cookies
    assert gemini.Observations._authenticated is False


def test_get_file_content(patch_content):
    """Test wrapper around _download_file_content."""
    content = gemini.Observations.get_file_content("filename", timeout=5)
    assert content == b"mock_content"


def test_get_file_url():
    """Test generating file URL based on filename."""
    url = gemini.Observations.get_file_url("filename")
    assert url == "https://archive.gemini.edu/file/filename"

