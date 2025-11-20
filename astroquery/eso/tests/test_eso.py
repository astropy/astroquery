# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===========================
ESO Astroquery Module tests
===========================

European Southern Observatory (ESO)

"""
import os
import shutil
import sys

import pytest
import pyvo
from astropy.table import Table
import astropy.io.ascii

from astroquery.utils.mocks import MockResponse
from ...eso import Eso
from ...eso.utils import _UserParams, \
    _build_adql_string, _adql_sanitize_op_val, _reorder_columns, \
    DEFAULT_LEAD_COLS_RAW
from ...exceptions import NoResultsWarning, MaxResultsWarning

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
EXPECTED_MAXREC = 1000
MONKEYPATCH_TABLE_LENGTH = 50


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


DATA_FILES = {
    'GET':
        {
            Eso.AUTH_URL: 'oidc_token.json',
        },
    'POST':
        {
            'https://archive.eso.org/wdb/wdb/eso/eso_archive_main/query': 'main_sgra_query.tbl',
            'https://archive.eso.org/wdb/wdb/eso/amber/query': 'amber_sgra_query.tbl',
            'https://archive.eso.org/wdb/wdb/adp/phase3_main/query': 'vvv_sgra_survey_response.tbl',
        },
    'ADQL':
        {
            "select * from ivoa.ObsCore where obs_collection in ('VVV') and "
            "intersects(s_region, circle('ICRS', 266.41681662, -29.00782497, 0.1775))=1":
            "query_coll_vvv_sgra.csv",

            "select * from ist.sinfoni where target = 'SGRA'":
            "query_inst_sinfoni_sgra.csv",

            "select * from ist.apex_quicklooks where project_id = 'E-095.F-9802A-2015'":
            "query_apex_ql_5.csv",

            "select * from dbo.raw where target = 'SGR A' and object = 'SGR A'":
            "query_main_sgra.csv",

            "select distinct obs_collection from ivoa.ObsCore": "query_list_surveys.csv",

            "select table_name from TAP_SCHEMA.tables where schema_name='ist' order by table_name":
            "query_list_instruments.csv",
        }
}

TEST_SURVEYS = [
    '081.C-0827', 'ADHOC', 'CAFFEINE', 'ENTROPY', 'GAIAESO', 'HARPS', 'INSPIRE', 'KIDS', 'ZCOSMOS']
TEST_INSTRUMENTS = [
    'amber', 'crires', 'espresso', 'fors1', 'giraffe', 'gravity', 'midi', 'xshooter']


def eso_request(request_type, url, **kwargs):
    _ = kwargs
    with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


def monkey_tap(query, **kwargs):
    _ = kwargs
    table_file = data_path(DATA_FILES['ADQL'][query])
    table = astropy.io.ascii.read(table_file, format='csv', header_start=0, data_start=1)
    return table


def download_request(url, **kwargs):
    _ = kwargs
    filename = 'testfile.fits.Z'
    with open(data_path(filename), 'rb') as f:
        header = {'Content-Disposition': f'filename={filename}'}
        response = MockResponse(content=f.read(), url=url, headers=header)
    return response


def calselector_request(url, **kwargs):
    is_multipart = len(kwargs['data']['dp_id']) > 1
    if is_multipart:
        filename = 'FORS2.2021-01-02T00_59_12.533_raw2raw_multipart.xml'
        header = {
            'Content-Type': 'multipart/form-data; '
            'boundary=uFQlfs9nBIDEAIoz0_ZM-O2SXKsZ2iSd4h7H;charset=UTF-8'
        }
    else:
        filename = 'FORS2.2021-01-02T00_59_12.533_raw2raw.xml'
        header = {
            'Content-Disposition': f'filename="{filename}"',
            'Content-Type': 'application/xml; content=calselector'
        }
    with open(data_path(filename), 'rb') as f:
        response = MockResponse(content=f.read(), url=url, headers=header)
    return response


def test_sinfoni_sgr_a_star(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)
    result = eso.query_instrument('sinfoni',
                                  column_filters={
                                      'target': "SGRA"
                                  }
                                  )
    # test all results are there and the expected target is present
    assert len(result) == MONKEYPATCH_TABLE_LENGTH
    assert 'SGRA' in result['target']


def test_main_sgr_a_star(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)
    result = eso.query_main(
        column_filters={
            'target': "SGR A",
            'object': "SGR A"
        })
    # test all results are there and the expected target is present
    assert len(result) == 23
    assert 'SGR A' in result['object']
    assert 'SGR A' in result['target']


def test_apex_retrieval(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)

    tbla = eso.query_apex_quicklooks(
        column_filters={
            "project_id": 'E-095.F-9802A-2015'
        }
    )

    assert len(tbla) == 5
    assert set(tbla['release_date']) == {
        '2015-07-17T03:06:23.280Z',
        '2015-07-18T12:07:32.713Z',
        '2015-09-18T11:31:15.867Z',
        '2015-09-15T11:06:55.663Z',
        '2015-09-18T11:46:19.970Z'
    }


def test_vvv(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)
    result = eso.query_surveys(surveys='VVV',
                               cone_ra=266.41681662, cone_dec=-29.00782497,
                               cone_radius=0.1775,
                               )
    # test all results are there and the expected target is present
    assert len(result) == MONKEYPATCH_TABLE_LENGTH
    assert 'target_name' in result.colnames
    assert 'b333' in result['target_name']


def test_list_surveys(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)
    saved_list = eso.list_surveys()
    assert isinstance(saved_list, list)
    assert set(TEST_SURVEYS) <= set(saved_list)


def test_list_instruments(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)
    saved_list = eso.list_instruments()
    assert isinstance(saved_list, list)
    assert set(TEST_INSTRUMENTS) <= set(saved_list)


def test_authenticate(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, '_request', eso_request)
    eso.cache_location = DATA_DIR
    authenticated = eso._authenticate(username="someuser", password="somepassword")
    assert authenticated is True


def test_download(monkeypatch, tmp_path):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    eso.cache_location = tmp_path
    fileid = 'testfile'
    filename = os.path.join(tmp_path, f"{fileid}.fits.Z")
    monkeypatch.setattr(eso._session, 'get', download_request)
    downloaded_files = eso.retrieve_data([fileid], unzip=False)
    assert len(downloaded_files) == 1
    assert downloaded_files[0] == filename


@pytest.mark.skipif(sys.platform.startswith("win"), reason="gunzip not available on Windows")
def test_unzip(tmp_path):
    eso = Eso()
    filename = os.path.join(DATA_DIR, 'testfile.fits.Z')
    tmp_filename = tmp_path / 'testfile.fits.Z'
    uncompressed_filename = tmp_path / 'testfile.fits'
    shutil.copy(filename, tmp_filename)
    uncompressed_files = eso._unzip_files([str(tmp_filename)])
    assert len(uncompressed_files) == 1
    assert uncompressed_files[0] == str(uncompressed_filename)


def test_cached_file():
    eso = Eso()
    filename = os.path.join(DATA_DIR, 'testfile.fits.Z')
    assert eso._find_cached_file(filename) is True
    assert eso._find_cached_file("non_existent_filename") is False


def test_calselector(monkeypatch, tmp_path):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    eso.cache_location = tmp_path
    dataset = 'FORS2.2021-01-02T00:59:12.533'
    monkeypatch.setattr(eso._session, 'post', calselector_request)
    result = eso.get_associated_files([dataset], savexml=True)
    assert isinstance(result, list)
    assert len(result) == MONKEYPATCH_TABLE_LENGTH
    assert dataset not in result


def test_calselector_multipart(monkeypatch, tmp_path):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    eso.cache_location = tmp_path
    datasets = ['FORS2.2021-01-02T00:59:12.533', 'FORS2.2021-01-02T00:59:12.534']
    monkeypatch.setattr(eso._session, 'post', calselector_request)
    result = eso.get_associated_files(datasets, savexml=False)
    assert isinstance(result, list)
    assert len(result) == 99
    assert datasets[0] not in result and datasets[1] not in result


def test_tap_url():
    prod_url = "https://archive.eso.org/tap_obs"
    eso_instance = Eso()
    assert eso_instance._tap_url() == prod_url


@pytest.mark.parametrize("input_val, expected", [
    # Numeric values
    (1, "= 1"),
    (1.5, "= 1.5"),
    (None, "= None"),

    # String values
    ("ciao", "= 'ciao'"),
    ("1.5", "= '1.5'"),
    ("ciao  ", "= 'ciao'"),
    ("  ciao", "= 'ciao'"),
    ("  ciao  ", "= 'ciao'"),
    ("1.5 ", "= '1.5'"),
    (" a string with spaces ", "= 'a string with spaces'"),
    ("SGR A", "= 'SGR A'"),
    ("'SGR A'", "= 'SGR A'"),

    # Operator-based queries
    ("< 5", "< 5"),
    ("> 1.23", "> 1.23"),
    ("< '5'", "< '5'"),
    ("> '1.23'", "> '1.23'"),

    ("like '%John%'", "like  '%John%'"),
    ("not like '%John%'", "not like  '%John%'"),
    ("in ('apple', 'mango', 'orange')", "in  ('apple', 'mango', 'orange')"),
    ("not in ('apple', 'mango', 'orange')", "not in  ('apple', 'mango', 'orange')"),
    ("in (1, 2, 3)", "in  (1, 2, 3)"),
    ("not in (1, 2, 3)", "not in  (1, 2, 3)"),

    # Operator-based queries
    ("<5", "< 5"),
    (">1.23", "> 1.23"),
    (">=1.23", ">= 1.23"),
    ("<=1.23", "<= 1.23"),
    ("!=1.23", "!= 1.23"),
    ("<'5'", "< '5'"),
    (">'1.23'", "> '1.23'"),

    # Strings that look like operators but should be treated as strings
    ("'like %John%'", "= 'like %John%'"),
    ("'= something'", "= '= something'"),
    ("'> 5'", "= '> 5'"),
    ("' > 1.23 '", "= ' > 1.23 '"),
    ("likewise", "= 'likewise'"),
    ("INfinity", "= 'INfinity'"),
    ("like'%John%'", "= 'like'%John%''"),  # pathologic case

    # Ill-formed queries: Operator, but not sanitized. Expected to be passed through as-is
    ("like %John%", "like  %John%"),
    ("not like %John%", "not like  %John%"),
    ("= SGR A", "= SGR A"),
])
def test_adql_sanitize_op_val(input_val, expected):
    assert _adql_sanitize_op_val(input_val) == expected


def test_maxrec():
    eso_instance = Eso()

    # EXPECTED_MAXREC is the default value in the conf
    maxrec = eso_instance.ROW_LIMIT
    assert maxrec == EXPECTED_MAXREC

    # we change it to 5
    eso_instance.ROW_LIMIT = 5
    maxrec = eso_instance.ROW_LIMIT
    assert maxrec == 5

    # change it to no-truncation
    eso_instance.ROW_LIMIT = None
    maxrec = eso_instance.ROW_LIMIT
    assert maxrec == sys.maxsize

    # no truncation
    eso_instance.ROW_LIMIT = 0
    maxrec = eso_instance.ROW_LIMIT
    assert maxrec == sys.maxsize

    # no truncation
    eso_instance.ROW_LIMIT = -1
    maxrec = eso_instance.ROW_LIMIT
    assert maxrec == sys.maxsize


def test_download_pyvo_table():
    eso_instance = Eso()
    dal = pyvo.dal.TAPService(eso_instance._tap_url())

    q_str = "select * from ivoa.ObsCore"
    table = None
    with pytest.raises(pyvo.dal.exceptions.DALFormatError):
        table = eso_instance._try_download_pyvo_table(q_str, dal)

    assert table is None


def test_issue_table_length_warnings():
    eso_instance = Eso()

    # should warn, since the table is empty
    t = Table()
    with pytest.warns(NoResultsWarning):
        eso_instance._maybe_warn_about_table_length(t, 1)

    # should warn, since EXPECTED_MAXREC = eso_instance.maxrec
    t = Table({"col_name": [i for i in range(EXPECTED_MAXREC+1)]})
    with pytest.warns(MaxResultsWarning):
        eso_instance._maybe_warn_about_table_length(t, EXPECTED_MAXREC+1)

    # should not warn
    t = Table({"col_name": [i for i in range(51)]})
    eso_instance._maybe_warn_about_table_length(t, EXPECTED_MAXREC+1)


def test_reorder_columns(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap', monkey_tap)
    table = eso.query_main(
        column_filters={
            'target': "SGR A",
            'object': "SGR A"}
    )
    names_before = table.colnames[:]
    table2 = _reorder_columns(table)
    names_after = table2.colnames[:]

    # the columns we want to change are actually in the table
    assert set(DEFAULT_LEAD_COLS_RAW).issubset(names_before)
    assert set(DEFAULT_LEAD_COLS_RAW).issubset(names_after)

    # no columns are removed nor added
    assert set(names_before) == set(names_after)

    # Column by column, the contents are the same
    for cname in table.colnames:
        assert table[[cname]].values_equal(table2[[cname]]), f"Error for {cname}"

    # empty table doesn't cause a crash
    empty_1 = Table()
    empty_2 = _reorder_columns(empty_1)
    assert len(empty_1) == 0 and isinstance(empty_1, Table)
    assert len(empty_2) == 0 and isinstance(empty_1, Table)

    # If the values we're looking for as leading columns, everything stays the same
    some_table = Table({"x": [1, 2, 3], "y": [4, 5, 6]})
    same_table = _reorder_columns(some_table)
    assert all(some_table == same_table), "Table with no cols to change fails"

    # If what we pas is not a table, the function has no effect
    not_a_table_1 = object()
    not_a_table_2 = _reorder_columns(not_a_table_1)
    assert not_a_table_1 == not_a_table_2


@pytest.mark.parametrize("params, expected", [
    # Basic SELECT * cases
    (_UserParams(table_name="ivoa.ObsCore"),
     "select * from ivoa.ObsCore"),

    (_UserParams(table_name="ivoa.ObsCore", columns=''),
     "select * from ivoa.ObsCore"),

    (_UserParams(table_name="ivoa.ObsCore", columns='*'),
     "select * from ivoa.ObsCore"),

    # Basic column selection
    (_UserParams(table_name="my.Table", columns="a, b, c"),
     "select a, b, c from my.Table"),

    (_UserParams(table_name="my.Table", columns=["a", "b", "c"]),
     "select a, b, c from my.Table"),

    # With filters and order
    (_UserParams(
        table_name="my.Table",
        columns=["a", "b", "c"],
        column_filters={"x": "> 1", "y": "< 2"},
        order_by="z"),
     "select a, b, c from my.Table where x > 1 and y < 2 order by z desc"),

    # With cone search
    (_UserParams(
        table_name="galaxies",
        columns="name, ra, dec",
        cone_ra=150.1, cone_dec=2.3, cone_radius=0.1),
     "select name, ra, dec from galaxies where "
     "intersects(s_region, circle('ICRS', 150.1, 2.3, 0.1))=1"),

    # With count_only
    (_UserParams(
        table_name="galaxies",
        cone_ra=10, cone_dec=20, cone_radius=0.5,
        count_only=True),
     "select count(*) from galaxies where intersects(s_region, circle('ICRS', 10, 20, 0.5))=1"),

    # With top
    (_UserParams(
        table_name="stars",
        columns="name, mag",
        top=10,
        order_by="mag",
        order_by_desc=False),
     "select top 10 name, mag from stars order by mag asc"),

    # With multiple filters including IN
    (_UserParams(
        table_name="beautiful.Stars",
        columns=["id", "instrument"],
        column_filters={"instrument": "in ('MUSE', 'UVES')", "t_exptime": "> 100"},
        order_by="t_exptime"),
     "select id, instrument from beautiful.Stars where instrument in  ('MUSE', 'UVES') "
     "and t_exptime > 100 order by t_exptime desc"),

    # With all params 1
    (
        _UserParams(
            table_name="ivoa.ObsCore",
            cone_ra=180.0,
            cone_dec=-45.0,
            cone_radius=0.05,
            columns=["target_name", "s_ra", "s_dec", "em_min", "em_max"],
            column_filters={
                "em_min": "> 4e-7",
                "em_max": "< 1.2e-6",
                "dataproduct_type": "in ('spectrum')"
            },
            top=100,
            order_by="em_min",
            order_by_desc=True,
            count_only=False,
            get_query_payload=True,
        ),
        "select top 100 target_name, s_ra, s_dec, em_min, em_max from ivoa.ObsCore "
        "where em_min > 4e-7 and em_max < 1.2e-6 and dataproduct_type in  ('spectrum') "
        "and intersects(s_region, circle('ICRS', 180.0, -45.0, 0.05))=1 "
        "order by em_min desc"
    ),

    # With all params 2
    (
        _UserParams(
            table_name="ivoa.ObsCore",
            cone_ra=180.0,
            cone_dec=-45.0,
            cone_radius=0.05,
            columns=["target_name", "s_ra", "s_dec", "em_min", "em_max"],
            column_filters={
                "em_min": "> 4e-7",
                "em_max": "< 1.2e-6",
                "dataproduct_type": "in ('spectrum')"
            },
            top=100,
            order_by="em_min",
            order_by_desc=False,
            count_only=True,
            get_query_payload=True,
        ),
        "select top 100 count(*) from ivoa.ObsCore "
        "where em_min > 4e-7 and em_max < 1.2e-6 and dataproduct_type in  ('spectrum') "
        "and intersects(s_region, circle('ICRS', 180.0, -45.0, 0.05))=1"
    ),
])
def test_build_adql_string(params, expected):
    """
    Tests that the ADQL query builder generates the expected query.

    Example of typical adql query:

        SELECT
            target_name, dp_id, s_ra, s_dec, t_exptime, em_min, em_max,
            dataproduct_type, instrument_name, obstech, abmaglim,
            proposal_id, obs_collection
        FROM
            ivoa.ObsCore
        WHERE
            intersects(s_region, circle('ICRS', 109.668246, -24.558700, 0.001389)) = 1
            AND dataproduct_type IN ('spectrum')
            AND em_min > 4.0e-7
            AND em_max < 1.2e-6
        ORDER BY
            em_min DESC
    """
    query = _build_adql_string(params)
    assert query == expected, f"Expected:\n{expected}\n\nGot:\n{query}\n"
