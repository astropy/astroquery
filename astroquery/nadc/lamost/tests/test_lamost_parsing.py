# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Regression cases from historical LAMOST table responses."""

from pathlib import Path
import json

from astropy import units as u
from astropy.table import Table
import numpy as np
import pytest

from astroquery.exceptions import LoginError, TableParseError
from ..core import LamostClass
from .helpers import create_mock_response


DATA = Path(__file__).parent / 'data'


@pytest.mark.parametrize('body', [b'', b' \t\r\n', b'\xef\xbb\xbf \n'])
@pytest.mark.parametrize('content_type', ['text/csv', 'text/plain', 'application/json', 'application/x-votable+xml'])
def test_blank_response_is_not_a_zero_row_table(body, content_type):
    client = LamostClass(token='')
    with pytest.raises(TableParseError, match='empty response body'):
        client._parse_result(create_mock_response(content=body, content_type=content_type))
    assert client.response.content == body


@pytest.mark.parametrize('body,names,values', [
    ('name,value\nA|B,2\n', ['name', 'value'], ['A|B', 2]),
    ('name|value\nA,B|2\n', ['name', 'value'], ['A,B', 2]),
    ('"name|unit",value\n"A|B",2\n', ['name|unit', 'value'], ['A|B', 2]),
    ('"name,unit"|value\n"A,B"|2\n', ['name,unit', 'value'], ['A,B', 2]),
    ('"name|unit"\n"A|B"\n', ['name|unit'], ['A|B']),
    ('name\nA|B\n', ['name'], ['A|B']),
])
def test_delimiter_evidence_comes_from_header(body, names, values):
    result = LamostClass(token='')._parse_csv_result(create_mock_response(content=body.encode()))
    assert result.colnames == names
    assert list(result[0]) == values


@pytest.mark.parametrize('body, diagnostic', [
    ('id,ra|dec\n1,2|3\n', 'Ambiguous table header'),
    ('id|ra|dec\n1|2\n', 'has 2 fields; expected 3'),
    ('id,ra,dec\n1,2\n', 'has 2 fields; expected 3'),
    ('id,ra\n1,2,3\n', 'has 3 fields; expected 2'),
    ('id|id\n1|2\n', 'empty or duplicate column names'),
    ('id,,dec\n1,2,3\n', 'empty or duplicate column names'),
    ('id|ra\n1|"unterminated\n', 'unexpected end of data'),
    ('id,ra\n1,"quoted"junk\n', 'expected after'),
])
def test_damaged_or_ambiguous_csv_is_rejected(body, diagnostic):
    with pytest.raises(TableParseError, match=diagnostic):
        LamostClass(token='')._parse_csv_result(create_mock_response(content=body.encode()))


@pytest.mark.parametrize('name,rows,columns', [('med_catalogue', 10, 6), ('med_stellar', 1, 80)])
def test_preserved_historical_sql_response(name, rows, columns):
    response = create_mock_response(content=(DATA / f'{name}_dr8.txt').read_bytes(), content_type='text/csv')
    schema = {'obsid': {'datatype': 'long'}, 'rv_br0': {'datatype': 'double', 'unit': 'km/s'}}
    if name == 'med_stellar':
        schema['gaia_source_id'] = {'datatype': 'char'}
    result = LamostClass(token='')._parse_result(response, column_schema=schema)
    assert len(result) == rows
    assert len(result.colnames) == columns
    assert set(result['obsid']) == {635003103}
    assert result['rv_br0'].unit == u.km / u.s
    assert result['rv_br0'][0] == (-3.97 if name == 'med_catalogue' else -1.08)
    if name == 'med_stellar':
        assert result['gaia_source_id'][0] == '3700975728440669184'
        assert result['mobsid'][0] == '635003103R'


@pytest.mark.parametrize('rows', [[], [
    {'obsid': 635003103, 'band': 'B', 'lmjm': 1},
    {'obsid': 635003103, 'band': 'R', 'lmjm': 1},
]])
def test_json_records_without_column_definitions(rows):
    # Constructed from the observed DR8 MRS info envelope, not captured HTTP bytes.
    table = LamostClass()._parse_result(create_mock_response(json_data={'rows': rows, 'total': len(rows)}))
    assert len(table) == len(rows)
    assert table.meta['total'] == len(rows)
    assert 'total' not in table.colnames
    assert [dict(row) for row in table] == rows
    if not rows:
        assert table.colnames == []


@pytest.mark.parametrize('data', [{'rows': {}}, {'rows': [1]}, {'rows': [[1, 2]]}, {'unexpected': 1}])
def test_unrecognized_json_tables_are_rejected(data):
    with pytest.raises(TableParseError):
        LamostClass()._parse_result(create_mock_response(json_data=data))


@pytest.mark.parametrize('envelope', ['list', 'data', 'rows', 'columns'])
def test_json_nulls_are_masked_without_guessing_types(envelope):
    rows = [{'id': '0001', 'value': 2, 'empty': None}, {'id': None, 'value': None, 'empty': None}]
    data = rows if envelope == 'list' else {('data' if envelope == 'data' else 'rows'): rows}
    if envelope == 'columns':
        data['columns'] = list(rows[0])
    table = LamostClass()._parse_result(create_mock_response(json_data=data))
    assert table['id'][0] == '0001'
    assert table['value'][0] == 2
    for name in ('id', 'value'):
        assert np.ma.getmaskarray(table[name]).tolist() == [False, True]
    assert np.ma.getmaskarray(table['empty']).all()


@pytest.mark.parametrize('resolution,filename,catalog', [
    ('low', 'info_lrs_dr10.json', 'combined'), ('medium', 'info_mrs_dr10.json', 'med_combined'),
])
def test_metadata_matches_captured_catalog_schema(monkeypatch, patch_request, resolution, filename, catalog):
    metadata = json.loads((DATA / 'schema_dr10.json').read_bytes())
    data = json.loads((DATA / filename).read_bytes())
    schema = metadata['tables'][catalog]['columns']
    assert set(data['rows'][0]) == set(schema)
    monkeypatch.setattr(LamostClass, 'get_tables_metadata', lambda self, **kwargs: metadata)
    patch_request(create_mock_response(json_data=data))
    table = LamostClass().get_metadata(data['rows'][0]['obsid'], resolution=resolution, cache=False)
    assert len(table) == len(data['rows'])
    for name, definition in schema.items():
        kind = definition['datatype']
        caster = {'long': int, 'int': int, 'double': float, 'char': str, 'date': str}.get(kind)
        if caster:
            assert table[name].dtype.kind in ('iu' if caster is int else 'f' if caster is float else 'SU')
        for i, row in enumerate(data['rows']):
            value = row[name]
            if value in (None, ''):
                assert np.ma.is_masked(table[name][i])
            else:
                assert not np.ma.is_masked(table[name][i])
                expected = caster(value) if caster else value
                assert table[name][i] == expected


def test_metadata_unknown_release_keeps_raw_types(patch_request):
    request = patch_request(create_mock_response(json_data=[{'obsid': 1, 'ra': '10.0'}]))
    table = LamostClass(data_release='future').get_metadata(1)
    assert table['ra'][0] == '10.0'
    assert request.call_count == 1


def test_captured_dr8_mrs_metadata_records(monkeypatch, patch_request):
    data = json.loads((DATA / 'info_mrs_dr8.json').read_bytes())
    schema = {'obsid': {'datatype': 'long'}, 'lmjm': {'datatype': 'long'},
              'ra': {'datatype': 'double'}, 'band': {'datatype': 'char'}}
    monkeypatch.setattr(LamostClass, 'get_tables_metadata', lambda self, **kwargs: {
        'tables': {'med_catalogue': {'columns': schema}}})
    patch_request(create_mock_response(json_data=data))
    table = LamostClass(data_release='dr8', sub_version='v1.0').get_metadata(635003103, resolution='medium')
    assert len(table) == len(data['rows']) == 10
    assert table.meta['total'] == data['total']
    for i, row in enumerate(data['rows']):
        for name, value in row.items():
            if value is None:
                assert np.ma.is_masked(table[name][i])
            else:
                assert table[name][i] == value


@pytest.mark.parametrize('legacy', [False, True])
def test_metadata_schema_auth_failure_is_not_hidden(monkeypatch, patch_request, legacy):
    data = {'response': [{'what': 'obsid', 'data': 1}]} if legacy else [{'obsid': 1}]
    patch_request(create_mock_response(json_data=data))

    def denied(self, **kwargs):
        raise LoginError('Schema SQL requires authentication')

    monkeypatch.setattr(LamostClass, 'get_tables_metadata', denied)
    with pytest.raises(LoginError, match='Schema SQL'):
        LamostClass(data_release='dr7' if legacy else 'dr10').get_metadata(1)


def test_preserved_dr8_cone_keeps_rows_and_masks_empty_integers(monkeypatch, patch_request):
    from xml.etree import ElementTree
    content = (DATA / 'cone_mrs_dr8.xml').read_bytes()
    root = ElementTree.fromstring(content)
    fields = list(root.iterfind('.//{*}FIELD'))
    rows = list(root.iterfind('.//{*}TR'))
    # The replay uses only these independently declared catalog types.
    schema = {'obsid': {'datatype': 'long'}, 'ra': {'datatype': 'double'}}
    monkeypatch.setattr(LamostClass, '_catalog_schema', lambda self, *args, **kwargs: schema)
    patch_request(create_mock_response(content=content, content_type='text/csv'))
    table = LamostClass(data_release='dr8', sub_version='v1.0').query_region(
        '186.5 0.58', '1 arcmin', resolution='medium')
    assert len(table) == len(rows)
    assert table['med_catalogue_obsid'].dtype.kind in 'iu'
    assert table['med_catalogue_ra'].dtype.kind == 'f'
    missing = 0
    for i, field in enumerate(fields):
        if field.get('datatype') in {'int', 'long', 'short'}:
            for j, row in enumerate(rows):
                if not (row[i].text or '').strip():
                    assert np.ma.is_masked(table.columns[i][j])
                    missing += 1
                else:
                    assert table.columns[i][j] == int(row[i].text)
    assert missing > 0


@pytest.mark.parametrize('prefix,resolution', [('catalogue_', 'low'), ('med_catalogue_', 'medium')])
def test_cone_schema_prefixes_preserve_exact_matches(monkeypatch, patch_request, prefix, resolution):
    schema = {'obsid': {'datatype': 'long'}, 'id': {'datatype': 'long'},
              prefix + 'id': {'datatype': 'char'}}
    monkeypatch.setattr(LamostClass, '_catalog_schema', lambda self, *args, **kwargs: schema)
    patch_request(create_mock_response(json_data=[{prefix + 'obsid': '1', prefix + 'id': '0001',
                                                  'unknown_obsid': '0002'}]))
    table = LamostClass(data_release='dr8', sub_version='v1.0').query_region(
        '10 40', '1 arcmin', resolution=resolution)
    assert table[prefix + 'obsid'][0] == 1
    assert table[prefix + 'id'][0] == '0001'
    assert table['unknown_obsid'][0] == '0002'


@pytest.mark.parametrize('body', [b'[]', b'{"rows": []}'], ids=['list', 'rows'])
def test_empty_cone_result_has_one_set_of_typed_columns(monkeypatch, patch_request, body):
    schema = {'obsid': {'datatype': 'long'}, 'ra': {'datatype': 'double'}}
    monkeypatch.setattr(LamostClass, '_catalog_schema', lambda self, *args, **kwargs: schema)
    patch_request(create_mock_response(content=body, content_type='application/json'))
    table = LamostClass().query_region('10 40', '1 arcmin')
    assert len(table) == 0
    assert table.colnames == ['obsid', 'ra']
    assert table['obsid'].dtype.kind in 'iu'
    assert table['ra'].dtype.kind == 'f'


@pytest.mark.parametrize('datatype', ['char', 'long', 'double', 'boolean'])
def test_schema_rejects_multidimensional_columns(datatype):
    table = Table({'value': np.array([[1, 2], [3, 4]])})
    with pytest.raises(TableParseError, match="'value' could not be converted"):
        LamostClass()._apply_catalog_schema(table, {'value': {'datatype': datatype}})


@pytest.mark.parametrize('fields,rows', [
    ('<FIELD name="n" datatype="int" arraysize="2"/>', '<TR><TD/></TR>'),
    ('<FIELD name="n" datatype="int"/>', '<TR><TD/><TD>1</TD></TR>'),
])
def test_votable_missing_integer_requires_reliable_scalar_mapping(fields, rows):
    content = f'<VOTABLE version="1.2"><RESOURCE><TABLE>{fields}<DATA><TABLEDATA>{rows}'
    content += '</TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>'
    with pytest.raises(TableParseError):
        LamostClass()._parse_result(create_mock_response(content=content))


@pytest.mark.parametrize('field', [
    '<FIELD name="value"/>', '<FIELD name="value" />',
    '<FIELD name="value"><DESCRIPTION>identifier</DESCRIPTION></FIELD>',
    '<FIELD name="value"></FIELD>', '<FIELD name="value" arraysize="*"/>',
], ids=['self-closing', 'self-closing-space', 'with-child', 'paired-empty', 'arraysize-only'])
def test_votable_field_without_datatype_is_repaired_in_every_form(field):
    # A FIELD without datatype defaults to a one-character string in astropy,
    # which would reject the identifier below as truncated.
    content = ('<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3"><RESOURCE><TABLE>'
               f'{field}<DATA><TABLEDATA><TR><TD>00101001</TD></TR></TABLEDATA></DATA>'
               '</TABLE></RESOURCE></VOTABLE>')
    table = LamostClass()._parse_result(create_mock_response(content=content))
    assert list(table['value']) == ['00101001']


@pytest.mark.parametrize('version', ['1.2', '1.3'])
def test_votable_whitespace_and_existing_null_masks(version):
    content = f'''<VOTABLE version="{version}"><RESOURCE><TABLE>
      <FIELD name="n" datatype="int"><VALUES null="-9"/></FIELD><DATA><TABLEDATA>
      <TR><TD>0</TD></TR><TR><TD> \t </TD></TR><TR><TD>-9</TD></TR>
      </TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>'''
    table = LamostClass()._parse_result(create_mock_response(content=content))
    assert np.ma.getmaskarray(table['n']).tolist() == [False, True, True]
    assert table['n'][0] == 0
