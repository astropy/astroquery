# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path

import requests
import pytest
from astropy.io import ascii
from astropy.table import Table
from astropy.units import arcsec

from astroquery.utils.mocks import MockResponse
from ...xmatch import XMatch

DATA_DIR = Path(__file__).parent / "data"
DATA_FILES = {
    'get': 'tables.csv',  # .action.getVizieRTableNames
    'post': 'query_res.csv',  # .request.xmatch
    'poslist': 'posList.csv',
    'poslist_duplicates': 'posList_duplicates.csv',
}


class MockResponseXmatch(MockResponse):
    def __init__(self, method, url, data, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        filename = DATA_DIR / DATA_FILES[method.lower()]
        with open(filename, "rb") as file:
            self.content = file.read()

    def get_content(self):
        return self.content


@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests, "_request", request_mockreturn)
    return mp


def request_mockreturn(method, url, data, **kwargs):
    return MockResponseXmatch(method, url, data)


def test_xmatch_query_invalid_max_distance():
    with pytest.raises(ValueError) as ex:
        XMatch().query_async('', '', 181 * arcsec)
        assert str(ex.value) == (
            'max_distance argument must not be greater than 180')


def test_get_available_tables(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, '_request', request_mockreturn)

    tables = xm.get_available_tables()
    assert tables
    assert 'II/311/wise' in tables
    assert 'II/246/out' in tables


def test_xmatch_is_avail_table(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, '_request', request_mockreturn)

    assert xm.is_table_available('II/311/wise')
    assert xm.is_table_available('II/246/out')
    assert xm.is_table_available('vizier:II/311/wise')
    assert not xm.is_table_available('blablabla')


def test_xmatch_query_local(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, '_request', request_mockreturn)
    with open(DATA_DIR / "posList.csv") as pos_list:
        response = xm.query_async(
            cat1=pos_list, cat2='vizier:II/246/out', max_distance=5 * arcsec,
            colRA1='ra', colDec1='dec')
    table = ascii.read(response.text, format='csv', fast_reader=False)
    assert isinstance(table, Table)
    assert table.colnames == [
        'angDist', 'ra', 'dec', 'my_id', '2MASS', 'RAJ2000', 'DEJ2000',
        'errHalfMaj', 'errHalfMin', 'errPosAng', 'Jmag', 'Hmag', 'Kmag',
        'e_Jmag', 'e_Hmag', 'e_Kmag', 'Qfl', 'Rfl', 'X', 'MeasureJD']
    assert len(table) == 11


def test_xmatch_query_cat1_table_local(monkeypatch):
    xm = XMatch()
    monkeypatch.setattr(xm, '_request', request_mockreturn)
    with open(DATA_DIR / "posList.csv") as pos_list:
        input_table = Table.read(pos_list.readlines(),
                                 format='ascii.csv',
                                 guess=False)
    response = xm.query_async(
        cat1=input_table, cat2='vizier:II/246/out', max_distance=5 * arcsec,
        colRA1='ra', colDec1='dec')
    table = ascii.read(response.text, format='csv', fast_reader=False)
    assert isinstance(table, Table)
    assert table.colnames == [
        'angDist', 'ra', 'dec', 'my_id', '2MASS', 'RAJ2000', 'DEJ2000',
        'errHalfMaj', 'errHalfMin', 'errPosAng', 'Jmag', 'Hmag', 'Kmag',
        'e_Jmag', 'e_Hmag', 'e_Kmag', 'Qfl', 'Rfl', 'X', 'MeasureJD']
    assert len(table) == 11
