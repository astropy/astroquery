# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import importlib
import os
import json
import traceback
from unittest.mock import Mock
from urllib.parse import quote

from astropy import units as u
from astropy.table import Table
import numpy as np
from requests import HTTPError, Request, TooManyRedirects

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


def test_captured_login_redirect(patch_request):
    patch_request(create_mock_response(content=(DATA / 'login_dr7.html').read_bytes(), content_type='text/html'))
    with pytest.raises(LoginError, match='LamostClass'):
        LamostClass(token='').query_sql('SELECT 1')
