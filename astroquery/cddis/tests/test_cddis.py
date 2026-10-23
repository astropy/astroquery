# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest

from astroquery.cddis import CDDIS, CDDISClass
from astroquery.exceptions import LoginError
from astroquery.query import AstroQuery
from astroquery.utils.mocks import MockResponse


def test_query_files_parses_archive_listing(monkeypatch):
    content = (
        b'<html><a href="../">Parent Directory</a>'
        b'<a href="ABCD00USA_R_20250010000_01D_30S_MO.rnx.gz">'
        b'ABCD00USA_R_20250010000_01D_30S_MO.rnx.gz</a>'
        b'<a href="subdir/">subdir/</a></html>'
    )
    response = MockResponse(
        content=content,
        url='https://cddis.nasa.gov/archive/gnss/data/daily/2025/001/25d/')
    monkeypatch.setattr(CDDIS, '_request', lambda *args, **kwargs: response)

    result = CDDIS.query_files('data/daily/2025/001/25d', cache=False)

    assert result['name'].tolist() == [
        'ABCD00USA_R_20250010000_01D_30S_MO.rnx.gz', 'subdir/']
    assert result['path'].tolist() == [
        'data/daily/2025/001/25d/ABCD00USA_R_20250010000_01D_30S_MO.rnx.gz',
        'data/daily/2025/001/25d/subdir']
    assert result['is_directory'].tolist() == [False, True]


def test_query_files_parses_absolute_archive_links(monkeypatch):
    response = MockResponse(
        content=(
            b'<html><a href="https://cddis.nasa.gov/archive/gnss/'
            b'data/daily/2025/001/25d/ABCD.rnx.gz">ABCD.rnx.gz</a></html>'
        ),
        url='https://cddis.nasa.gov/archive/gnss/data/daily/2025/001/25d/')
    monkeypatch.setattr(CDDIS, '_request', lambda *args, **kwargs: response)

    result = CDDIS.query_files('data/daily/2025/001/25d', cache=False)

    assert result['path'].tolist() == [
        'data/daily/2025/001/25d/ABCD.rnx.gz']
    assert result['is_directory'].tolist() == [False]


def test_query_files_strips_whitespace_from_archive_links(monkeypatch):
    response = MockResponse(
        content=(
            b'<html><a href="ABMF00GLP_R_20250010000_01D_30S_MO.crx.gz ">'
            b'ABMF00GLP_R_20250010000_01D_30S_MO.crx.gz</a></html>'
        ),
        url='https://cddis.nasa.gov/archive/gnss/data/daily/2025/001/25d/')
    monkeypatch.setattr(CDDIS, '_request', lambda *args, **kwargs: response)

    result = CDDIS.query_files('data/daily/2025/001/25d', cache=False)

    assert result['path'].tolist() == [
        'data/daily/2025/001/25d/ABMF00GLP_R_20250010000_01D_30S_MO.crx.gz']


def test_query_files_returns_empty_table_for_empty_listing(monkeypatch):
    response = MockResponse(
        content=b'<html><a href="../">Parent Directory</a></html>',
        url='https://cddis.nasa.gov/archive/gnss/data/daily/2025/001/25d/')
    monkeypatch.setattr(CDDIS, '_request', lambda *args, **kwargs: response)

    result = CDDIS.query_files('data/daily/2025/001/25d', cache=False)

    assert result.colnames == ['name', 'path', 'is_directory']
    assert len(result) == 0


@pytest.mark.parametrize('path', [
    '../outside',
    '/absolute/path',
    'data/../outside',
    'data//daily',
    'data/daily?query=1',
])
def test_archive_url_rejects_unsafe_paths(path):
    with pytest.raises(ValueError):
        CDDISClass()._archive_url(path)


def test_query_files_requires_earthdata_login(monkeypatch, tmp_path):
    response = MockResponse(
        content=b'Login required',
        url='https://urs.earthdata.nasa.gov/oauth/authorize')
    monkeypatch.setattr(CDDIS, '_cache_location', tmp_path)
    cache_location = CDDIS.cache_location
    query = AstroQuery('GET', 'https://cddis.nasa.gov/archive/gnss/products/')
    cached_response = query.request_file(cache_location)
    cached_response.write_bytes(b'cached login response')

    def mock_request(*args, **kwargs):
        CDDIS._last_query = query
        return response

    monkeypatch.setattr(CDDIS, '_request', mock_request)

    with pytest.raises(LoginError, match='Earthdata Login'):
        CDDIS.query_files('products')
    assert not cached_response.exists()


def test_download_file_uses_archive_path_and_save(monkeypatch, tmp_path):
    response = MockResponse(
        content=b'data', url='https://cddis.nasa.gov/archive/gnss/file.dat')
    calls = {}

    def mock_request(*args, **kwargs):
        calls.update(kwargs)
        filepath = str(tmp_path / 'file.dat')
        return filepath, response

    monkeypatch.setattr(CDDIS, '_request', mock_request)
    result = CDDIS.download_file('data/daily/file.dat', savedir=str(tmp_path))

    assert result == str(tmp_path / 'file.dat')
    assert calls['save'] is True
    assert calls['savedir'] == str(tmp_path)
    assert calls['return_response_on_save'] is True


def test_download_file_accepts_cached_file_path(monkeypatch, tmp_path):
    filepath = str(tmp_path / 'file.dat')
    monkeypatch.setattr(
        CDDIS, '_request', lambda *args, **kwargs: (filepath, filepath))

    result = CDDIS.download_file('data/daily/file.dat', savedir=str(tmp_path))

    assert result == filepath
