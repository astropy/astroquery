# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import gzip
import importlib
import os
import json
import re
import traceback
from unittest.mock import Mock
from urllib.parse import parse_qs, quote, urlsplit

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
import numpy as np
from requests import HTTPError, Request, Response, TooManyRedirects

from .. import conf
from ..core import Lamost, LamostClass
from astroquery.exceptions import (
    InvalidQueryError,
    LoginError,
    RemoteServiceError,
    TableParseError,
)
from .helpers import DATA, create_mock_response


class TestLamost:
    """
    Unit tests for LAMOST query class.
    """

    def test_conftest_import_preserves_environment(self, monkeypatch):
        from . import conftest

        monkeypatch.setenv('ASTROQUERY_LAMOST_TOKEN', 'synthetic-token')
        original = dict(os.environ)
        importlib.reload(conftest)
        assert dict(os.environ) == original

    def test_init_default(self):
        """Test initialization with default parameters"""
        lamost = LamostClass()
        assert lamost.data_release == 'dr10'
        assert lamost.sub_version == 'v2.0'
        assert lamost.URL == 'https://www.lamost.org/openapi'
        assert lamost.token is None

        lamost_dr12 = LamostClass(data_release='dr12', sub_version='v1.0')
        assert lamost_dr12.data_release == 'dr12'
        assert lamost_dr12.sub_version == 'v1.0'

    def test_init_custom(self):
        """Test initialization with custom parameters"""
        lamost = LamostClass(
            token='test_token',
            data_release='dr10',
            sub_version='v1.0'
        )
        assert lamost.token == 'test_token'
        assert lamost.data_release == 'dr10'
        assert lamost.sub_version == 'v1.0'

    def test_config_is_read_when_instance_is_created(self, monkeypatch):
        original = LamostClass()
        with (
            conf.set_temp('server', 'https://mirror.nao.cas.cn/openapi/'),
            conf.set_temp('timeout', 7),
            conf.set_temp('token', 'configured-token'),
        ):
            configured = LamostClass()

        assert configured.URL.rstrip('/') == 'https://mirror.nao.cas.cn/openapi'
        assert configured.TIMEOUT == 7
        assert configured.token == 'configured-token'
        assert original.URL == 'https://www.lamost.org/openapi'
        assert original.TIMEOUT == 60
        assert original.token is None
        assert Lamost.token is None

        request = Mock(return_value=create_mock_response(json_data=[]))
        monkeypatch.setattr(configured, '_request', request)
        configured.query_sql('SELECT obsid FROM combined LIMIT 1')
        assert request.call_args.args[1] == 'https://mirror.nao.cas.cn/openapi/dr10/v2.0/sql'
        assert request.call_args.kwargs['timeout'] == 7
        assert request.call_args.kwargs['params']['token'] == 'configured-token'

    @pytest.mark.parametrize('method, key, unit', [
        ('query_region', 'sr', u.deg),
        ('query_spectra', 'pos', u.arcsec),
        ('query_stellar_parameters', 'pos', u.arcsec),
        ('query_repeat_observations', 'radius', u.deg),
    ])
    @pytest.mark.parametrize('radius', ['5 arcsec', 5 * u.arcsec])
    def test_radius_units(self, spectral_schema, method, key, unit, radius):
        payload = getattr(Lamost, method)(
            coordinates=SkyCoord(10, 40, unit='deg'),
            radius=radius,
            get_query_payload=True,
        )
        value = (np.rad2deg(float(re.search(r'VALUES \(0, 10.0, 40.0, ([^)]+)', payload['sql'])[1])) * 3600
                 if key == 'pos' else payload[key])
        assert value == pytest.approx((5 * u.arcsec).to_value(unit))

    @pytest.mark.parametrize('method, key, value', [
        ('query_region', 'sr', 0.25),
        ('query_spectra', 'pos', 0.25),
        ('query_stellar_parameters', 'pos', 0.25),
        ('query_repeat_observations', 'radius', 0.25),
    ])
    def test_numeric_radius_uses_documented_unit(self, spectral_schema, method, key, value):
        payload = getattr(Lamost, method)(
            coordinates=SkyCoord(10, 40, unit='deg'), radius=value,
            get_query_payload=True,
        )
        actual = (np.rad2deg(float(re.search(r'VALUES \(0, 10.0, 40.0, ([^)]+)', payload['sql'])[1])) * 3600
                  if key == 'pos' else payload[key])
        assert actual == pytest.approx(value)

    @pytest.mark.parametrize('method', [
        'query_region', 'query_spectra',
        'query_stellar_parameters', 'query_repeat_observations',
    ])
    @pytest.mark.parametrize('radius', [
        -1 * u.arcsec, np.nan * u.deg, np.inf * u.deg,
        [1, 2] * u.arcsec, 'invalid angle', 5 * u.m,
    ])
    def test_invalid_radius_has_parameter_error(self, method, radius):
        with pytest.raises(InvalidQueryError, match='radius'):
            getattr(Lamost, method)(
                coordinates=SkyCoord(10, 40, unit='deg'), radius=radius,
                get_query_payload=True,
            )

    @pytest.mark.parametrize('resolution, path', [('low', 'lrs'), ('medium', 'mrs')])
    def test_build_url(self, resolution, path):
        assert LamostClass()._build_url('voservice/conesearch', resolution=resolution) == (
            f'https://www.lamost.org/openapi/dr10/v2.0/{path}/voservice/conesearch'
        )

    def test_build_url_invalid_resolution(self):
        """Invalid resolution values should fail instead of silently using LRS."""
        lamost = LamostClass()
        with pytest.raises(InvalidQueryError, match="resolution must be one of"):
            lamost._build_url('voservice/conesearch', resolution='LOWRES')

    def test_query_region_payload(self):
        """Test cone search query payload construction"""
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_region(
            coord, radius=0.2*u.deg, get_query_payload=True
        )

        assert 'ra' in payload
        assert 'dec' in payload
        assert 'sr' in payload
        assert payload['ra'] == 10.0
        assert payload['dec'] == 40.0
        assert payload['sr'] == 0.2
        assert payload['output.fmt'] == 'csv'

        # Test different output formats with new parameter name
        for fmt in ['json', 'csv', 'votable']:
            payload_new = Lamost.query_region(
                coord, radius=0.2*u.deg, output_format=fmt, get_query_payload=True
            )
            assert payload_new['output.fmt'] == fmt

    def test_query_region_invalid_output_format(self):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        with pytest.raises(InvalidQueryError, match="output_format must be one of"):
            Lamost.query_region(coord, radius=0.2*u.deg, output_format='fits', get_query_payload=True)

    def test_query_sql_payload(self):
        """Test SQL query payload construction"""
        sql = 'SELECT * FROM combined LIMIT 10'
        payload = Lamost.query_sql(sql, get_query_payload=True)

        assert 'sql' in payload
        assert payload['sql'] == sql
        assert payload['output.fmt'] == 'json'

        # Test different output formats
        for fmt in ['votable', 'csv', 'txt']:
            payload_fmt = Lamost.query_sql(sql, output_format=fmt, get_query_payload=True)
            assert payload_fmt['output.fmt'] == fmt

    def test_query_sql_invalid_output_format(self):
        with pytest.raises(InvalidQueryError, match="output_format must be one of"):
            Lamost.query_sql('SELECT 1', output_format='fits', get_query_payload=True)

    @pytest.mark.parametrize('method, args', [
        ('query_catalog', ('combined',)), ('query_spectra', ()), ('query_stellar_parameters', ()),
    ])
    def test_structured_query_row_limit(self, method, args):
        query = getattr(LamostClass(), method)
        assert query(*args, get_query_payload=True)['rows'] == 100
        assert query(*args, max_rows=7, get_query_payload=True)['rows'] == 7

    def test_query_catalog_payload_simple(self):
        """Test catalog query payload construction"""
        payload = Lamost.query_catalog(
            'combined',
            columns=['obsid', 'ra', 'dec'],
            max_rows=10,
            get_query_payload=True
        )

        assert 'rows' in payload
        assert 'showcol' in payload
        assert payload['rows'] == 10
        assert payload['showcol'] == ['obsid', 'ra', 'dec']
        assert payload['output.fmt'] == 'json'

        # Test different output formats
        for fmt in ['votable', 'csv', 'txt']:
            payload_fmt = Lamost.query_catalog(
                'combined',
                columns=['obsid', 'ra', 'dec'],
                max_rows=10,
                output_format=fmt,
                get_query_payload=True
            )
            assert payload_fmt['output.fmt'] == fmt

    def test_query_catalog_payload_with_constraints(self):
        """Test catalog query with column constraints"""
        constraints = [
            {'column_name': 'teff', 'min': 3500, 'max': 3700, 'operation': 'between'}
        ]
        payload = Lamost.query_catalog(
            'combined',
            column_constraints=constraints,
            columns=['obsid', 'teff'],
            max_rows=100,
            get_query_payload=True
        )

        assert 'column_constraints' in payload
        assert payload['column_constraints'] == constraints
        assert 'showcol' in payload

    @pytest.mark.parametrize('kwargs', [
        {'sort_order': 'bogus'}, {'columns': ['obsid', 'obsid']},
    ], ids=['sort-order', 'duplicate-columns'])
    @pytest.mark.parametrize('position', [
        None, {'cone': {'racenter': 10., 'deccenter': 40., 'radius': 5.}},
    ], ids=['native', 'sql'])
    def test_query_catalog_rejects_invalid_inputs_on_both_paths(self, spectral_schema, kwargs, position):
        with pytest.raises(InvalidQueryError, match='sort_order|duplicate'):
            LamostClass().query_catalog(
                'combined', position_constraints=position, get_query_payload=True, **kwargs)

    def test_query_catalog_contains_requires_a_value(self, spectral_schema):
        with pytest.raises(InvalidQueryError, match='contains'):
            LamostClass().query_catalog(
                'combined', column_constraints=[{'column_name': 'obsid', 'operation': 'contains'}],
                position_constraints={'cone': {'racenter': 10., 'deccenter': 40., 'radius': 5.}},
                get_query_payload=True)

    @pytest.mark.parametrize('method', ['query_catalog', 'query_spectra', 'query_stellar_parameters'])
    def test_query_catalog_all_matches_uses_sql(self, monkeypatch, spectral_schema, method):
        request = Mock(return_value=create_mock_response(json_data=[]))
        monkeypatch.setattr(LamostClass, '_request', request)
        if method == 'query_catalog':
            args = ('combined',)
            kwargs = {'position_constraints': {'cone': {
                'racenter': 10., 'deccenter': 40., 'radius': 5., 'cone_nearestonly': False,
            }}}
        else:
            args = (SkyCoord(10, 40, unit='deg'), 5 * u.arcsec)
            kwargs = {'nearest_only': False}
        result = getattr(LamostClass(), method)(*args, columns=['obsid'], max_rows=5, **kwargs)
        assert len(result) == 0
        assert result['obsid'].dtype.kind == 'i'
        sql = request.call_args.kwargs['params']['sql']
        assert 'LIMIT 1' not in sql
        assert sql.endswith('LIMIT 5 OFFSET 0')
        assert request.call_args.args[1].endswith('/sql')

    def test_query_catalog_payload_with_token_separates_body_and_params(self):
        lamost = LamostClass(token='query-token')

        payload = lamost.query_catalog(
            'combined',
            columns=['obsid'],
            max_rows=1,
            get_query_payload=True,
        )

        assert payload['json'] == {
            'rows': 1,
            'page': 1,
            'output.fmt': 'json',
            'order': 'asc',
            'showcol': ['obsid'],
        }
        assert 'token' in payload['params']
        assert 'query-token' not in repr(payload)

    def test_query_spectra_builds_quality_payload(self, spectral_schema):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_spectra(
            coord,
            5 * u.arcsec,
            snr_min=20,
            teff_range=(4500, 6500),
            logg_range=(3.5, 5.0),
            feh_range=(-1.0, 0.5),
            columns=['obsid', 'ra', 'dec', 'snrg', 'teff', 'logg', 'feh'],
            nearest_only=True,
            max_rows=25,
            get_query_payload=True,
        )

        sql = payload['sql']
        assert sql.endswith('LIMIT 25 OFFSET 0')
        assert sql.index('t."snrg" >= 20') < sql.index('LIMIT 1')
        assert 't."teff" >= 4500 AND t."teff" <= 6500' in sql
        assert 't."logg" >= 3.5 AND t."logg" <= 5.0' in sql
        assert 't."feh" >= -1.0 AND t."feh" <= 0.5' in sql
        assert 'degrees(spos(' in sql

    def test_query_stellar_parameters_uses_default_columns(self):
        payload = Lamost.query_stellar_parameters(
            teff_range=(4500, 6500),
            snr_min=30,
            get_query_payload=True,
        )

        assert payload['showcol'] == ['obsid', 'ra', 'dec', 'teff', 'logg', 'feh', 'snrg']
        assert payload['column_constraints'] == [
            {'column_name': 'snrg', 'operation': 'greaterequal', 'constraint': '30'},
            {'column_name': 'teff', 'operation': 'between', 'min': 4500, 'max': 6500},
        ]

    def test_query_stellar_parameters_maps_medium_resolution_fields(self):
        payload = Lamost.query_stellar_parameters(
            resolution='medium',
            teff_range=(4500, 6500),
            logg_range=(3.0, 5.0),
            feh_range=(-1.0, 0.5),
            snr_min=30,
            get_query_payload=True,
        )

        assert payload['showcol'] == [
            'obsid', 'ra', 'dec', 'teff_lasp', 'logg_lasp', 'feh_lasp', 'snr',
        ]
        assert payload['column_constraints'] == [
            {'column_name': 'snr', 'operation': 'greaterequal', 'constraint': '30'},
            {'column_name': 'teff_lasp', 'operation': 'between', 'min': 4500, 'max': 6500},
            {'column_name': 'logg_lasp', 'operation': 'between', 'min': 3.0, 'max': 5.0},
            {'column_name': 'feh_lasp', 'operation': 'between', 'min': -1.0, 'max': 0.5},
        ]

    @pytest.mark.parametrize(
        'query_kwargs, missing_column',
        [
            ({'columns': ['obsid', 'missing']}, 'missing'),
            ({'column_constraints': [{'column_name': 'bad_filter'}]}, 'bad_filter'),
            ({'sort_by': 'bad_sort'}, 'bad_sort'),
        ],
    )
    def test_query_catalog_validates_schema_before_query(
        self, monkeypatch, query_kwargs, missing_column
    ):
        metadata_response = create_mock_response(json_data={
            'tables': {
                'combined': {
                    'columns': ['obsid', 'ra', 'dec', 'teff'],
                },
            },
        })
        requested_urls = []

        def mock_request(self, method, url, **kwargs):
            requested_urls.append(url)
            return metadata_response

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        with pytest.raises(InvalidQueryError, match=missing_column):
            LamostClass().query_catalog('combined', **query_kwargs)

        assert len(requested_urls) == 1
        assert requested_urls[0].endswith('/tables')

    def test_query_catalog_rejects_missing_returned_columns(self, monkeypatch):
        metadata_response = create_mock_response(json_data={
            'tables': {
                'combined': {
                    'columns': ['obsid', 'ra'],
                },
            },
        })
        result_response = create_mock_response(json_data=[{'obsid': '101001'}])

        def mock_request(self, method, url, **kwargs):
            if url.endswith('/tables'):
                return metadata_response
            return result_response

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        with pytest.raises(TableParseError, match='omitted requested column.*ra'):
            LamostClass().query_catalog(
                'combined',
                columns=['obsid', 'ra'],
                max_rows=1,
            )

    def test_query_catalog_converts_values_from_live_schema(self, monkeypatch):
        metadata_response = create_mock_response(json_data={
            'tables': {
                'combined': {
                    'columns': [
                        {'name': 'obsid', 'datatype': 'char'},
                        {'name': 'ra', 'datatype': 'double', 'unit': 'deg'},
                        {'name': 'teff', 'datatype': 'float', 'unit': 'K'},
                    ],
                },
            },
        })
        result_response = create_mock_response(json_data=[{
            'obsid': '00101001',
            'ra': '10.25',
            'teff': '5500.0',
        }])

        def mock_request(self, method, url, **kwargs):
            if url.endswith('/tables'):
                return metadata_response
            return result_response

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        table = LamostClass().query_catalog(
            'combined',
            columns=['obsid', 'ra', 'teff'],
            max_rows=1,
        )

        assert table.colnames == ['obsid', 'ra', 'teff']
        assert table['obsid'][0] == '00101001'
        assert table['ra'].dtype.kind == 'f'
        assert table['teff'].dtype.kind == 'f'
        assert table['ra'].unit == u.deg
        assert table['teff'].unit == u.K

    def test_query_repeat_observations_payload_from_coordinates(self):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_repeat_observations(
            coordinates=coord,
            radius=3 * u.arcsec,
            get_query_payload=True,
        )

        assert payload['ra'] == 10.0
        assert payload['dec'] == 40.0
        assert payload['radius'] == pytest.approx(3 / 3600)

    def test_query_repeat_observations_rejects_ambiguous_target(self):
        with pytest.raises(InvalidQueryError, match="either obsid or coordinates"):
            Lamost.query_repeat_observations(
                obsid='101001',
                coordinates=SkyCoord(10.0, 40.0, unit='deg', frame='icrs'),
                radius=1 * u.arcsec,
            )

    def test_get_metadata_payload(self):
        """Test metadata query payload construction"""
        payload = Lamost.get_metadata(
            '101001',
            resolution='low',
            get_query_payload=True
        )

        assert 'obsid' in payload
        assert payload['obsid'] == '101001'

    def test_get_metadata_returns_json(self, patch_request, spectral_schema):
        response = create_mock_response(
            json_data=[{'obsid': '101001', 'ra': 10.0, 'dec': 40.0}]
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_metadata('101001')

        assert isinstance(result, Table)
        assert result['obsid'][0] == 101001
        assert result['ra'][0] == 10.0

    @pytest.mark.parametrize('output_format', ['votable', 'json'])
    def test_request_query_format(self, patch_request, mock_votable_response, mock_json_response,
                                  output_format):
        response = (create_mock_response(content=mock_votable_response, content_type='application/x-votable+xml')
                    if output_format == 'votable' else create_mock_response(json_data=mock_json_response))
        request = patch_request(response)
        client = LamostClass(token='query-token')
        result = client._request_query_region(
            SkyCoord(10, 40, unit='deg'), radius=.2 * u.deg, output_format=output_format, cache=False,
        )
        assert result is response
        request.assert_called_once_with(
            'GET', 'https://www.lamost.org/openapi/dr10/v2.0/lrs/voservice/conesearch',
            params={'ra': 10., 'dec': 40., 'sr': .2, 'output.fmt': output_format, 'token': 'query-token'},
            json=None, timeout=60, cache=False, stream=False,
        )

    def test_request_query_region_raises_http_error(self, patch_request):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        response = create_mock_response(
            json_data={'error': 'boom'},
            status_code=503,
        )
        patch_request(response)

        lamost = LamostClass()
        with pytest.raises(HTTPError):
            lamost._request_query_region(coord, radius=0.2*u.deg, output_format='json')

    def test_request_rejects_oauth_redirect(self, patch_request):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        response = create_mock_response(
            headers={'Location': 'https://oauth.china-vo.org/login?token=secret'},
        )
        patch_request(response)

        with pytest.raises(LoginError, match='redirected to an OAuth login page'):
            LamostClass(token='secret')._request_query_region(
                coord,
                radius=0.2*u.deg,
                output_format='json',
            )

    def test_request_rejects_json_error_with_text_content_type(self, patch_request):
        response = create_mock_response(
            content=json.dumps({
                'description': 'The SQL service failed.',
                'error': 'Internal Server Error',
            }).encode('utf-8'),
            content_type='text/plain',
        )
        patch_request(response)

        with pytest.raises(RemoteServiceError, match='Internal Server Error'):
            LamostClass().query_sql('SELECT * FROM combined LIMIT 1')


class TestLamostDiagnostics:

    @pytest.mark.parametrize('method, args, kwargs', [
        ('query_region', (), {'coordinates': SkyCoord(10, 40, unit='deg'), 'radius': '5 arcsec'}),
        ('query_sql', ('SELECT obsid FROM combined LIMIT 1',), {}),
        ('query_catalog', ('combined',), {'columns': ['obsid']}),
        ('query_spectra', (), {}),
        ('query_stellar_parameters', (), {}),
        ('query_repeat_observations', (), {'obsid': '101001'}),
        ('get_metadata', ('101001',), {}),
        ('get_spectra', ('101001',), {}),
        ('get_spectrum_list', ('101001',), {}),
    ])
    def test_query_payload_redacts_token(self, method, args, kwargs):
        token = 'synthetic-lamost-token+/='
        payload = getattr(LamostClass(token=token), method)(*args, get_query_payload=True, **kwargs)

        assert token not in repr(payload)
        assert quote(token, safe='') not in repr(payload)

    @pytest.mark.parametrize('status_code, exception', [
        (200, RemoteServiceError), (400, HTTPError), (401, LoginError),
        (403, LoginError), (404, HTTPError),
    ])
    def test_service_errors_preserve_safe_details(self, patch_request, status_code, exception):
        token = 'synthetic-lamost-token+/='
        response = create_mock_response(
            status_code=status_code,
            json_data={'error': 'Bad Request', 'description': f'Unknown selected column; token={token}'},
            url=f'https://example.invalid/sql?token={quote(token, safe="")}',
        )
        response.request.headers['Authorization'] = f'Bearer {token}'
        patch_request(response)

        with pytest.raises(exception) as caught:
            LamostClass(token=token).query_sql('SELECT missing FROM combined')

        assert 'Unknown selected column' in str(caught.value)
        if status_code in (401, 403):
            assert 'conf.token' in str(caught.value) or 'token=' in str(caught.value)
        if status_code == 404:
            assert not isinstance(caught.value, LoginError)
        errors = [caught.value]
        visited = set()
        diagnostics = []
        while errors:
            error = errors.pop()
            if id(error) in visited:
                continue
            visited.add(id(error))
            diagnostics.extend([str(error), repr(vars(error)), ''.join(traceback.format_exception(error))])
            for linked in (error.__context__, error.__cause__):
                if linked is not None:
                    errors.append(linked)
            response = getattr(error, 'response', None)
            if response is not None:
                diagnostics.extend([str(response.url), response.text, repr(dict(response.headers))])
                request = response.request
            else:
                request = getattr(error, 'request', None)
            if request is not None:
                diagnostics.extend([str(request.url), str(request.body), repr(dict(request.headers))])
        assert token not in '\n'.join(diagnostics)
        assert quote(token, safe='') not in '\n'.join(diagnostics)

    def test_debug_logging_redacts_credentials(self, caplog):
        from astroquery import log

        token = 'synthetic-lamost-token+/='
        response = create_mock_response(
            json_data={'message': f'token={token}'},
            url=f'https://example.invalid/sql?token={quote(token, safe="")}',
        )
        response.request = Request(
            'POST', response.url, headers={'Authorization': f'Bearer {token}'},
            json={'token': token, 'sql': 'SELECT obsid FROM combined'},
        ).prepare()
        with caplog.at_level('DEBUG', logger=log.name):
            LamostClass(token=token)._response_hook(response)

        assert caplog.records
        assert token not in caplog.text
        assert quote(token, safe='') not in caplog.text

    def test_parser_diagnostics_redact_credentials(self, patch_request):
        token = 'synthetic-lamost-token+/='
        response = create_mock_response(
            content=f'{{invalid JSON; token={token}'.encode(),
            content_type='application/json',
            url=f'https://example.invalid/sql?token={quote(token, safe="")}',
        )
        patch_request(response)
        lamost = LamostClass(token=token)

        with pytest.raises(TableParseError) as caught:
            lamost.query_sql('SELECT obsid FROM combined')

        diagnostics = '\n'.join([
            ''.join(traceback.format_exception(caught.value)),
            repr(vars(lamost.json_parse_error)),
            lamost.response.text, lamost.response.request.url,
        ])
        assert token not in diagnostics
        assert quote(token, safe='') not in diagnostics

    def test_transport_error_redacts_accessible_exception_chain(self, monkeypatch):
        token = 'synthetic-lamost-token+/='
        request = Request('GET', 'https://example.invalid/sql', params={'token': token}).prepare()
        error = HTTPError(f'Failed request token={token}', request=request)
        error.__cause__ = HTTPError(f'Underlying response token={token}', request=request)
        error.__context__ = HTTPError(f'Original request token={token}', request=request)
        monkeypatch.setattr(LamostClass, '_request', Mock(side_effect=error))

        with pytest.raises(HTTPError) as caught:
            LamostClass(token=token).query_sql('SELECT obsid FROM combined')

        for linked in (caught.value, caught.value.__cause__, caught.value.__context__):
            assert linked is not None
            assert token not in str(linked)
            assert quote(token, safe='') not in linked.request.url

    def test_oauth_stream_diagnostics_do_not_read_body(self, patch_request, tmp_path):
        from urllib3.exceptions import ReadTimeoutError

        token = 'synthetic-stream-token'
        response = Response()
        response.status_code = 302
        response.request = Request('GET', 'https://example.invalid/catalog', params={'token': token}).prepare()
        response.url = response.request.url
        response.headers['Location'] = f'https://oauth.china-vo.org/login?token={token}'
        response.raw = Mock()
        response.raw.stream.side_effect = ReadTimeoutError(None, response.url, f'Interrupted token={token}')
        response.close = Mock(wraps=response.close)
        patch_request(response)
        lamost = LamostClass(token=token)

        with pytest.raises(LoginError) as caught:
            lamost.download_catalog('catalog', save_dir=str(tmp_path))

        response.raw.stream.assert_not_called()
        response.close.assert_called_once()
        response.raw.close.assert_called_once()
        assert token not in ''.join(traceback.format_exception(caught.value))
        assert token not in lamost.response.url
        assert token not in lamost.response.request.url
        assert token not in repr(dict(lamost.response.headers))
        assert lamost.response.raw is None

    def test_redirect_loop_preserves_requests_error(self, monkeypatch):
        from requests.adapters import BaseAdapter
        from astroquery.query import BaseQuery

        token = 'synthetic-redirect-token'
        responses = []

        def redirect_response(request, **kwargs):
            response = create_mock_response(
                status_code=302, headers={'Location': request.url}, url=request.url,
            )
            responses.append(response)
            return response

        lamost = LamostClass(token=token)
        lamost.URL = 'https://redirect.example/openapi'
        adapter = Mock(spec=BaseAdapter)
        adapter.send.side_effect = redirect_response
        lamost._session.mount('https://redirect.example/', adapter)
        lamost._session.max_redirects = 1
        monkeypatch.setattr(LamostClass, '_request', BaseQuery._request)

        with pytest.raises(TooManyRedirects) as caught:
            lamost.query_sql('SELECT 1')

        assert len(responses) == 2
        # Requests versions differ in whether the last history contains itself.
        # The public contract is the preserved, redacted exception below.
        for response in responses:
            response.close.assert_called()
        assert token not in ''.join(traceback.format_exception(caught.value))
        assert token not in caught.value.request.url
        assert token not in caught.value.response.url
        assert caught.value.response.raw is None
        assert caught.value.response.history == []

    def test_diagnostic_response_handles_cyclic_history(self):
        response = create_mock_response(url='https://example.org/?token=synthetic-token')
        response.history = [response]
        diagnostic = LamostClass(token='synthetic-token')._diagnostic_response(response)
        assert diagnostic.history == []
        assert 'synthetic-token' not in diagnostic.url

    def test_diagnostic_headers_stay_case_insensitive(self):
        response = create_mock_response(content_type='text/csv', url='https://example.org/?token=synthetic-token')
        response.request.headers['Authorization'] = 'Bearer synthetic-token'
        diagnostic = LamostClass(token='synthetic-token')._diagnostic_response(response)
        assert diagnostic.headers['content-type'] == 'text/csv'
        assert diagnostic.request.headers['authorization'] == '<redacted>'


class TestLamostConfiguration:
    """
    Test explicit configuration file handling and token detection.
    """

    @pytest.mark.parametrize('content, expected', [
        ('token=test_token_123\n# comment\nother=value', {'token': 'test_token_123', 'other': 'value'}),
        ('token=valid\nmalformed_line\nother=value', {'token': 'valid', 'other': 'value'}),
        ('# comment\ntoken=my_token\n# another\nother=value\n', {'token': 'my_token', 'other': 'value'}),
        ('token=my_token\n\nother=value\n\n', {'token': 'my_token', 'other': 'value'}),
    ], ids=['inline-comment', 'malformed-line', 'comments', 'blank-lines'])
    def test_get_config_contents(self, temp_config_file, content, expected):
        temp_config_file.write_text(content)
        assert LamostClass()._get_config(temp_config_file) == expected

    def test_get_config_file_not_exists(self, temp_config_file):
        """Test when the explicit pylamost.ini path is missing"""
        lamost = LamostClass()
        config = lamost._get_config(temp_config_file)
        assert config is None

    def test_detect_token_from_explicit_config(self, temp_config_file):
        """Test loading token from an explicit pylamost config"""
        temp_config_file.write_text("token=auto_loaded_token")

        lamost = LamostClass(pylamost_config=temp_config_file)
        assert lamost.token == 'auto_loaded_token'

    def test_detect_token_from_conf(self):
        """Test preferring Astroquery config token."""
        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass()

        assert lamost.token == 'conf_token'

    def test_detect_token_from_environment(self, monkeypatch):
        """Test loading token from environment after Astroquery config."""
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        lamost = LamostClass()

        assert lamost.token == 'env_token'

    def test_shared_nadc_token_is_not_used(self, monkeypatch):
        monkeypatch.setenv('ASTROQUERY_NADC_TOKEN', 'shared_token')

        lamost = LamostClass()

        assert lamost.token is None

    def test_default_constructor_does_not_read_pylamost_ini(self, temp_config_file):
        """Test that pylamost.ini is only read when requested."""
        temp_config_file.write_text("token=legacy_token")

        lamost = LamostClass()

        assert lamost.token is None

    def test_detect_token_empty_value(self, temp_config_file):
        """Test when token= is empty"""
        temp_config_file.write_text("token=")

        lamost = LamostClass(pylamost_config=temp_config_file)
        # Empty token should not be set
        assert lamost.token is None

    def test_token_priority(self, temp_config_file):
        """Test that parameter token overrides explicit pylamost config"""
        temp_config_file.write_text("token=config_token")

        lamost = LamostClass(token='param_token', pylamost_config=temp_config_file)
        # Parameter should take precedence
        assert lamost.token == 'param_token'

    def test_empty_parameter_token_disables_config_read(self, monkeypatch, temp_config_file):
        """Test that an explicit empty token blocks later fallback sources."""
        temp_config_file.write_text("token=legacy_token")
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass(token='', pylamost_config=temp_config_file)

        assert lamost.token is None

    def test_conf_token_overrides_explicit_config(self, temp_config_file):
        """Test that conf.token is preferred over explicit pylamost.ini."""
        temp_config_file.write_text("token=legacy_token")

        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass(pylamost_config=temp_config_file)

        assert lamost.token == 'conf_token'

    def test_conf_token_overrides_environment(self, monkeypatch):
        """Test that conf.token is preferred over environment tokens."""
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass()

        assert lamost.token == 'conf_token'

    def test_environment_token_overrides_explicit_config(self, monkeypatch, temp_config_file):
        """Test that environment token is preferred over explicit pylamost.ini."""
        temp_config_file.write_text("token=legacy_token")
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        lamost = LamostClass(pylamost_config=temp_config_file)

        assert lamost.token == 'env_token'


class TestLamostResultParsing:
    """
    Test response parsing for different formats (VOTable, JSON, CSV, TXT).
    """

    @pytest.mark.parametrize('source', [
        'json_schema', 'json_explicit', 'csv_explicit', 'csv_catalog', 'csv_region',
    ])
    def test_numeric_schema_preserves_identifiers(self, monkeypatch, source):
        schema = {
            'obsid': {'datatype': 'long'},
            'gaia_source_id': {'datatype': 'char'},
            'ra': {'datatype': 'double', 'unit': 'deg'},
            'teff': {'datatype': 'float', 'unit': 'K'},
            'feh': {'datatype': 'float', 'unit': 'dex'},
        }
        record = {
            'obsid': '9007199254740993', 'gaia_source_id': '0000123',
            'ra': '10.25', 'teff': '5500.0', 'feh': '-0.2',
        }
        columns = [dict(name=name, **metadata) for name, metadata in schema.items()]
        if source.startswith('csv'):
            content = ','.join(record) + '\n' + ','.join(record.values()) + '\n'
            response = create_mock_response(content=content.encode(), content_type='text/csv')
        elif source == 'json_schema':
            response = create_mock_response(json_data={'columns': columns, 'rows': [record]})
        else:
            response = create_mock_response(json_data=[record])

        def mock_request(self, method, url, **kwargs):
            if url.endswith('/tables'):
                return create_mock_response(json_data={'tables': {'combined': {'columns': columns}}})
            return response

        monkeypatch.setattr(LamostClass, '_request', mock_request)
        lamost = LamostClass()
        if source == 'csv_catalog':
            table = lamost.query_catalog('combined', columns=list(schema), output_format='csv')
            assert table.meta['catalog'] == 'combined'
        elif source == 'csv_region':
            table = lamost.query_region(SkyCoord(10, 40, unit='deg'), '5 arcsec', output_format='csv')
            assert table.meta['catalog'] == 'combined'
        else:
            kwargs = {'column_schema': schema} if source.endswith('explicit') else {}
            table = lamost.query_sql(
                'SELECT obsid, gaia_source_id, ra, teff, feh FROM combined',
                output_format='csv' if source.startswith('csv') else 'json',
                **kwargs,
            )

        assert table['obsid'].dtype.kind in 'iu'
        assert table['obsid'][0] == 9007199254740993
        assert table['gaia_source_id'].dtype.kind in 'SU'
        assert table['gaia_source_id'][0] == '0000123'
        assert table['ra'].unit == u.deg
        assert table['teff'].unit == u.K
        assert table['feh'].unit == u.dex
        assert table['teff'][0] > 5000
        assert table['feh'][0] == pytest.approx(-0.2)

    def test_query_sql_without_schema_keeps_source_types(self, patch_request):
        record = {'obsid': '0000123', 'teff': '5500.0', 'feh': '-0.2', 'selected_count': 2}
        patch_request(create_mock_response(json_data=[record]))

        table = LamostClass().query_sql('SELECT * FROM combined')

        for name, value in record.items():
            assert table[name][0] == value
        assert table['teff'].dtype.kind in 'SU'
        assert table['selected_count'].dtype.kind in 'iu'

    @pytest.mark.parametrize('rows', [[], [{'obsid': None, 'teff': ''}]])
    @pytest.mark.parametrize('embedded_schema', [True, False])
    def test_numeric_schema_empty_and_missing_columns(self, patch_request, rows, embedded_schema):
        schema = {'obsid': {'datatype': 'long'}, 'teff': {'datatype': 'float', 'unit': 'K'}}
        data = {'columns': [dict(name=name, **meta) for name, meta in schema.items()], 'rows': rows}
        patch_request(create_mock_response(json_data=data if embedded_schema else rows))

        kwargs = {} if embedded_schema else {'column_schema': schema}
        table = LamostClass().query_sql('SELECT obsid, teff FROM combined', **kwargs)

        assert len(table) == len(rows)
        assert table['obsid'].dtype.kind in 'iu'
        assert table['teff'].dtype.kind == 'f'
        assert table['teff'].unit == u.K
        if rows:
            assert table['obsid'].mask.tolist() == [True]
            assert table['teff'].mask.tolist() == [True]

    def test_numeric_schema_rejects_invalid_value(self, patch_request):
        patch_request(create_mock_response(json_data=[{'teff': 'not a temperature'}]))

        with pytest.raises(TableParseError, match='teff'):
            LamostClass().query_sql('SELECT teff FROM combined', column_schema={'teff': {'datatype': 'float'}})

    @pytest.mark.parametrize('field, value', [
        ('<FIELD name="value" datatype="date"/>', '2020-01-02'),
        ('<FIELD name="value"></FIELD>', '00101001'),
        ('<FIELD name="value" datatype="char" arraysize=""/>', '00101001'),
    ], ids=['invalid-date', 'missing-datatype', 'empty-arraysize'])
    @pytest.mark.parametrize('with_rows', [False, True], ids=['empty', 'with-values'])
    def test_parse_votable_repairs_preserve_values(self, field, value, with_rows):
        rows = f'<TR><TD>{value}</TD></TR>' if with_rows else ''
        content = f'''<?xml version="1.0"?>
    <VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
      <RESOURCE type="results"><TABLE>{field}
        <DATA><TABLEDATA>{rows}</TABLEDATA></DATA>
      </TABLE></RESOURCE>
    </VOTABLE>'''
        table = LamostClass()._parse_votable_result(
            create_mock_response(content=content, content_type='application/x-votable+xml'),
        )
        assert table.colnames == ['value']
        # Variable-length VOTable strings may use an object column.
        assert table['value'].dtype.kind in 'SUO'
        assert list(table['value']) == ([value] if with_rows else [])

    def test_parse_votable_result_empty(self):
        """Test empty VOTable"""
        empty_votable = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsid" datatype="char" arraysize="*"/>
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

        response = create_mock_response(
            content=empty_votable,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        table = lamost._parse_votable_result(response)
        assert isinstance(table, Table)
        assert len(table) == 0

    def test_parse_votable_result_rejects_arraysize_truncation(self):
        truncated_votable = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsid" datatype="char" arraysize="1"/>
      <DATA><TABLEDATA><TR><TD>101001</TD></TR></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""
        response = create_mock_response(
            content=truncated_votable,
            content_type='application/x-votable+xml',
        )

        with pytest.raises(TableParseError, match='refusing to return truncated data'):
            LamostClass()._parse_votable_result(response)

    def test_parse_votable_result_invalid_xml(self):
        """Test TableParseError on invalid XML"""
        response = create_mock_response(
            content=b'<invalid>xml',
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()

        with pytest.raises(TableParseError):
            lamost._parse_votable_result(response)

    def test_parse_votable_result_rejects_html_error_page(self):
        """Test that HTML/login pages raise a clearer parse error."""
        response = create_mock_response(
            content=b'<!DOCTYPE html><html><head><title>Login</title></head><body>login</body></html>',
            content_type='text/html; charset=utf-8'
        )

        lamost = LamostClass()

        with pytest.raises(TableParseError, match="Server returned HTML instead of a table response"):
            lamost._parse_votable_result(response)

    def test_parse_json_result_dict_with_data(self):
        """Test JSON with 'data' field"""
        json_data = {
            'data': [
                {'obsid': '101001', 'ra': 10.0},
                {'obsid': '101002', 'ra': 10.1}
            ],
            'count': 2
        }

        response = create_mock_response(
            json_data=json_data,
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_json_result(response)

        assert isinstance(table, Table)
        assert len(table) == 2
        assert table['obsid'][0] == '101001'

    def test_parse_json_result_metadata_envelope(self):
        response = create_mock_response(json_data={
            'columns': ['obsid', 'ra'],
            'rows': [
                {'ra': 10.0, 'obsid': '101001'},
                {'ra': 10.1, 'obsid': '101002'},
            ],
            'total': 42,
        })

        table = LamostClass()._parse_json_result(response)

        assert table.colnames == ['obsid', 'ra']
        assert len(table) == 2
        assert table.meta['columns'] == ['obsid', 'ra']
        assert table.meta['total'] == 42

    def test_parse_json_result_rejects_unrecognized_dict(self):
        """An unrecognized envelope must not masquerade as a one-row table."""
        json_data = {'obsid': '101001', 'ra': 10.0, 'dec': 40.0}

        response = create_mock_response(
            json_data=json_data,
            content_type='application/json'
        )

        lamost = LamostClass()
        with pytest.raises(TableParseError):
            lamost._parse_json_result(response)

    def test_parse_json_result_empty(self):
        """Test empty JSON array"""
        response = create_mock_response(
            json_data=[],
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_json_result(response)

        assert isinstance(table, Table)
        assert len(table) == 0

    def test_parse_json_result_invalid(self):
        """Test TableParseError on malformed JSON"""
        response = create_mock_response(
            content=b'{invalid json}',
            content_type='application/json'
        )

        lamost = LamostClass()

        with pytest.raises(TableParseError):
            lamost._parse_json_result(response)

    def test_parse_csv_result_strips_utf8_bom(self):
        response = create_mock_response(
            content='\ufeffinputobjs_dist_arcsec,obsid\n0.25,101001\n'.encode('utf-8'),
            content_type='text/csv',
        )

        table = LamostClass()._parse_csv_result(response)

        assert table.colnames == ['inputobjs_dist_arcsec', 'obsid']
        assert len(table) == 1

    def test_parse_txt_result_valid(self):
        """Test parsing plain text table"""
        txt_content = """# request: ra,dec
obsid\tra\tdec
101001\t10.0\t40.0
101002\t10.1\t40.1"""

        response = create_mock_response(
            content=txt_content.encode('utf-8'),
            content_type='text/plain'
        )

        lamost = LamostClass()
        table = lamost._parse_txt_result(response)

        assert table.colnames == ['obsid', 'ra', 'dec']
        assert len(table) == 2
        assert table['obsid'][0] == 101001

    @pytest.mark.parametrize('output_format', ['json', 'votable', 'csv'])
    def test_parse_result_auto_detect(self, mock_json_response, mock_votable_response,
                                      mock_csv_response, output_format):
        responses = {
            'json': create_mock_response(json_data=mock_json_response),
            'votable': create_mock_response(content=mock_votable_response, content_type='application/x-votable+xml'),
            'csv': create_mock_response(content=mock_csv_response, content_type='text/csv'),
        }
        table = LamostClass()._parse_result(responses[output_format])
        assert isinstance(table, Table)
        assert table.colnames == ['obsid', 'ra', 'dec', 'teff']
        expected_ids = ([101001, 101002, 101003] if output_format == 'csv'
                        else ['101001', '101002', '101003'])
        assert list(table['obsid']) == expected_ids
        for name in ('ra', 'dec', 'teff'):
            np.testing.assert_allclose(table[name], [row[name] for row in mock_json_response])


class TestLamostDataRetrieval:
    """
    Test spectrum and catalog downloads.
    """

    def test_get_spectra_payload(self):
        """Test get_spectra with get_query_payload=True"""
        lamost = LamostClass()
        payload = lamost.get_spectra('101001', resolution='low', get_query_payload=True)

        assert isinstance(payload, dict)
        assert 'obsid' in payload
        assert payload['obsid'] == '101001'

    @pytest.mark.parametrize('resolution, path', [('low', 'lrs'), ('medium', 'mrs')])
    @pytest.mark.parametrize('obsid, token', [('101001', 'test_token'), (686112127, 'synthetic-token+/=')])
    def test_spectrum_urls(self, resolution, path, obsid, token):
        client = LamostClass(token=token, data_release='dr8', sub_version='v1.0')
        urls = client.get_spectrum_list(obsid, resolution=resolution)
        assert len(urls) == 1
        parsed = urlsplit(urls[0])
        assert parsed.scheme == 'https'
        assert parsed.netloc == 'www.lamost.org'
        assert parsed.path == f'/openapi/dr8/v1.0/{path}/spectrum/fits'
        assert parse_qs(parsed.query) == {'obsid': [str(obsid)], 'token': [token]}

    @pytest.mark.parametrize('compressed', [False, True])
    def test_get_spectra_downloads_fits(self, monkeypatch, mock_fits_content, compressed):
        content = gzip.compress(mock_fits_content) if compressed else mock_fits_content
        response = create_mock_response(content=content, content_type='application/fits')
        request = Mock(return_value=response)
        monkeypatch.setattr(LamostClass, '_request', request)

        with conf.set_temp('timeout', 7):
            lamost = LamostClass(token='secret_token')
        result = lamost.get_spectra('101001', resolution='low')

        assert len(result) == 1
        with result[0] as hdul:
            assert isinstance(hdul, fits.HDUList)
            hdul.verify('exception')
            np.testing.assert_array_equal(hdul[0].data, [[1, 2], [3, 4]])
        url = Request('GET', request.call_args.args[1], params=request.call_args.kwargs.get('params')).prepare().url
        assert urlsplit(url).path.endswith('/lrs/spectrum/fits')
        assert parse_qs(urlsplit(url).query) == {'obsid': ['101001'], 'token': ['secret_token']}
        assert request.call_args.kwargs['timeout'] == 7
        assert request.call_args.kwargs['cache'] is False
        response.close.assert_called_once()

    @pytest.mark.parametrize('mode', [
        'success', 'skip', 'http_error', 'oauth', 'iteration_error',
        'write_error', 'invalid_fits',
    ])
    def test_download_catalog_closes_response(
        self, tmp_path, monkeypatch, mock_fits_content, mode
    ):
        destination = tmp_path / 'catalog.fits.gz'
        destination.write_bytes(b'existing content')
        existing_temp = tmp_path / 'catalog.fits.gz.temp'
        existing_temp.write_bytes(b'unrelated existing file')
        content = gzip.compress(mock_fits_content)
        token = 'synthetic-download-token'
        response = create_mock_response(
            content=b'not fits' if mode == 'invalid_fits' else content,
            headers={'Content-Disposition': 'filename="catalog.fits.gz"'},
            status_code=503 if mode == 'http_error' else 200,
        )
        if mode == 'oauth':
            response.headers['Location'] = 'https://oauth.china-vo.org/login'
        if mode == 'iteration_error':
            def interrupted_stream(**kwargs):
                yield b'partial'
                raise OSError(f'Interrupted download token={token}')
            response.iter_content = interrupted_stream
        if mode == 'write_error':
            monkeypatch.setattr('builtins.open', Mock(side_effect=OSError('Disk full')))
        monkeypatch.setattr(LamostClass, '_request', Mock(return_value=response))
        lamost = LamostClass(token=token)

        if mode in {'success', 'skip'}:
            result = lamost.download_catalog(
                'catalog', save_dir=str(tmp_path), overwrite=mode != 'skip'
            )
            assert result == str(destination)
        else:
            exception = {'http_error': HTTPError, 'oauth': LoginError}.get(mode, OSError)
            with pytest.raises(exception) as caught:
                lamost.download_catalog('catalog', save_dir=str(tmp_path), overwrite=True)
            assert token not in str(caught.value)

        response.close.assert_called_once()
        assert existing_temp.read_bytes() == b'unrelated existing file'
        assert set(tmp_path.iterdir()) == {destination, existing_temp}
        if mode == 'success':
            assert destination.read_bytes() == content
            with fits.open(destination) as hdul:
                hdul.verify('exception')
                np.testing.assert_array_equal(hdul[0].data, [[1, 2], [3, 4]])
        else:
            assert destination.read_bytes() == b'existing content'

    @pytest.mark.parametrize('override, expected', [
        (None, 'header_catalog.fits.gz'), ('custom.fits.gz', 'custom.fits.gz'),
    ])
    def test_download_catalog_filename(self, tmp_path, patch_request, mock_fits_content, override, expected):
        content = gzip.compress(mock_fits_content)
        response = create_mock_response(content=content, headers={
            'Content-Disposition': 'attachment; filename="header_catalog.fits.gz"',
        })
        patch_request(response)
        saved = LamostClass().download_catalog('test', save_dir=str(tmp_path), filename=override)
        assert saved == str(tmp_path / expected)
        assert (tmp_path / expected).read_bytes() == content
        assert set(tmp_path.iterdir()) == {tmp_path / expected}
        response.close.assert_called_once()

    def test_download_catalog_rejects_corrupt_fits(self, tmp_path, monkeypatch):
        response = create_mock_response(
            content=b'not a fits product',
            headers={'Content-Disposition': 'filename="corrupt.fits.gz"'},
        )
        monkeypatch.setattr(LamostClass, '_request', Mock(return_value=response))

        with pytest.raises(OSError):
            LamostClass().download_catalog('corrupt', save_dir=str(tmp_path))

        assert not (tmp_path / 'corrupt.fits.gz').exists()
        assert not (tmp_path / 'corrupt.fits.gz.temp').exists()
        response.close.assert_called_once()


class TestLamostDataDiscovery:
    """
    Test metadata and discovery methods.
    """

    @pytest.mark.parametrize('server', [
        'https://mirror.nao.cas.cn/openapi',
        'https://mirror.nao.cas.cn/openapi/',
    ])
    def test_get_dr_versions_preserves_server(self, monkeypatch, server):
        request = Mock(return_value=create_mock_response(json_data={'versions': []}))
        monkeypatch.setattr(LamostClass, '_request', request)
        with conf.set_temp('server', server):
            LamostClass().get_dr_versions()

        assert request.call_args.args[1] == 'https://mirror.nao.cas.cn/openapi/dr_versions'

    def test_get_dr_versions(self, patch_request, mock_dr_versions_response):
        """Test fetching data release versions"""
        response = create_mock_response(
            json_data=mock_dr_versions_response,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        versions = lamost.get_dr_versions()

        assert isinstance(versions, list)
        assert len(versions) == 3
        assert versions[0]['dr_version'] == 'dr10'
        assert versions[0]['sub_version'] == 'v2.0'

        # Validate required fields on all entries
        for v in versions:
            assert 'dr_version' in v
            assert 'sub_version' in v
            assert 'public_status' in v
            assert v['public_status'] in ['public', 'internal']

    def test_get_dr_versions_reports_authentication_error(self, patch_request):
        response = create_mock_response(json_data={'error': 'denied'}, status_code=401)
        patch_request(response)

        lamost = LamostClass()
        with pytest.raises(LoginError, match='(conf.token|token=)'):
            lamost.get_dr_versions()

    @pytest.mark.parametrize('token, cache', [('', True), ('auth-token', False)])
    def test_get_tables_metadata(self, patch_request, token, cache):
        metadata = {'tables': {'combined': {'description': 'Combined catalog', 'columns': ['obsid', 'ra', 'dec']}}}
        request = patch_request(create_mock_response(json_data=metadata))
        result = LamostClass(token=token).get_tables_metadata(cache=cache)
        assert result == metadata
        request.assert_called_once_with(
            'GET', 'https://www.lamost.org/openapi/dr10/v2.0/tables',
            params={'token': token} if token else {}, json=None, timeout=60, cache=cache, stream=False,
        )

    def test_get_tables_metadata_normalizes_list_response(self, patch_request):
        metadata = [
            {
                'table_name': 'combined',
                'description': 'Combined catalog',
                'columns': ['obsid', 'ra', 'dec'],
            },
            {
                'table_name': 'med_combined',
                'description': 'Medium-resolution catalog',
                'columns': ['obsid', 'rv'],
            },
        ]

        response = create_mock_response(json_data=metadata)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_tables_metadata()

        assert list(result.keys()) == ['tables']
        assert 'combined' in result['tables']
        assert result['tables']['combined']['table_name'] == 'combined'
        assert 'med_combined' in result['tables']

    @pytest.mark.parametrize('parameters', [{'obsid': '101001'}, {'ra': 10., 'dec': 40., 'radius': .001}])
    def test_repeat_observations(self, patch_request, parameters):
        data = {'uid': 'U_12345', 'obsid-low': ['101001', '101002'], 'obsid-medium': ['101001']}
        request = patch_request(create_mock_response(json_data=data))
        result = LamostClass(token='id-token').query_repeat_observations(**parameters, cache=False)
        assert result['unique_id'] == data['uid']
        assert result['related_obsids_low'] == data['obsid-low']
        assert result['related_obsids_medium'] == data['obsid-medium']
        assert result['related_obsids'] == ['101001', '101002']
        request.assert_called_once_with(
            'GET', 'https://www.lamost.org/openapi/dr10/v2.0/get_unique_id_and_related_obsids',
            params={**parameters, 'token': 'id-token'}, json=None, timeout=60, cache=False, stream=False,
        )

    def test_repeat_observations_unknown_target(self, patch_request):
        patch_request(create_mock_response(json_data={}))
        assert LamostClass().query_repeat_observations(obsid=0) == {
            'unique_id': None, 'related_obsids': [], 'related_obsids_low': [], 'related_obsids_medium': [],
        }

    def test_repeat_observations_missing_params(self):
        """Test ValueError when neither obsid nor coords"""
        lamost = LamostClass()

        with pytest.raises(ValueError, match="Either 'obsid' OR all of"):
            lamost.query_repeat_observations()

    def test_repeat_observations_normalizes_alternative_keys(self, patch_request):
        unique_id_data = {
            'uid': 'U_ALT',
            'obsid-low': ['101001', '101002'],
            'obsid-medium': ['201001'],
        }

        response = create_mock_response(json_data=unique_id_data)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.query_repeat_observations(obsid='101001')

        assert result['unique_id'] == 'U_ALT'
        assert result['related_obsids'] == ['101001', '101002', '201001']
        assert result['related_obsids_low'] == ['101001', '101002']
        assert result['related_obsids_medium'] == ['201001']


@pytest.mark.parametrize('token', ['', 'synthetic-rejected-token+/='])
@pytest.mark.parametrize('body', [
    '<html><head><META HTTP-EQUIV="refresh" CONTENT="0;URL=https://oauth.china-vo.org/user/login?token={token}">'
    '</head></html>',
    "<html><meta content=\"0; url='https://oauth.china-vo.org/user/login'\" http-equiv='Refresh'></html>",
    '{{"error":"Bad Request","description":"please check your token: {token}"}}',
])
def test_recognized_authentication_bodies(patch_request, token, body):
    # META fixture is constructed from the captured, truncated DR7 response.
    response = create_mock_response(content=body.format(token=token), content_type='application/octet-stream')
    patch_request(response)
    client = LamostClass(token=token)
    with pytest.raises(LoginError) as caught:
        client.query_sql('SELECT 1')
    message = str(caught.value)
    if token:
        assert 'validity' in message and 'permissions' in message
        assert token not in message + client.response.text + ''.join(traceback.format_exception(caught.value))
    else:
        assert 'LamostClass(token=' in message and 'ASTROQUERY_NADC_LAMOST_TOKEN' in message
    response.close.assert_called_once()


@pytest.mark.parametrize('body', [
    '<html><a href="https://oauth.china-vo.org/user/login">login</a></html>',
    '<html><meta http-equiv="refresh" content="0;url=https://oauth.unverified.example/login"></html>',
    '<html><meta http-equiv="refresh" content="0;url=https://oauth.china-vo.org.evil.example/login"></html>',
    '<html><meta http-equiv="refresh" content="0;url=https://[invalid"></html>',
])
def test_html_without_verified_login_redirect_is_not_authentication(patch_request, body):
    patch_request(create_mock_response(content=body))
    with pytest.raises(TableParseError, match='HTML'):
        LamostClass().query_sql('SELECT 1')


def test_authentication_text_in_table_cells_is_data(patch_request):
    value = '<html><meta http-equiv="refresh" content="0;URL=https://oauth.china-vo.org">please check your token'
    patch_request(create_mock_response(json_data=[{'error': value}]))
    assert LamostClass().query_sql('SELECT error FROM sample')['error'][0] == value


@pytest.mark.parametrize('body,expected,message', [
    ((DATA / 'catalog_unknown.json').read_bytes(), RemoteServiceError, 'Not Found'),
    (b'\xef\xbb\xbf \n{"error":"Bad Request","description":"please check your token=synthetic-download-token"}',
     LoginError, 'validity'),
    (b'<html><meta http-equiv="refresh" content="0;URL=https://oauth.china-vo.org/login"></html>',
     LoginError, 'validity'),
    (b'{"broken":', TableParseError, 'catalog'),
    (b'{"data": [1, 2]}', TableParseError, 'catalog'),
    (b'{' + b' ' * (1024 * 1024), TableParseError, 'limit'),
    (b'\xef\xbb\xbf \n', TableParseError, 'empty body'),
], ids=['unknown-product', 'token', 'login-html', 'broken-json', 'json-data', 'oversized-text', 'empty-body'])
@pytest.mark.parametrize('content_type', ['application/octet-stream', 'application/json'])
def test_streamed_catalog_error_preserves_destination(tmp_path, patch_request, body, expected, message, content_type):
    destination = tmp_path / 'catalog.fits.gz'
    destination.write_bytes(b'original product')
    response = Response()
    response.status_code = 200
    response.url = 'https://example.invalid/catalog'
    response.headers['Content-Type'] = content_type
    response.raw = Mock()

    def chunks(*args, **kwargs):
        # Classification must use the completed temporary file, not network chunks.
        yield body[:1]
        yield body[1:7]
        yield body[7:]

    response.raw.stream.side_effect = chunks
    response.close = Mock(wraps=response.close)
    patch_request(response)
    client = LamostClass(token='synthetic-download-token')
    with pytest.raises(expected, match=message) as caught:
        client.download_catalog('catalog', filename=destination.name, save_dir=tmp_path)
    assert client.token not in ''.join(traceback.format_exception(caught.value))
    if hasattr(client, 'response'):
        assert client.token not in client.response.text
    response.raw.stream.assert_called_once()
    response.close.assert_called_once()
    assert response._content is False  # No access to Response.content, even with a JSON content type.
    assert destination.read_bytes() == b'original product'
    assert list(tmp_path.iterdir()) == [destination]


def test_captured_login_redirect(patch_request):
    patch_request(create_mock_response(content=(DATA / 'login_dr7.html').read_bytes(), content_type='text/html'))
    with pytest.raises(LoginError, match='LamostClass'):
        LamostClass(token='').query_sql('SELECT 1')
