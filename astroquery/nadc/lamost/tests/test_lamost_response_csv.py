# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Response classification and lossless CSV character-field regressions."""

import csv
import json
from io import StringIO

from astropy import units as u
from astropy.table import Table
import numpy as np
import pytest

from astroquery.exceptions import TableParseError
from ..core import LamostClass
from .helpers import create_mock_response


HTML = '<!DOCTYPE html>\n<html><body>Service unavailable</body></html>'


def responding_client(monkeypatch, body, content_type, *, token=''):
    response = create_mock_response(content=body, content_type=content_type,
                                    url=f'https://example.invalid/lamost?token={token}')
    client = LamostClass(token=token)
    monkeypatch.setattr(client, '_request', lambda *args, **kwargs: response)
    return client


@pytest.mark.parametrize('body', [HTML, '\ufeff \r\n' + HTML, '  <HTML lang="en">error</HTML>'])
@pytest.mark.parametrize('content_type,output_format', [
    ('text/csv', 'csv'), ('text/plain', 'txt'),
    ('application/json', 'json'), ('application/x-votable+xml', 'votable'),
])
def test_sql_classifies_html_before_format_parsing(monkeypatch, body, content_type, output_format):
    client = responding_client(monkeypatch, body, content_type)
    with pytest.raises(TableParseError, match='HTML'):
        client.query_sql('SELECT obsid FROM catalogue LIMIT 1', output_format=output_format, cache=False)
    assert client.response.status_code == 200
    assert client.response.content == body.encode()


@pytest.mark.parametrize('content_type', ['text/html; charset=utf-8', 'application/xhtml+xml'])
def test_html_media_type_rejects_fragments(monkeypatch, content_type):
    client = responding_client(monkeypatch, '<body>Service unavailable</body>', content_type)
    with pytest.raises(TableParseError, match='HTML'):
        client.query_sql('SELECT obsid FROM catalogue LIMIT 1', cache=False)


@pytest.mark.parametrize('method', ['get_tables_metadata', 'get_dr_versions'])
@pytest.mark.parametrize('body,diagnostic', [
    (HTML, 'HTML'), ('\ufeff\n' + HTML, 'HTML'),
    ('', 'empty response body'), (' \r\n\t', 'empty response body'),
    ('\ufeff \n', 'empty response body'),
])
def test_json_endpoints_diagnose_non_data_responses(monkeypatch, method, body, diagnostic):
    client = responding_client(monkeypatch, body, 'application/json')
    with pytest.raises(TableParseError, match=diagnostic):
        kwargs = {} if method == 'get_dr_versions' else {'cache': False}
        getattr(client, method)(**kwargs)
    assert client.response.headers['Content-Type'] == 'application/json'
    assert client.response.content == body.encode()


@pytest.mark.parametrize('metadata', [False, True])
def test_response_diagnostics_preserve_context_and_redact_credentials(monkeypatch, metadata):
    token = 'synthetic-secret-token'
    body = HTML.replace('Service unavailable', token)
    client = responding_client(monkeypatch, body, 'application/json' if metadata else 'text/csv', token=token)
    with pytest.raises(TableParseError, match='HTML') as caught:
        if metadata:
            client.get_tables_metadata(cache=False)
        else:
            client.query_sql('SELECT obsid FROM catalogue LIMIT 1', cache=False)
    assert '200' in str(caught.value)
    assert 'example.invalid/lamost' in str(caught.value)
    assert str(len(body.encode())) in str(caught.value)
    assert token not in str(caught.value)
    assert token not in client.response.url
    assert token not in client.response.request.url
    assert token.encode() not in client.response.content


@pytest.mark.parametrize('body', ['{"tables": {}}', '[]'])
def test_empty_metadata_structures_remain_valid(monkeypatch, body):
    client = responding_client(monkeypatch, body, 'application/json')
    assert client.get_tables_metadata(cache=False) == {'tables': {}}


@pytest.mark.parametrize('content_type,body', [
    ('application/json', '[{"label": "<html>data</html>"}]'),
    ('text/csv', 'label\n"<html>data</html>"\n'),
])
def test_html_inside_a_data_field_is_valid(monkeypatch, content_type, body):
    client = responding_client(monkeypatch, body, content_type)
    result = client.query_sql('SELECT label FROM sample', cache=False)
    assert result['label'][0] == '<html>data</html>'


@pytest.mark.parametrize('delimiter', [',', '|'])
@pytest.mark.parametrize('with_schema', [False, True])
def test_csv_preserves_character_content_across_logical_records(monkeypatch, delimiter, with_schema):
    values = [
        ' x ', '\tx\t', ' x \r\n y ', 'first\n\n\t \nlast',
        'x\r\r y', '\n', '   ', '\t', '\v', 'x\x85y', 'x\u2028y',
        ' 000123 ', '\ufeffinside', 'a,b|c"d',
    ]
    stream = StringIO(newline='')
    writer = csv.writer(stream, delimiter=delimiter, quoting=csv.QUOTE_ALL)
    writer.writerow([' label ', 'number'])
    for i, value in enumerate(values):
        writer.writerow([value, i])
        stream.write('\r\n')  # Empty records between data rows are ignored.
    client = responding_client(monkeypatch, stream.getvalue(), 'text/csv')
    schema = {'label': {'datatype': 'char'}, 'number': {'datatype': 'long'}} if with_schema else None
    result = client.query_sql('SELECT label,number FROM sample', column_schema=schema, cache=False)
    assert result.colnames == ['label', 'number']
    assert list(result['label']) == values
    np.testing.assert_array_equal(result['number'], np.arange(len(values)))


@pytest.mark.parametrize('body,expected', [
    ('label\n" x "', [' x ']),
    ('label\r\n"x\r\n\r\n y"\r\n', ['x\r\n\r\n y']),
    ('label\n   \n\n\t\n', ['   ', '\t']),
])
def test_single_column_csv_keeps_whitespace_records(monkeypatch, body, expected):
    client = responding_client(monkeypatch, body, 'text/csv')
    result = client.query_sql('SELECT label FROM sample', column_schema={'label': {'datatype': 'char'}}, cache=False)
    assert list(result['label']) == expected


@pytest.mark.parametrize('with_data', [False, True])
def test_multiline_quoted_header(monkeypatch, with_data):
    body = '" label\r\n\r\nunit "' + ('\r\n" x "' if with_data else '')
    client = responding_client(monkeypatch, body, 'text/csv')
    result = client.query_sql('SELECT label FROM sample', cache=False)
    assert result.colnames == ['label\r\n\r\nunit']
    assert len(result) == int(with_data)
    if with_data:
        assert result[result.colnames[0]][0] == ' x '


@pytest.mark.parametrize('body, names', [
    ('obsid,ra\n', ['obsid', 'ra']), ('obsid|ra\n', ['obsid', 'ra']), ('obsid', ['obsid']),
])
def test_header_only_csv_preserves_columns_and_default_types(monkeypatch, body, names):
    client = responding_client(monkeypatch, body, 'text/csv')
    result = client.query_sql('SELECT obsid,ra FROM catalogue LIMIT 0', cache=False)
    assert isinstance(result, Table)
    assert len(result) == 0
    assert result.colnames == names
    assert all(result[name].dtype.kind in 'iu' for name in names)


@pytest.mark.parametrize('delimiter', [',', '|'])
@pytest.mark.parametrize('schema_mode', ['none', 'partial', 'full'])
def test_csv_preserves_numeric_types_units_and_empty_masks(monkeypatch, delimiter, schema_mode):
    stream = StringIO(newline='')
    writer = csv.writer(stream, delimiter=delimiter)
    labels = ['a,b|c "quoted"', 'line one\nline two']
    writer.writerow(['id', 'count', 'temperature', 'label'])
    writer.writerow(['000123', ' 2 ', ' 5770.5 ', labels[0]])
    writer.writerow(['000456', '', '', labels[1]])
    schema = {'id': {'datatype': 'char'}, 'count': {'datatype': 'long'},
              'temperature': {'datatype': 'double', 'unit': 'K'}}
    if schema_mode == 'full':
        schema['label'] = {'datatype': 'char'}
    client = responding_client(monkeypatch, stream.getvalue(), 'text/csv')
    result = client.query_sql('SELECT id,count,temperature,label FROM sample',
                              column_schema=schema if schema_mode != 'none' else None, cache=False)
    assert list(result['label']) == labels
    assert result['count'].dtype.kind in 'iu'
    assert result['count'][0] == 2
    assert result['temperature'].dtype.kind == 'f'
    assert result['temperature'][0] == 5770.5
    assert result['count'].mask[1] and result['temperature'].mask[1]
    if schema_mode != 'none':
        assert list(result['id']) == ['000123', '000456']
        assert result['temperature'].unit == u.K


def test_txt_schema_uses_compatible_string_conversion(monkeypatch):
    client = responding_client(monkeypatch, 'id\ttemperature\n000123\t5770.5\n000456\t\n', 'text/plain')
    result = client.query_sql('SELECT id,temperature FROM sample', output_format='txt', cache=False,
                              column_schema={'id': {'datatype': 'char'},
                                             'temperature': {'datatype': 'double', 'unit': 'K'}})
    assert list(result['id']) == ['000123', '000456']
    assert result['temperature'][0] == 5770.5
    assert result['temperature'].unit == u.K
    assert result['temperature'].mask[1]


@pytest.mark.parametrize('as_json', [False, True])
def test_schema_distinguishes_empty_text_from_whitespace(monkeypatch, as_json):
    body = (json.dumps([{'label': ' \t ', 'number': ' \t '}, {'label': '', 'number': None}]) if as_json
            else 'label,number\n" \t "," \t "\n,\n')
    client = responding_client(monkeypatch, body, 'application/json' if as_json else 'text/csv')
    result = client.query_sql('SELECT label,number FROM sample', cache=False, column_schema={
        'label': {'datatype': 'char'}, 'number': {'datatype': 'long'},
    })
    assert result['label'][0] == ' \t '
    assert result['label'].mask[1]
    assert all(result['number'].mask)
