# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import shutil
import sys

import pickle
import pytest

from astroquery.utils.mocks import MockResponse
from ...eso import Eso, EsoClass
from ...eso.utils import py2adql

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


DATA_FILES = {
    'GET':
        {
            Eso.AUTH_URL: 'oidc_token.json',
        },
    'POST':
        {
            'http://archive.eso.org/wdb/wdb/eso/eso_archive_main/query': 'main_sgra_query.tbl',
            'http://archive.eso.org/wdb/wdb/eso/amber/query': 'amber_sgra_query.tbl',
            'http://archive.eso.org/wdb/wdb/adp/phase3_main/query': 'vvv_sgra_survey_response.tbl',
        },
    'ADQL':
        {
            # TODO: Point the second query to an IST when the ISTs are available.
            # TODO: Fix the apex query when the backend is available.
            "select top 50 * from ivoa.ObsCore where obs_collection in ('VVV') and "
            "intersects(circle('ICRS', 266.41681662, -29.00782497, 0.1775), s_region)=1":
            "query_coll_vvv_sgra.pickle",
            "select top 50 * from dbo.raw where instrument in ('sinfoni') and "
            "target = 'SGRA'":
            "query_inst_sinfoni_sgra.pickle",
            "select top 50 * from dbo.raw where target = 'SGR A' and object = 'SGR A'":
            "query_main_sgra.pickle",
            "APEX_QUERY_PLACEHOLDER": "query_apex_ql_5.pickle",
        }
}


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


def test_sinfoni_SgrAstar(monkeypatch):
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
    result = eso.query_instrument('sinfoni', target='SGRA')
    # test all results are there and the expected target is present
    assert len(result) == 50
    assert 'SGRA' in result['target']


def test_main_SgrAstar(monkeypatch):
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
    result = eso.query_collections(collections='VVV',
                                   coord1=266.41681662, coord2=-29.00782497,
                                   box='01 00 00',
                                   )
    # test all results are there and the expected target is present
    assert len(result) == 50
    assert 'target_name' in result.colnames
    assert 'b333' in result['target_name']


def test_apex_quicklooks(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, 'query_tap_service', monkey_tap)
    p_id = '095.F-9802'
    table = eso.query_apex_quicklooks(prog_id=p_id, cache=True)

    assert len(table) == 5
    assert set(table['Release Date']) == {'2015-07-17', '2015-07-18',
                                         '2015-09-15', '2015-09-18'}


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
    assert len(result) == 50
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
    url = EsoClass.tap_url()
    if EsoClass.USE_DEV_TAP:
        assert url == "http://dfidev5.hq.eso.org:8123/tap_obs"
    else:
        assert url == "http://archive.eso.org/tap_obs"


def test_py2adql():
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
    #

    # Simple tests
    q = py2adql('ivoa.ObsCore')
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
        "order by order_col desc"  # JM check here!!
    assert eq == q, f"Expected:\n{eq}\n\nObtained:\n{q}\n\n"

    q = py2adql('pinko.Pallino', ['pippo', 'tizio', 'caio'],
                where_constraints=["asdf = 'ASDF'", "bcd = 'BCD'"],
                order_by='order_col')
    eq = "select pippo, tizio, caio from pinko.Pallino " + \
        "where asdf = 'ASDF' and bcd = 'BCD' " + \
        "order by order_col desc"  # JM check here!!
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
