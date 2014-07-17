import os.path

import pytest
import requests
from astropy.units import arcsec

from ...utils.testing_tools import MockResponse
from ...xmatch import XMatch


class MockResponseXmatch(MockResponse):
    def __init__(self, content, **kwargs):
        self.content = content
        super(MockResponseXmatch, self).__init__(**kwargs)

    def get_content(self):
        return self.content


@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, "get", get_mockreturn)
    return mp


def get_mockreturn(url, data, timeout, **kwargs):
    with open(data_path('tables.csv')) as f:
        data = f.read()
    return MockResponseXmatch(data)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_xmatch_query_invalid_max_distance():
    with pytest.raises(ValueError) as ex:
        XMatch().query_async('', '', 181 * arcsec)
        assert str(ex.value) == (
            'max_distance argument must not be greater than 180')


def test_get_available_tables():
    tables = XMatch().get_available_tables()
    assert tables
    assert 'II/311/wise' in tables
    assert 'II/246/out' in tables


def test_xmatch_is_avail_table():
    assert XMatch().is_table_available('II/311/wise')
    assert XMatch().is_table_available('II/246/out')
    assert not XMatch().is_table_available('vizier:II/311/wise')
