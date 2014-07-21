import os.path

import pytest
import requests
from astropy.units import arcsec

from ...utils.testing_tools import MockResponse
from ...xmatch import XMatch

DATA_FILES = {'get':'tables.csv', # .action.getVizieRTableNames
              'post':'pos_list.csv',} # .request.xmatch

class MockResponseXmatch(MockResponse):
    def __init__(self, method, url, data, **kwargs):
        super(MockResponseXmatch, self).__init__(**kwargs)

        self.data = data
        fn = data_path(DATA_FILES[method.lower()])
        with open(fn, 'r') as f:
            self.content = f.read()

    def get_content(self):
        return self.content

@pytest.fixture
def patch_request(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, "request", request_mockreturn)
    return mp

def request_mockreturn(method, url, data, **kwargs):
    return MockResponseXmatch(method, url, data)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_xmatch_query_invalid_max_distance():
    with pytest.raises(ValueError) as ex:
        XMatch().query_async('', '', 181 * arcsec)
        assert str(ex.value) == (
            'max_distance argument must not be greater than 180')


def test_get_available_tables(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, 'request', request_mockreturn)

    tables = xm.get_available_tables()
    assert tables
    assert 'II/311/wise' in tables
    assert 'II/246/out' in tables


def test_xmatch_is_avail_table(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, 'request', request_mockreturn)

    assert xm.is_table_available('II/311/wise')
    assert xm.is_table_available('II/246/out')
    assert not xm.is_table_available('vizier:II/311/wise')

# This should pass if we give it reasonable inputs (i.e. not 'something')
@pytest.mark.xfail
def test_xmatch_query(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, 'request', request_mockreturn)

    blah = xm.query('something')
    blah = xm().query('something')
