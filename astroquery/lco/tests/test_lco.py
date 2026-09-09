# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import os
import warnings

import pytest
import requests

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroquery.exceptions import (MaxResultsWarning, NoResultsWarning,
                                   RemoteServiceError)
from astroquery.lco import LcoArchiveQuery
from astroquery.utils.mocks import MockResponse


DATA_FILES = {'frames': 'frames.json',
              'aggregate': 'aggregate.json'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def read_data(name):
    with open(data_path(DATA_FILES[name])) as f:
        return json.load(f)


def nonremote_request(self, method, url, **kwargs):
    name = 'aggregate' if url.endswith('aggregate/') else 'frames'
    with open(data_path(DATA_FILES[name]), 'rb') as f:
        return MockResponse(content=f.read(), url=url)


@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(LcoArchiveQuery, '_request', nonremote_request)
    return mp


@pytest.fixture
def lco():
    return LcoArchiveQuery()


# --- payload construction: no network needed at all -------------------------

def test_query_criteria_payload(lco):
    payload = lco.query_criteria(proposal_id='LCOEPO2014B-010',
                                 site_id='lsc',
                                 reduction_level=91,
                                 get_query_payload=True)
    assert payload == {'proposal_id': 'LCOEPO2014B-010',
                       'site_id': 'lsc',
                       'reduction_level': 91}


def test_query_criteria_drops_none(lco):
    payload = lco.query_criteria(site_id='lsc', target_name=None,
                                 get_query_payload=True)
    assert payload == {'site_id': 'lsc'}


def test_public_is_lowercased_bool(lco):
    assert lco.query_criteria(public=True,
                              get_query_payload=True)['public'] == 'true'
    assert lco.query_criteria(public=False,
                              get_query_payload=True)['public'] == 'false'


def test_exposure_time_quantity_becomes_seconds(lco):
    payload = lco.query_criteria(exposure_time=2*u.min, get_query_payload=True)
    assert payload['exposure_time'] == 120.0


def test_start_end_accept_time_objects(lco):
    from astropy.time import Time
    payload = lco.query_criteria(start=Time('2024-01-01'),
                                 end='2024-02-01', get_query_payload=True)
    assert payload['start'].startswith('2024-01-01')
    assert payload['end'] == '2024-02-01'


# 'PROPID' is one of the upper case names the archive no longer accepts; it
# is rejected the same way any other unknown filter is.
@pytest.mark.parametrize('unknown', ['instrument', 'PROPID'])
def test_unknown_filter_is_rejected(lco, unknown):
    with pytest.raises(ValueError, match="not a supported LCO archive filter"):
        lco.query_criteria(**{unknown: 'x'}, get_query_payload=True)


def test_multi_value_filter_accepts_a_sequence(lco):
    payload = lco.query_criteria(
        exclude_configuration_type=['BIAS', 'DARK'], get_query_payload=True)
    # requests turns a list value into a repeated query parameter, which is
    # what the archive's MultipleChoiceFilter expects.
    assert payload == {'exclude_configuration_type': ['BIAS', 'DARK']}


def test_multi_value_filter_accepts_a_single_value(lco):
    payload = lco.query_criteria(include_configuration_type='BIAS',
                                 get_query_payload=True)
    assert payload == {'include_configuration_type': 'BIAS'}


def test_empty_target_name_is_a_presence_flag(lco):
    # The archive activates this filter for any non-empty value, so a falsy
    # request has to leave the parameter out rather than send 'false'.
    assert lco.query_criteria(empty_target_name=True,
                              get_query_payload=True) == {
        'empty_target_name': 'true'}
    assert lco.query_criteria(empty_target_name=False, site_id='lsc',
                              get_query_payload=True) == {'site_id': 'lsc'}


def test_query_object_matches_exactly_by_default(lco):
    payload = lco.query_object('M101', get_query_payload=True)
    assert payload == {'target_name_exact': 'M101'}


def test_query_object_substring_match(lco):
    payload = lco.query_object('M101', exact=False, get_query_payload=True)
    assert payload == {'target_name': 'M101'}


def test_query_region_without_radius_uses_covers(lco):
    coord = SkyCoord(210.80242917, 54.34875, unit='deg')
    payload = lco.query_region(coord, get_query_payload=True)
    assert payload['covers'] == 'POINT(210.80242917 54.34875)'
    assert 'intersects' not in payload


def test_query_region_with_radius_uses_polygon(lco):
    coord = SkyCoord(210.80242917, 54.34875, unit='deg')
    payload = lco.query_region(coord, radius=0.1*u.deg, get_query_payload=True)
    wkt = payload['intersects']
    assert wkt.startswith('POLYGON((') and wkt.endswith('))')
    # 32 vertices plus the repeated closing vertex.
    assert len(wkt[len('POLYGON(('):-2].split(',')) == 33


def test_query_region_box(lco):
    coord = SkyCoord(0, 0, unit='deg')
    payload = lco.query_region(coord, width=1*u.deg, height=2*u.deg,
                               get_query_payload=True)
    assert payload['intersects'].startswith('POLYGON((')


def test_query_region_rejects_radius_and_box(lco):
    coord = SkyCoord(0, 0, unit='deg')
    with pytest.raises(ValueError, match="not both"):
        lco.query_region(coord, radius=1*u.deg, width=1*u.deg, height=1*u.deg,
                         get_query_payload=True)


def test_query_region_requires_both_box_sides(lco):
    coord = SkyCoord(0, 0, unit='deg')
    with pytest.raises(ValueError, match="Both 'width' and 'height'"):
        lco.query_region(coord, width=1*u.deg, get_query_payload=True)


@pytest.mark.parametrize('row_limit', [0, -2])
def test_meaningless_row_limit_is_rejected(lco, row_limit):
    with pytest.raises(ValueError, match="'row_limit' must be 1 or more"):
        lco.query_criteria(site_id='lsc', row_limit=row_limit,
                           get_query_payload=True)


def test_bad_thumbnail_size(lco):
    with pytest.raises(ValueError, match="thumbnail_size"):
        lco.query_criteria(site_id='lsc', thumbnail_size='enormous',
                           get_query_payload=True)


# --- parsing, against a saved archive response ------------------------------

def test_query_returns_table(patch_request, lco):
    result = lco.query_object('TEST-TARGET', row_limit=2)
    assert isinstance(result, Table)
    assert len(result) == 2
    assert result['target_name'][0] == 'TEST-TARGET'
    assert result['exposure_time'].unit == u.s


def test_deprecated_columns_are_dropped(patch_request, lco):
    result = lco.query_object('TEST-TARGET', row_limit=2)
    assert 'PROPID' not in result.colnames
    assert 'proposal_id' in result.colnames


def test_nested_fields_are_dropped(patch_request, lco):
    result = lco.query_object('TEST-TARGET', row_limit=2)
    for column in ('area', 'version_set', 'related_frames'):
        assert column not in result.colnames


def test_thumbnail_columns(patch_request, lco):
    result = lco.query_object('TEST-TARGET', row_limit=2,
                              include_thumbnails=True, thumbnail_size='small')
    assert 'thumbnail_url' in result.colnames
    assert result['thumbnail_filename'][0].endswith('-small_thumbnail.jpg')

    result = lco.query_object('TEST-TARGET', row_limit=2,
                              include_thumbnails=True, thumbnail_size='large')
    assert result['thumbnail_filename'][0].endswith('-large_thumbnail.jpg')


def test_empty_result_warns(patch_request, lco, monkeypatch):
    def empty_request(self, method, url, **kwargs):
        return MockResponse(content=json.dumps({'results': [],
                                                'next': None}).encode(),
                            url=url)

    monkeypatch.setattr(LcoArchiveQuery, '_request', empty_request)
    with pytest.warns(NoResultsWarning):
        result = lco.query_object('nothing-matches-this')
    assert len(result) == 0
    assert 'basename' in result.colnames


def test_list_helpers(patch_request, lco):
    assert lco.list_sites() == sorted(read_data('aggregate')['sites'])
    assert lco.list_configuration_types() == sorted(
        read_data('aggregate')['obstypes'])


def test_download_drops_the_auth_header(lco, monkeypatch, tmp_path):
    # S3 rejects a presigned URL that also carries an Authorization header
    # with "Only one auth mechanism allowed", so an authenticated session
    # must not send its token to the download host.
    seen = {}

    def record_headers(self, url, local_filepath, **kwargs):
        seen.update(kwargs.get('headers') or {})
        return local_filepath

    monkeypatch.setattr(LcoArchiveQuery, '_download_file', record_headers)
    lco._session.headers['Authorization'] = 'Token sekrit'

    frames = Table({'filename': ['a.fits.fz'], 'url': ['https://s3/a?X-Amz-Signature=x']})
    lco.download_files(frames, download_dir=str(tmp_path))

    assert seen['Authorization'] is None
    # The session itself keeps the token for further queries.
    assert lco._session.headers['Authorization'] == 'Token sekrit'


def test_expired_download_link_explains_itself(lco, monkeypatch, tmp_path):
    def expired(self, url, local_filepath, **kwargs):
        response = requests.Response()
        response.status_code = 403
        raise requests.exceptions.HTTPError(response=response)

    monkeypatch.setattr(LcoArchiveQuery, '_download_file', expired)
    frames = Table({'filename': ['a.fits.fz'], 'url': ['https://expired']})
    with pytest.raises(RemoteServiceError, match='has expired'):
        lco.download_files(frames, download_dir=str(tmp_path))


def test_other_download_errors_are_not_swallowed(lco, monkeypatch, tmp_path):
    def not_found(self, url, local_filepath, **kwargs):
        response = requests.Response()
        response.status_code = 404
        raise requests.exceptions.HTTPError(response=response)

    monkeypatch.setattr(LcoArchiveQuery, '_download_file', not_found)
    frames = Table({'filename': ['a.fits.fz'], 'url': ['https://missing']})
    with pytest.raises(requests.exceptions.HTTPError):
        lco.download_files(frames, download_dir=str(tmp_path))


def test_download_thumbnails_requires_the_column(lco):
    # A table from a query that did not ask for thumbnails has no links to
    # download, and should say so rather than failing later.
    with pytest.raises(ValueError, match="include_thumbnails=True"):
        lco.download_thumbnails(Table({'id': [1], 'basename': ['a']}))


# --- authentication ---------------------------------------------------------

def test_login_with_token_sets_header(lco, monkeypatch):
    def fake_request(self, method, url, **kwargs):
        assert url.endswith('/profile/')
        return MockResponse(content=json.dumps({'username': 'jnation'}).encode(),
                            url=url)

    monkeypatch.setattr(LcoArchiveQuery, '_request', fake_request)
    lco.login(token='sekrit')
    assert lco._session.headers['Authorization'] == 'Token sekrit'
    assert lco.authenticated()

    lco.logout()
    assert 'Authorization' not in lco._session.headers
    assert not lco.authenticated()


def test_bad_token_is_rejected_and_header_removed(lco, monkeypatch):
    def anonymous_profile(self, method, url, **kwargs):
        return MockResponse(content=json.dumps({'username': ''}).encode(),
                            url=url)

    monkeypatch.setattr(LcoArchiveQuery, '_request', anonymous_profile)
    lco.login(token='wrong')
    assert not lco.authenticated()
    assert 'Authorization' not in lco._session.headers


def test_login_needs_token_or_username(lco):
    from astroquery.exceptions import LoginError
    with pytest.raises(LoginError):
        lco.login()


def test_page_size_depends_on_auth(lco):
    assert lco._page_size == 100
    lco._authenticated = True
    assert lco._page_size == 1000


def test_authenticated_queries_are_not_cached(lco, monkeypatch):
    seen = {}

    def record_cache(self, method, url, **kwargs):
        seen['cache'] = kwargs.get('cache')
        return MockResponse(content=json.dumps({'results': [],
                                                'next': None}).encode(),
                            url=url)

    monkeypatch.setattr(LcoArchiveQuery, '_request', record_cache)

    with pytest.warns(NoResultsWarning):
        lco.query_object('TEST-TARGET')
    assert seen['cache'] is True

    lco._authenticated = True
    with pytest.warns(NoResultsWarning):
        lco.query_object('TEST-TARGET')
    assert seen['cache'] is False


def paged_request(pages):
    """Serve a canned sequence of pages, one per request."""
    served = iter(pages)

    def request(self, method, url, **kwargs):
        return MockResponse(content=json.dumps(next(served)).encode(), url=url)

    return request


def test_truncation_warns(lco, monkeypatch):
    rows = read_data('frames')['results']
    # One page that fills the row limit, with more waiting behind it.
    monkeypatch.setattr(LcoArchiveQuery, '_request', paged_request(
        [{'results': rows, 'next': 'https://archive-api.lco.global/frames/'
                                   '?cursor=TESTCURSOR&limit=2'}]))

    with pytest.warns(MaxResultsWarning, match='truncated to 2 frames'):
        result = lco.query_object('TEST-TARGET', row_limit=2)
    assert len(result) == 2


def test_no_truncation_warning_when_the_archive_is_exhausted(lco, monkeypatch):
    rows = read_data('frames')['results']
    monkeypatch.setattr(LcoArchiveQuery, '_request', paged_request(
        [{'results': rows, 'next': None}]))

    warnings.simplefilter('error')
    result = lco.query_object('TEST-TARGET', row_limit=2)
    assert len(result) == 2


def test_no_truncation_warning_when_unlimited(lco, monkeypatch):
    rows = read_data('frames')['results']
    monkeypatch.setattr(LcoArchiveQuery, '_request', paged_request(
        [{'results': rows, 'next': 'https://archive-api.lco.global/frames/'
                                   '?cursor=TESTCURSOR&limit=2'},
         {'results': rows, 'next': None}]))

    warnings.simplefilter('error')
    result = lco.query_object('TEST-TARGET', row_limit=-1)
    assert len(result) == 4


def test_cursor_pagination_is_requested(lco, monkeypatch):
    seen = {}

    def record_params(self, method, url, **kwargs):
        seen.update(kwargs.get('params') or {})
        return MockResponse(content=json.dumps({'results': [],
                                                'next': None}).encode(),
                            url=url)

    monkeypatch.setattr(LcoArchiveQuery, '_request', record_params)
    with pytest.warns(NoResultsWarning):
        lco.query_object('TEST-TARGET', row_limit=10)

    assert seen['pagination_style'] == 'cursor'
    assert seen['limit'] == 10
