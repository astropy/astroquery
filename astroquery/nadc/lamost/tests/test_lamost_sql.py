# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Regressions for archive compatibility; HTTP responses are deliberately small."""

from io import BytesIO
import gzip
from unittest.mock import Mock

import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table

from ..core import LamostClass
from .._sql import catalog_sql, spectral_catalog
from ....exceptions import InvalidQueryError, LoginError, RemoteServiceError, TableParseError
from .helpers import create_mock_response


def test_raw_sql_response_is_not_parsed_or_redacted(patch_request):
    response = create_mock_response(content=b'<broken>raw response\x00\xff synthetic-token', content_type='text/csv')
    patch_request(response)
    client = LamostClass(token='synthetic-token')
    raw = client.query_sql_async('SELECT 1')
    assert raw is response
    assert raw.content.endswith(b'\x00\xff synthetic-token')
    with pytest.raises(TableParseError):
        client.query_sql('SELECT 1')
    assert 'synthetic-token' not in repr(client.response.content)


@pytest.mark.parametrize('release, version, expected', [
    ('dr3', 'v2.0', 'csv'), ('dr8', 'v1.0', 'csv'), ('dr10', 'v2.0', 'json'),
])
def test_sql_default_format_respects_release_and_explicit_choice(release, version, expected):
    client = LamostClass(data_release=release, sub_version=version)
    payload = client.query_sql_async('SELECT 1', get_query_payload=True)
    assert payload['output.fmt'] == expected
    explicit = 'json' if expected == 'csv' else 'csv'
    payload = client.query_sql('SELECT 1', output_format=explicit, get_query_payload=True)
    assert payload['output.fmt'] == explicit


@pytest.mark.parametrize('release, version, resolution, stellar, expected', [
    ('dr3', 'v2.0', 'low', False, 'catalogue'),
    ('dr3', 'v2.0', 'low', True, 'stellar'),
    ('dr6', 'v1.1', 'medium', False, 'med_catalogue'),
    ('dr6', 'v1.1', 'medium', True, 'med_stellar'),
    ('dr10', 'v2.0', 'medium', True, 'med_combined'),
])
def test_catalog_population(release, version, resolution, stellar, expected):
    assert spectral_catalog(release, version, resolution, stellar=stellar) == expected


def test_unknown_release_does_not_guess_catalog():
    with pytest.raises(InvalidQueryError, match='No verified default catalog'):
        LamostClass(data_release='dr99').query_stellar_parameters(get_query_payload=True)


def test_proximity_preserves_input_lines_and_filters_before_nearest(spectral_schema):
    client = LamostClass(token='private-token')
    payload = client.query_catalog(
        'combined', columns=['obsid', 'teff'], max_rows=3,
        position_constraints={'proximity': {'radecTextarea': '# targets\nra, dec, radius\n10, 40, 720\n10, 40, 720',
                                            'proximity_nearestonly': True}},
        column_constraints=[{'column_name': 'teff', 'operation': 'between', 'min': 4500, 'max': 6500}],
        get_query_payload=True,
    )
    sql = payload['sql']
    assert '(3, 10.0, 40.0,' in sql and '(4, 10.0, 40.0,' in sql
    assert sql.index('t."teff" <= 6500') < sql.index('LIMIT 1')
    assert 'inputobjs_input_line' in sql
    assert sql.endswith('LIMIT 3 OFFSET 0')
    assert 'private-token' not in repr(payload)


@pytest.mark.parametrize('value', ['0); DROP TABLE stellar; --', 'NaN', float('inf'), '1.2'])
def test_sql_numeric_values_are_not_sql_fragments(spectral_schema, value):
    with pytest.raises(InvalidQueryError, match='finite long'):
        LamostClass().query_catalog(
            'combined',
            column_constraints=[{'column_name': 'obsid', 'operation': 'equal', 'constraint': value}],
            position_constraints={'cone': {'racenter': 10, 'deccenter': 40, 'radius': 720}},
            get_query_payload=True)


def test_sql_escapes_strings_and_pages_without_deduplication():
    sql, _ = catalog_sql('med_catalogue', {'obsid': {'datatype': 'long'}, 'name': {'datatype': 'text'}},
                         constraints=[{'column_name': 'name', 'operation': 'equal', 'constraint': "a'\\b"}],
                         position=None, columns=['obsid'], sort_by='obsid', sort_order='asc', max_rows=7, page=4)
    assert "E'a''\\\\b'" in sql
    assert sql.endswith('LIMIT 7 OFFSET 21')
    assert 'DISTINCT' not in sql


@pytest.mark.parametrize('kwargs', [
    {'nearest_only': 'False'}, {'nearest_only': True, 'page': 2},
    {'page': 0}, {'max_rows': True},
])
def test_invalid_query_parameters(spectral_schema, kwargs):
    with pytest.raises(InvalidQueryError):
        LamostClass().query_stellar_parameters(SkyCoord(10, 40, unit='deg'), '5 arcsec',
                                               get_query_payload=True, **kwargs)


@pytest.mark.parametrize('count, error', [
    (0, None), (1, TableParseError), (None, TableParseError),
    ({'error': 'permission denied'}, RemoteServiceError),
])
def test_only_verified_empty_generated_page_is_a_typed_table(spectral_schema, monkeypatch, count, error):
    def respond(method, url, *, params, **kwargs):
        if params['sql'].startswith('SELECT COUNT(*)'):
            assert 'LIMIT 2 OFFSET 4' in params['sql']
            if isinstance(count, dict):
                return create_mock_response(json_data=count)
            return create_mock_response(content='' if count is None else f'n\n{count}\n', content_type='text/csv')
        return create_mock_response(content=b'', content_type='text/csv')
    request = Mock(side_effect=respond)
    monkeypatch.setattr(LamostClass, '_request', request)

    def call():
        return LamostClass().query_stellar_parameters(
            SkyCoord(10, 40, unit='deg'), '5 arcsec', max_rows=2, page=3)
    if error:
        with pytest.raises(error):
            call()
    else:
        table = call()
        assert len(table) == 0 and table['obsid'].dtype.kind == 'i'
        assert table['teff'].dtype.kind == 'f'
    assert request.call_count == 2


@pytest.mark.parametrize('status, body, expected', [
    (403, b'denied', LoginError), (200, b'{"error":"permission denied"}', RemoteServiceError),
    (200, b'{"error":"Unauthorized"}', LoginError),
])
def test_legacy_metadata_does_not_hide_permission_failures(patch_request, status, body, expected):
    request = patch_request(create_mock_response(content=body, status_code=status))
    with pytest.raises(expected):
        LamostClass(data_release='dr3').get_tables_metadata()
    assert request.call_count == 1


def test_legacy_metadata_uses_visible_relations(patch_request):
    request = patch_request(create_mock_response(content='table_name,column_name,datatype\nstellar,obsid,bigint\n',
                                                 content_type=None))
    metadata = LamostClass(data_release='dr3').get_tables_metadata()
    assert metadata['tables']['stellar']['columns']['obsid']['datatype'] == 'bigint'
    assert 'pg_table_is_visible(c.oid)' in request.call_args.kwargs['params']['sql']
    assert request.call_args.args[1] == 'https://dr3.lamost.org/sql/q'


@pytest.mark.parametrize('body, empty', [
    ('observed,accepted\n2019-01-01,False\n', False), ('observed,accepted\n', True),
])
def test_legacy_date_and_boolean_types_including_empty_tables(patch_request, body, empty):
    patch_request(create_mock_response(content=body, content_type='text/csv'))
    table = LamostClass().query_sql('SELECT observed,accepted FROM sample', column_schema={
        'observed': {'datatype': 'date'}, 'accepted': {'datatype': 'boolean'}})
    assert table['observed'].dtype.kind == 'U' and table['accepted'].dtype.kind == 'b'
    assert len(table) == (0 if empty else 1)
    if not empty:
        assert not table['accepted'][0]


def test_legacy_spectrum_metadata_is_a_row(monkeypatch, patch_request):
    response = create_mock_response(json_data={'response': [
        {'what': 'obsid', 'action': '', 'data': '205208022'},
        {'what': 'teff', 'action': '', 'data': ''},
    ]})
    request = patch_request(response)
    monkeypatch.setattr(LamostClass, 'get_tables_metadata', lambda self, **k: {'tables': {
        'stellar': {'columns': {'obsid': {'datatype': 'bigint'}, 'teff': {'datatype': 'double'}}}}})
    table = LamostClass(data_release='dr3').get_metadata(205208022)
    assert table.colnames == ['obsid', 'teff']
    assert table['obsid'][0] == 205208022
    assert np.ma.is_masked(table['teff'][0])
    assert request.call_args.args[1].endswith('/spectrum/info/205208022')


@pytest.mark.parametrize('content_type', ['text/csv', None])
def test_actual_votable_format_and_missing_integer(content_type):
    response = create_mock_response(content=b'''<VOTABLE version="1.2"><RESOURCE><TABLE>
      <FIELD name="count" datatype="int"/><DATA><TABLEDATA>
      <TR><TD>0</TD></TR><TR><TD/></TR></TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>''', content_type=content_type)
    client = LamostClass()
    # Reliably mapped empty scalar cells now receive masks, including VOTable 1.2.
    table = client._parse_table_response(response)
    assert np.ma.getmaskarray(table['count']).tolist() == [False, True]
    assert table['count'][0] == 0
    response._content = response.content.replace(b'version="1.2"', b'version="1.3"')
    table = client._parse_table_response(response)
    assert np.ma.is_masked(table['count'][1])
    assert not np.ma.is_masked(table['count'][0])
    response._content = response.content.replace(b'<TR><TD/></TR>', b'<TR><TD>2</TD></TR>')
    table = client._parse_table_response(response)
    assert list(table['count']) == [0, 2]


def test_dr3_plan_is_validated_as_gzip_csv(tmp_path, patch_request):
    content = gzip.compress(b'pid,planid,ra,dec\n1,test,10,40\n')
    request = patch_request(create_mock_response(content=content, content_type=None))
    path = LamostClass(data_release='dr3').download_catalog('plan', save_dir=tmp_path)
    assert path.endswith('dr3_plan.csv.gz')
    with gzip.open(path) as stream:
        assert len(Table.read(BytesIO(stream.read()), format='ascii.csv')) == 1
    assert request.call_args.args[1] == 'https://dr3.lamost.org/catdl'
