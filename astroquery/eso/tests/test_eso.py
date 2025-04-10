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

import pickle
import pytest
import pyvo
from astropy.table import Table

from astroquery.utils.mocks import MockResponse
from ...eso import Eso
from ...eso.utils import py2adql, adql_sanitize_val
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
            # TODO: Point the second query to an IST when the ISTs are available.
            # TODO: Fix the apex query when the backend is available.
            "select * from ivoa.ObsCore where obs_collection in ('VVV') and "
            "intersects(s_region, circle('ICRS', 266.41681662, -29.00782497, 0.1775))=1":
            "query_coll_vvv_sgra.pickle",

            "select * from ist.sinfoni where target = 'SGRA'":
            "query_inst_sinfoni_sgra.pickle",

            "select * from dbo.raw where target = 'SGR A' and object = 'SGR A'":
            "query_main_sgra.pickle",

            "select distinct obs_collection from ivoa.ObsCore": "query_list_collections.pickle",

            "select table_name from TAP_SCHEMA.tables where schema_name='ist' order by table_name":
            "query_list_instruments.pickle",

            "APEX_QUERY_PLACEHOLDER": "query_apex_ql_5.pickle",

            "generic cached query":
            "fd303fa27993048bd2393af067fe5ceccf4817c288ce5c0b4343386f.pickle",

            "query points to non table file":
            "2031769bb0e68fb2816bf5680203e586eea71ca58b2694a71a428605.pickle"
        }
}

TEST_COLLECTIONS = [
    '081.C-0827', 'ADHOC', 'CAFFEINE', 'ENTROPY', 'GAIAESO', 'HARPS', 'INSPIRE', 'KIDS', 'ZCOSMOS']
TEST_INSTRUMENTS = [
    'amber', 'crires', 'espresso', 'fors1', 'giraffe', 'gravity', 'midi', 'xshooter']


def eso_request(request_type, url, **kwargs):
    _ = kwargs
    with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


def monkey_tap(query_str, **kwargs):
    _ = kwargs
    table_file = data_path(DATA_FILES['ADQL'][query_str])
    with open(table_file, "rb") as f:
        table = pickle.load(f)
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
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
    result = eso.query_instrument('sinfoni', target='SGRA')
    # test all results are there and the expected target is present
    assert len(result) == MONKEYPATCH_TABLE_LENGTH
    assert 'SGRA' in result['target']


def test_main_sgr_a_star(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
    result = eso.query_main(target='SGR A', object='SGR A')
    # test all results are there and the expected target is present
    assert len(result) == 23
    assert 'SGR A' in result['object']
    assert 'SGR A' in result['target']


def test_vvv(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
    result = eso.query_surveys(surveys='VVV',
                               cone_ra=266.41681662, cone_dec=-29.00782497,
                               cone_radius=0.1775,
                               )
    # test all results are there and the expected target is present
    assert len(result) == MONKEYPATCH_TABLE_LENGTH
    assert 'target_name' in result.colnames
    assert 'b333' in result['target_name']


def test_list_collections(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
    saved_list = eso.list_surveys()
    assert isinstance(saved_list, list)
    assert set(TEST_COLLECTIONS) <= set(saved_list)


def test_list_instruments(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
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
    tap_url_env_var = "ESO_TAP_URL"
    tmpvar = None
    dev_url = "dev_url"
    prod_url = "https://archive.eso.org/tap_obs"

    # ESO_TAP_URL shouldn't be set to start the test
    try:
        tmpvar = os.environ[tap_url_env_var]
        del os.environ[tap_url_env_var]
    except KeyError:
        pass

    eso_instance = Eso()

    # ESO_TAP_URL not set
    assert eso_instance._tap_url() == prod_url

    # ESO_TAP_URL set
    os.environ[tap_url_env_var] = dev_url
    assert eso_instance._tap_url() == dev_url

    # set again the env vars, in case we deleted it earlier
    if tmpvar:
        os.environ[tap_url_env_var] = tmpvar


def test_adql_sanitize_val():
    # adql queries are themselves strings.
    # field that are strings are surrounded by single quotes ('')
    # This function sanitizes values so that the following queries
    # are correctly written:
    # select [...] where x_int = 9
    # select [...] where x_str = '9'

    assert adql_sanitize_val("ciao") == "'ciao'"
    assert adql_sanitize_val(1) == "1"
    assert adql_sanitize_val(1.5) == "1.5"
    assert adql_sanitize_val("1.5") == "'1.5'"


def test_maxrec():
    eso_instance = Eso()

    # EXPECTED_MAXREC is the default value in the conf
    maxrec = eso_instance.maxrec
    assert maxrec == EXPECTED_MAXREC

    # we change it to 5
    eso_instance.maxrec = 5
    maxrec = eso_instance.maxrec
    assert maxrec == 5

    # change it to no-truncation
    eso_instance.maxrec = None
    maxrec = eso_instance.maxrec
    assert maxrec == sys.maxsize

    # no truncation
    eso_instance.maxrec = 0
    maxrec = eso_instance.maxrec
    assert maxrec == sys.maxsize

    # no truncation
    eso_instance.maxrec = -1
    maxrec = eso_instance.maxrec
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
        eso_instance._maybe_warn_about_table_length(t)

    # should warn, since EXPECTED_MAXREC = eso_instance.maxrec
    t = Table({"col_name": [i for i in range(EXPECTED_MAXREC)]})
    with pytest.warns(MaxResultsWarning):
        eso_instance._maybe_warn_about_table_length(t)

    # should not warn
    t = Table({"col_name": [i for i in range(51)]})
    eso_instance._maybe_warn_about_table_length(t)


def test_py2adql():
    """
    #  Example query:
    #
    #  SELECT
    #      target_name, dp_id, s_ra, s_dec, t_exptime, em_min, em_max,
    #      dataproduct_type, instrument_name, obstech, abmaglim,
    #      proposal_id, obs_collection
    #  FROM
    #      ivoa.ObsCore
    #  WHERE
    #      intersects(s_region, circle('ICRS', 109.668246, -24.558700, 0.001389))=1
    #  AND
    #      dataproduct_type in ('spectrum')
    #  AND
    #      em_min>4.0e-7
    #  AND
    #      em_max<1.2e-6
    #  ORDER BY SNR DESC
    """

    # Simple tests
    q = py2adql('ivoa.ObsCore')
    eq = "select * from ivoa.ObsCore"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('ivoa.ObsCore', columns='')
    eq = "select * from ivoa.ObsCore"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('ivoa.ObsCore', columns='*')
    eq = "select * from ivoa.ObsCore"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('pinko.Pallino', ['pippo', 'tizio', 'caio'])
    eq = "select pippo, tizio, caio from pinko.Pallino"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('pinko.Pallino', ['pippo', 'tizio', 'caio'])
    eq = "select pippo, tizio, caio from pinko.Pallino"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('pinko.Pallino', ['pippo', 'tizio', 'caio'],
                where_constraints=['asdf > 1', 'asdf < 2', 'asdf = 3', 'asdf != 4'],
                order_by='order_col')
    eq = "select pippo, tizio, caio from pinko.Pallino " + \
        "where asdf > 1 and asdf < 2 and asdf = 3 and asdf != 4 " + \
        "order by order_col desc"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('pinko.Pallino', ['pippo', 'tizio', 'caio'],
                where_constraints=["asdf = 'ASDF'", "bcd = 'BCD'"],
                order_by='order_col')
    eq = "select pippo, tizio, caio from pinko.Pallino " + \
        "where asdf = 'ASDF' and bcd = 'BCD' " + \
        "order by order_col desc"
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    # All arguments
    columns = 'target_name, dp_id, s_ra, s_dec, t_exptime, em_min, em_max, ' + \
        'dataproduct_type, instrument_name, obstech, abmaglim, ' + \
        'proposal_id, obs_collection'
    table = 'ivoa.ObsCore'
    and_c_list = ['em_min>4.0e-7', 'em_max<1.2e-6', 'asdasdads']

    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=True)
    expected_query = 'select ' + columns + ' from ' + table + \
        ' where ' + and_c_list[0] + ' and ' + and_c_list[1] + ' and ' + and_c_list[2] + \
        " order by snr desc"
    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"

    # All arguments
    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=False)
    expected_query = 'select ' + columns + ' from ' + table + \
        ' where ' + and_c_list[0] + ' and ' + and_c_list[1] + ' and ' + and_c_list[2] + \
        " order by snr asc"
    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"

    # ra, dec, radius, all int
    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=False,
                cone_ra=1, cone_dec=2, cone_radius=3)
    expected_query = 'select ' + columns + ' from ' + table + \
        ' where ' + and_c_list[0] + ' and ' + and_c_list[1] + ' and ' + and_c_list[2] + \
        ' and intersects(s_region, circle(\'ICRS\', 1, 2, 3))=1' + \
        " order by snr asc"
    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"

    # ra, dec, radius, all float
    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=False,
                cone_ra=1.23, cone_dec=2.34, cone_radius=3.45)
    expected_query = 'select ' + columns + ' from ' + table + \
        ' where ' + and_c_list[0] + ' and ' + and_c_list[1] + ' and ' + and_c_list[2] + \
        ' and intersects(s_region, circle(\'ICRS\', 1.23, 2.34, 3.45))=1' + \
        " order by snr asc"
    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"

    # ra, dec, radius, all zero
    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=False,
                cone_ra=0, cone_dec=0, cone_radius=0)
    expected_query = 'select ' + columns + ' from ' + table + \
        ' where ' + and_c_list[0] + ' and ' + and_c_list[1] + ' and ' + and_c_list[2] + \
        ' and intersects(s_region, circle(\'ICRS\', 0, 0, 0))=1' + \
        " order by snr asc"
    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"

    # count only
    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=False,
                cone_ra=1.23, cone_dec=2.34, cone_radius=3.45, count_only=True)
    expected_query = ("select count(*) from ivoa.ObsCore where "
                      "em_min>4.0e-7 and em_max<1.2e-6 and asdasdads "
                      "and intersects(s_region, circle('ICRS', 1.23, 2.34, 3.45))=1 "
                      "order by snr asc")
    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"

    # top
    q = py2adql(columns=columns, table=table,
                where_constraints=and_c_list,
                order_by='snr', order_by_desc=False,
                cone_ra=1.23, cone_dec=2.34, cone_radius=3.45, top=5)
    expected_query = 'select top 5 ' + columns + ' from ' + table + \
        ' where ' + and_c_list[0] + ' and ' + and_c_list[1] + ' and ' + and_c_list[2] + \
        ' and intersects(s_region, circle(\'ICRS\', 1.23, 2.34, 3.45))=1' + \
        " order by snr asc"

    assert expected_query == q, f"Expected:\n{expected_query}\n\nObtained:\n{q}\n\n"
