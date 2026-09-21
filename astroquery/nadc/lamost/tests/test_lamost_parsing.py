# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Regression cases from historical LAMOST table responses."""

from pathlib import Path

from astropy import units as u
import numpy as np
import pytest

from astroquery.exceptions import TableParseError
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


@pytest.mark.parametrize('fields,rows', [
    ('<FIELD name="n" datatype="int" arraysize="2"/>', '<TR><TD/></TR>'),
    ('<FIELD name="n" datatype="int"/>', '<TR><TD/><TD>1</TD></TR>'),
])
def test_votable_missing_integer_requires_reliable_scalar_mapping(fields, rows):
    content = f'<VOTABLE version="1.2"><RESOURCE><TABLE>{fields}<DATA><TABLEDATA>{rows}'
    content += '</TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>'
    with pytest.raises(TableParseError):
        LamostClass()._parse_result(create_mock_response(content=content))


@pytest.mark.parametrize('version', ['1.2', '1.3'])
def test_votable_whitespace_and_existing_null_masks(version):
    content = f'''<VOTABLE version="{version}"><RESOURCE><TABLE>
      <FIELD name="n" datatype="int"><VALUES null="-9"/></FIELD><DATA><TABLEDATA>
      <TR><TD>0</TD></TR><TR><TD> \t </TD></TR><TR><TD>-9</TD></TR>
      </TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>'''
    table = LamostClass()._parse_result(create_mock_response(content=content))
    assert np.ma.getmaskarray(table['n']).tolist() == [False, True, True]
    assert table['n'][0] == 0
