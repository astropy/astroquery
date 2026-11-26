# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Check the SCS integration while keeping real PyVO request and table handling."""

from io import BytesIO
import traceback
from urllib.parse import parse_qs, urlsplit

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import votable
from astropy.table import MaskedColumn, Table
from requests import HTTPError, Timeout
from requests.adapters import HTTPAdapter

from astroquery.exceptions import InvalidQueryError, LoginError, TableParseError
from ..core import LamostClass
from .helpers import create_mock_response


ENDPOINTS = [
    ('dr3', '', 'https://dr3.lamost.org'),
    ('dr6', 'v1', 'https://dr6.lamost.org/v1'),
    ('dr8', 'v2.0', 'https://www.lamost.org/dr8/v2.0'),
    ('dr10', 'v2.0', 'https://www.lamost.org/dr10/v2.0'),
    ('dr13', 'v1.0', 'https://www.lamost.org/dr13/v1.0'),
]


class _Raw(BytesIO):
    def read(self, size=-1, **kwargs):
        return super().read(size)


@pytest.fixture
def scs(monkeypatch):
    state = {'table': Table({'obsid': [1], 'identifier': ['001'], 'ra': [10.] * u.deg,
                             'teff': MaskedColumn([0.], mask=[True])}),
             'response': None, 'requests': []}
    versions = [dict(dr_version=dr, sub_version=sub, base_url=url) for dr, sub, url in ENDPOINTS]
    monkeypatch.setattr(LamostClass, 'get_dr_versions', lambda self: versions)

    def send(adapter, request, **kwargs):
        state['requests'].append((request, kwargs))
        response = state['response']
        if isinstance(response, Exception):
            raise response
        if response is None:
            stream = BytesIO()
            votable.from_table(state['table']).to_xml(stream)
            response = create_mock_response(content=stream.getvalue())
        response.url, response.request, response.raw = request.url, request, _Raw(response.content)
        state['last_response'] = response
        return response

    monkeypatch.setattr(HTTPAdapter, 'send', send)
    return state


@pytest.mark.parametrize('release,version,base', ENDPOINTS)
@pytest.mark.parametrize('resolution,path', [('low', 'voservice'), ('medium', 'medvoservice')])
def test_scs_endpoint_authentication_and_table(release, version, base, resolution, path, scs, tmp_path):
    client = LamostClass(token='synthetic-token', data_release=release, sub_version=version or 'v2.0')
    client.TIMEOUT, client.cache_location = 17, tmp_path
    table = client.query_region(SkyCoord(10, 40, unit='deg'), '5 arcsec', resolution=resolution)
    request, options = scs['requests'][0]
    params = parse_qs(urlsplit(request.url).query)
    assert request.url.split('?')[0] == f'{base}/{path}/conesearch'
    assert params['token'] == ['synthetic-token'] and options['timeout'] == 17
    assert float(params['SR'][0]) == pytest.approx(5 / 3600)
    assert client._session.params == {} and not list(tmp_path.iterdir())
    assert isinstance(table, Table) and table['obsid'].dtype.kind in 'iu'
    assert list(table['identifier']) == ['001'] and table['teff'].mask.tolist() == [True]
    assert table['ra'].unit == u.deg and table.meta['data_release'] == release
    assert scs['last_response'].close.called


def test_preview_anonymous_requests_and_empty_tables(scs):
    client = LamostClass(token='private-token')
    position = SkyCoord(10, 40, unit='deg').galactic
    preview = client.query_region(position, '5 arcsec', get_query_payload=True)
    assert preview['RA'] == pytest.approx(10) and preview['DEC'] == pytest.approx(40)
    assert preview['VERB'] == 2 and preview['token'] == '<redacted>' and not scs['requests']
    client.token = ''
    scs['table'] = scs['table'][:0]
    table = client.query_region(position, '5 arcsec')
    assert len(table) == 0 and table['obsid'].dtype.kind in 'iu'
    assert 'token' not in parse_qs(urlsplit(scs['requests'][0][0].url).query)


@pytest.mark.parametrize('failure,error', [
    ({'status_code': 302, 'headers': {'Location': '/lmusers/user/login'}}, LoginError),
    ({'status_code': 403}, LoginError),
    ({'status_code': 500}, HTTPError),
    ({'content': '<html>not data</html>', 'content_type': 'text/html'}, TableParseError),
    ({'content': '<invalid>'}, TableParseError),
    (Timeout('failed: https://www.lamost.org/?token=private%2Bvo-token'), Timeout),
])
def test_errors_are_preserved_redacted_and_closed(failure, error, scs):
    scs['response'] = create_mock_response(**failure) if isinstance(failure, dict) else failure
    client = LamostClass(token='private+vo-token')
    with pytest.raises(error) as caught:
        client.query_region(SkyCoord(10, 40, unit='deg'), '.1 deg')
    trace = ''.join(traceback.format_exception(caught.value))
    assert 'private+vo-token' not in trace and 'private%2Bvo-token' not in trace
    if 'last_response' in scs:
        assert scs['last_response'].close.called and 'private' not in client.response.url


@pytest.mark.parametrize('url,fmt', [
    ('https://mirror.example/openapi', None),
    ('https://www.lamost.org/openapi', 'csv'),
    ('https://www.lamost.org/openapi', 'json'),
])
def test_openapi_compatibility_is_preserved(url, fmt, scs):
    client = LamostClass(token='')
    client.URL = url
    payload = client.query_region(SkyCoord(10, 40, unit='deg'), '.1 deg',
                                  output_format=fmt, get_query_payload=True)
    assert payload['output.fmt'] == (fmt or 'csv') and not scs['requests']


@pytest.mark.parametrize('radius', [-1 * u.arcsec, np.inf * u.deg, [1, 2] * u.arcsec, 5 * u.m])
def test_invalid_radius_is_rejected_before_request(radius, scs):
    with pytest.raises(InvalidQueryError, match='radius'):
        LamostClass(token='').query_region(SkyCoord(10, 40, unit='deg'), radius)
    assert not scs['requests']


@pytest.mark.parametrize('base', [None, 'http://www.lamost.org/dr10/v2.0', 'https://evil.example'])
def test_unknown_release_and_untrusted_endpoint_are_rejected(base, scs, monkeypatch):
    versions = [] if base is None else [dict(dr_version='dr10', sub_version='v2.0', base_url=base)]
    monkeypatch.setattr(LamostClass, 'get_dr_versions', lambda self: versions)
    with pytest.raises(InvalidQueryError if base is None else TableParseError):
        LamostClass(token='private-token').query_region(SkyCoord(10, 40, unit='deg'), '.1 deg')
    assert not scs['requests']
