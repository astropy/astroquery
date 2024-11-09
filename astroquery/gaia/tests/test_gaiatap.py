# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""
import datetime
import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.table import Column, Table
from astropy.utils.data import get_pkg_data_filename
from astropy.utils.exceptions import AstropyDeprecationWarning
from requests import HTTPError

from astroquery.gaia import conf
from astroquery.gaia.core import GaiaClass
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.core import TapPlus

GAIA_QUERIER = GaiaClass(show_server_messages=False)

package = "astroquery.gaia.tests"
JOB_DATA_FILE_NAME = get_pkg_data_filename(os.path.join("data", 'job_1.vot'), package=package)
JOB_DATA_FILE_NAME_NEW = get_pkg_data_filename(os.path.join("data", '1710099405832VAL-result.vot'), package=package)

JOB_DATA_CONE_SEARCH_ASYNC_JSON_FILE_NAME = get_pkg_data_filename(os.path.join("data", 'cone_search_async.json'),
                                                                  package=package)
JOB_DATA_QUERIER_ASYNC_FILE_NAME = get_pkg_data_filename(os.path.join("data", 'launch_job_async.json'), package=package)

JOB_DATA_QUERIER_ECSV_FILE_NAME = get_pkg_data_filename(os.path.join("data", '1712337806100O-result.ecsv'),
                                                        package=package)

DL_PRODUCTS_VOT = get_pkg_data_filename(
    os.path.join("data", 'gaia_dr3_source_id_5937083312263887616_dl_products_vot.zip'),
    package=package)

DL_PRODUCTS_ECSV = get_pkg_data_filename(
    os.path.join("data", 'gaia_dr3_source_id_5937083312263887616_dl_products_ecsv.zip'),
    package=package)

DL_PRODUCTS_CSV = get_pkg_data_filename(
    os.path.join("data", 'gaia_dr3_source_id_5937083312263887616_dl_products_csv.zip'),
    package=package)

DL_PRODUCTS_FITS = get_pkg_data_filename(
    os.path.join("data", 'gaia_dr3_source_id_5937083312263887616_dl_products_fits.zip'),
    package=package)

JOB_DATA = Path(JOB_DATA_FILE_NAME).read_text()
JOB_DATA_NEW = Path(JOB_DATA_FILE_NAME_NEW).read_text()

JOB_DATA_CONE_SEARCH_ASYNC_JSON = Path(JOB_DATA_CONE_SEARCH_ASYNC_JSON_FILE_NAME).read_text()
JOB_DATA_QUERIER_ASYNC_JSON = Path(JOB_DATA_QUERIER_ASYNC_FILE_NAME).read_text()
JOB_DATA_ECSV = Path(JOB_DATA_QUERIER_ECSV_FILE_NAME).read_text()

ids_ints = [1104405489608579584, '1104405489608579584, 1809140662896080256', (1104405489608579584, 1809140662896080256),
            ('1104405489608579584', '1809140662896080256'), '4295806720-38655544960',
            '4295806720-38655544960, 549755818112-1275606125952',
            ('4295806720-38655544960', '549755818112-1275606125952')]

ids_designator = ['Gaia DR3 1104405489608579584', 'Gaia DR3 1104405489608579584, Gaia DR3 1809140662896080256',
                  ('Gaia DR3 1104405489608579584', 'Gaia DR3 1809140662896080256'),
                  'Gaia DR3 4295806720-Gaia DR3 38655544960',
                  'Gaia DR3 4295806720-Gaia DR3 38655544960, Gaia DR3 549755818112-Gaia DR3 1275606125952',
                  ('Gaia DR3 4295806720-Gaia DR3 38655544960', 'Gaia DR3 549755818112-Gaia DR3 1275606125952'),
                  'Gaia DR3 4295806720-Gaia DR3 38655544960, Gaia DR2 549755818112-Gaia DR2 1275606125952',
                  ('Gaia DR3 4295806720-Gaia DR3 38655544960', 'Gaia DR2 549755818112-Gaia DR2 1275606125952')]

RADIUS = 1 * u.deg
SKYCOORD = SkyCoord(ra=19 * u.deg, dec=20 * u.deg, frame="icrs")

FAKE_TIME = datetime.datetime(2024, 1, 1, 0, 0, 59, 1)


@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return FAKE_TIME

    monkeypatch.setattr(datetime, 'datetime', mydatetime)


def test_patch_datetime(patch_datetime_now):
    assert datetime.datetime.now() == FAKE_TIME


@pytest.fixture(scope="module")
def column_attrs():
    dtypes = {
        "alpha": np.float64,
        "delta": np.float64,
        "source_id": object,
        "table1_oid": np.int32
    }
    columns = {k: Column(name=k, description=k, dtype=v) for k, v in dtypes.items()}

    columns["source_id"].meta = {"_votable_string_dtype": "char"}
    return columns


@pytest.fixture(scope="module")
def column_attrs_lower_case_new():
    columns = {}
    columns["designation"] = Column(name="designation",
                                    description='Unique source designation (unique across all Data Releases)',
                                    dtype=object)
    columns["source_id"] = Column(name="source_id",
                                  description='Unique source identifier (unique within a particular Data Release)',
                                  unit=None, dtype=np.int64)
    columns["ra"] = Column(name="ra", description='Right ascension', unit='deg', dtype=np.float64)
    columns["dec"] = Column(name="dec", description='Declination', unit='deg', dtype=np.float64)
    columns["parallax"] = Column(name="parallax", description='Parallax', unit='mas', dtype=np.float64)
    return columns


@pytest.fixture(scope="module")
def column_attrs_upper_case_new():
    columns = {}
    columns["DESIGNATION"] = Column(name="DESIGNATION",
                                    description='Unique source designation (unique across all Data Releases)',
                                    dtype=object)
    columns["SOURCE_ID"] = Column(name="SOURCE_ID",
                                  description='Unique source identifier (unique within a particular Data Release)',
                                  unit=None, dtype=np.int64)
    columns["ra"] = Column(name="ra", description='Right ascension', unit='deg', dtype=np.float64)
    columns["dec"] = Column(name="dec", description='Declination', unit='deg', dtype=np.float64)
    columns["parallax"] = Column(name="parallax", description='Parallax', unit='mas', dtype=np.float64)
    return columns


@pytest.fixture(scope="module")
def column_attrs_conesearch_json():
    columns = {}
    columns["solution_id"] = Column(name="solution_id", description='Solution Identifier', unit=None, dtype=np.int64)
    columns["ref_epoch"] = Column(name="ref_epoch", description='Reference epoch', unit='yr', dtype=np.float64)
    columns["ra"] = Column(name="ra", description='Right ascension', unit='deg', dtype=np.float64)
    columns["ra_error"] = Column(name="ra_error", description='Standard error of right ascension', unit='mas',
                                 dtype=np.float64)
    columns["pm"] = Column(name="pm", description='Total proper motion', unit='mas / yr', dtype=object)

    return columns


@pytest.fixture(scope="module")
def column_attrs_launch_json():
    columns = {}
    columns["source_id"] = Column(name="source_id",
                                  description='Unique source identifier (unique within a particular Data Release)',
                                  unit=None, dtype=np.int64)
    columns["ra"] = Column(name="ra", description='Right ascension', unit='deg', dtype=np.float64)
    columns["dec"] = Column(name="dec", description='Declination', unit='deg', dtype=np.float64)
    columns["parallax"] = Column(name="parallax", description='Parallax', unit='mas', dtype=np.float64)

    return columns


@pytest.fixture(scope="module")
def mock_querier():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="function")
def mock_datalink_querier(patch_datetime_now):

    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=DL_PRODUCTS_VOT)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)
    conn_handler.set_response(
        '?DATA_STRUCTURE=INDIVIDUAL&FORMAT=votable&ID=5937083312263887616&RELEASE=Gaia+DR3&RETRIEVAL_TYPE=ALL'
        '&USE_ZIP_ALWAYS=true&VALID_DATA=false',
        launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_datalink_querier_ecsv():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=DL_PRODUCTS_ECSV)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)
    conn_handler.set_response(
        '?DATA_STRUCTURE=INDIVIDUAL&FORMAT=ecsv&ID=5937083312263887616&RELEASE=Gaia+DR3&RETRIEVAL_TYPE=ALL'
        '&USE_ZIP_ALWAYS=true&VALID_DATA=false',
        launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_datalink_querier_csv():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=DL_PRODUCTS_CSV)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)
    conn_handler.set_response(
        '?DATA_STRUCTURE=INDIVIDUAL&FORMAT=csv&ID=5937083312263887616&RELEASE=Gaia+DR3&RETRIEVAL_TYPE=ALL'
        '&USE_ZIP_ALWAYS=true&VALID_DATA=false',
        launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_datalink_querier_fits():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=DL_PRODUCTS_FITS)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)
    conn_handler.set_response(
        '?DATA_STRUCTURE=INDIVIDUAL&FORMAT=fits&ID=5937083312263887616&RELEASE=Gaia+DR3&RETRIEVAL_TYPE=ALL'
        '&USE_ZIP_ALWAYS=true&VALID_DATA=false',
        launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_ecsv():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA_ECSV)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_async():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    jobid = "12345"

    launch_response = DummyResponse(303)
    launch_response_headers = [["location", "http://test:1111/tap/async/" + jobid]]
    launch_response.set_data(method="POST", headers=launch_response_headers)
    conn_handler.set_default_response(launch_response)

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body="COMPLETED")
    conn_handler.set_response("async/" + jobid + "/phase", phase_response)

    results_response = DummyResponse(200)
    results_response.set_data(method="GET", body=JOB_DATA)
    conn_handler.set_response("async/" + jobid + "/results/result", results_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_async_names_new():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler, use_names_over_ids=True)
    jobid = "12345"

    launch_response = DummyResponse(303)
    launch_response_headers = [["location", "http://test:1111/tap/async/" + jobid]]
    launch_response.set_data(method="POST", headers=launch_response_headers)
    conn_handler.set_default_response(launch_response)

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body="COMPLETED")
    conn_handler.set_response("async/" + jobid + "/phase", phase_response)

    results_response = DummyResponse(200)
    results_response.set_data(method="GET", body=JOB_DATA_NEW)
    conn_handler.set_response("async/" + jobid + "/results/result", results_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_async_ids_new():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler, use_names_over_ids=False)
    jobid = "12345"

    launch_response = DummyResponse(303)
    launch_response_headers = [["location", "http://test:1111/tap/async/" + jobid]]
    launch_response.set_data(method="POST", headers=launch_response_headers)
    conn_handler.set_default_response(launch_response)

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body="COMPLETED")
    conn_handler.set_response("async/" + jobid + "/phase", phase_response)

    results_response = DummyResponse(200)
    results_response.set_data(method="GET", body=JOB_DATA_NEW)
    conn_handler.set_response("async/" + jobid + "/results/result", results_response)

    GaiaClass.USE_NAMES_OVER_IDS = False
    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_names_new():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler, use_names_over_ids=True)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA_QUERIER_ASYNC_JSON)
    conn_handler.set_default_response(launch_response)

    GaiaClass.USE_NAMES_OVER_IDS = True
    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_ids_new():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler, use_names_over_ids=False)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA_QUERIER_ASYNC_JSON)
    conn_handler.set_default_response(launch_response)

    GaiaClass.USE_NAMES_OVER_IDS = False
    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_cone_search_json():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA_CONE_SEARCH_ASYNC_JSON)
    conn_handler.set_default_response(launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_cone_search_async_json():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    jobid = "12345"

    launch_response = DummyResponse(303)
    launch_response_headers = [["location", "http://test:1111/tap/async/" + jobid]]
    launch_response.set_data(method="GET", headers=launch_response_headers, body=JOB_DATA_CONE_SEARCH_ASYNC_JSON)
    conn_handler.set_default_response(launch_response)

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body="COMPLETED")
    conn_handler.set_response("async/" + jobid + "/phase", phase_response)

    results_response = DummyResponse(200)
    results_response.set_data(method="GET", body=JOB_DATA)
    conn_handler.set_response("async/" + jobid + "/results/result", results_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_json():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA_QUERIER_ASYNC_JSON)
    conn_handler.set_default_response(launch_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_async_json():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    jobid = "12345"

    launch_response = DummyResponse(303)
    launch_response_headers = [["location", "http://test:1111/tap/async/" + jobid]]
    launch_response.set_data(method="GET", headers=launch_response_headers, body=JOB_DATA_QUERIER_ASYNC_JSON)
    conn_handler.set_default_response(launch_response)

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body="COMPLETED")
    conn_handler.set_response("async/" + jobid + "/phase", phase_response)

    results_response = DummyResponse(200)
    results_response.set_data(method="GET", body=JOB_DATA)
    conn_handler.set_response("async/" + jobid + "/results/result", results_response)

    return GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)


@pytest.fixture
def cross_match_kwargs():
    return {"full_qualified_table_name_a": "schemaA.tableA",
            "full_qualified_table_name_b": "schemaB.tableB",
            "results_table_name": "results"}


def test_show_message():
    print(JOB_DATA_FILE_NAME)
    connHandler = DummyConnHandler()

    dummy_response = DummyResponse(200)

    message_text = "1653401204784D[type: -100,-1]=Gaia dev is under maintenance"

    dummy_response.set_data(method='GET', body=message_text)
    connHandler.set_default_response(dummy_response)

    # show_server_messages
    tableRequest = 'notification?action=GetNotifications'
    connHandler.set_response(tableRequest, dummy_response)

    tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
    GaiaClass(tap_plus_conn_handler=connHandler, datalink_handler=tapplus, show_server_messages=True)


@pytest.mark.parametrize(
    "kwargs", [{"width": 12 * u.deg, "height": 10 * u.deg}, {"radius": RADIUS}])
def test_query_object(column_attrs, mock_querier, kwargs):
    table = mock_querier.query_object(SKYCOORD, **kwargs)
    assert len(table) == 3
    for colname, attrs in column_attrs.items():
        assert table[colname].attrs_equal(attrs)


@pytest.mark.parametrize(
    "kwargs,reported_missing", [({}, "width"), ({"width": 12 * u.deg}, "height")])
def test_query_object_missing_argument(kwargs, reported_missing):
    with pytest.raises(ValueError, match=f"^Missing required argument: {reported_missing}$"):
        GAIA_QUERIER.query_object(SKYCOORD, **kwargs)


@pytest.mark.parametrize(
    "kwargs", ({"width": 12 * u.deg, "height": 10 * u.deg}, {"radius": RADIUS}))
def test_query_object_async(column_attrs, mock_querier_async, kwargs):
    assert mock_querier_async.USE_NAMES_OVER_IDS is True

    table = mock_querier_async.query_object_async(SKYCOORD, **kwargs)
    assert len(table) == 3
    for colname, attrs in column_attrs.items():
        assert table[colname].attrs_equal(attrs)


def test_cone_search_sync(column_attrs, mock_querier):
    assert mock_querier.USE_NAMES_OVER_IDS is True

    job = mock_querier.cone_search(SKYCOORD, radius=RADIUS)
    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    # results
    results = job.get_results()
    assert len(results) == 3
    for col_name, attrs in column_attrs.items():
        assert results[col_name].attrs_equal(attrs)


def test_cone_search_sync_ecsv_format(column_attrs, mock_querier_ecsv):
    job = mock_querier_ecsv.cone_search(SKYCOORD, radius=RADIUS, output_format="ecsv")
    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    # results
    results = job.get_results()
    print(results)
    assert len(results) == 5

    assert results['designation'][0] == 'Gaia DR3 6636090334814214528'
    assert results['designation'][1] == 'Gaia DR3 6636090339112400000'


def test_cone_search_async(column_attrs, mock_querier_async):
    assert mock_querier_async.USE_NAMES_OVER_IDS is True

    job = mock_querier_async.cone_search_async(SKYCOORD, radius=RADIUS)
    assert job.async_ is True
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    # results
    results = job.get_results()
    assert len(results) == 3
    for col_name, attrs in column_attrs.items():
        assert results[col_name].attrs_equal(attrs)


def test_cone_search_async_json_format(tmp_path_factory, column_attrs_conesearch_json, mock_cone_search_async_json):
    d = tmp_path_factory.mktemp("data") / 'cone_search_async.json'
    d.write_text(JOB_DATA_CONE_SEARCH_ASYNC_JSON, encoding="utf-8")

    output_file = str(d)
    dump_to_file = True
    output_format = 'json'

    assert mock_cone_search_async_json.USE_NAMES_OVER_IDS is True

    job = mock_cone_search_async_json.cone_search_async(SKYCOORD, radius=RADIUS, output_file=output_file,
                                                        output_format=output_format, dump_to_file=dump_to_file,
                                                        verbose=True)
    assert job.async_ is True
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    # results
    results = job.get_results()

    assert type(results) is Table
    assert 50 == len(results), len(results)

    for col_name, attrs in column_attrs_conesearch_json.items():
        assert results[col_name].name == attrs.name
        assert results[col_name].description == attrs.description
        assert results[col_name].unit == attrs.unit
        assert results[col_name].dtype == attrs.dtype


def test_cone_search_json_format(tmp_path_factory, column_attrs_conesearch_json, mock_cone_search_json):
    d = tmp_path_factory.mktemp("data") / 'cone_search.json'
    d.write_text(JOB_DATA_CONE_SEARCH_ASYNC_JSON, encoding="utf-8")

    output_file = str(d)
    dump_to_file = True
    output_format = 'json'

    job = mock_cone_search_json.cone_search(SKYCOORD, radius=RADIUS, output_file=output_file,
                                            output_format=output_format, dump_to_file=dump_to_file,
                                            verbose=True)

    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    # results
    results = job.get_results()

    assert type(results) is Table
    assert 50 == len(results), len(results)

    for colname, attrs in column_attrs_conesearch_json.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_async_json_format(tmp_path_factory, column_attrs_launch_json, mock_querier_async_json):
    d = tmp_path_factory.mktemp("data") / 'launch_job_async.json'
    d.write_text(JOB_DATA_QUERIER_ASYNC_JSON, encoding="utf-8")

    output_file = str(d)
    dump_to_file = True
    output_format = 'json'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    job = mock_querier_async_json.launch_job_async(query, output_file=output_file, output_format=output_format,
                                                   dump_to_file=dump_to_file)

    assert job.async_ is True
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True
    # results
    results = job.get_results()

    assert type(results) is Table
    assert 1 == len(results), len(results)

    for colname, attrs in column_attrs_launch_json.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_json_format(tmp_path_factory, column_attrs_launch_json, mock_querier_json):
    d = tmp_path_factory.mktemp("data") / 'launch_job.json'
    d.write_text(JOB_DATA_QUERIER_ASYNC_JSON, encoding="utf-8")

    output_file = str(d)
    dump_to_file = True
    output_format = 'json'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    job = mock_querier_json.launch_job(query, output_file=output_file, output_format=output_format,
                                       dump_to_file=dump_to_file)

    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 1 == len(results), len(results)

    for colname, attrs in column_attrs_launch_json.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_json_format_no_dump(tmp_path_factory, column_attrs_launch_json, mock_querier_json):
    dump_to_file = False
    output_format = 'json'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    job = mock_querier_json.launch_job(query, output_format=output_format, dump_to_file=dump_to_file)

    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 1 == len(results), len(results)

    for colname, attrs in column_attrs_launch_json.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_async_vot_format_no_dump_names(tmp_path_factory, column_attrs_lower_case_new,
                                                   mock_querier_async_names_new):
    dump_to_file = False
    output_format = 'votable_plain'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    assert mock_querier_async_names_new.USE_NAMES_OVER_IDS is True

    job = mock_querier_async_names_new.launch_job_async(query, output_format=output_format, dump_to_file=dump_to_file)

    assert job.async_ is True
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 2 == len(results)

    print(results.columns)

    for colname, attrs in column_attrs_lower_case_new.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_async_vot_format_no_dump_ids(tmp_path_factory, column_attrs_upper_case_new,
                                                 mock_querier_async_ids_new):
    dump_to_file = False
    output_format = 'votable_plain'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    assert mock_querier_async_ids_new.USE_NAMES_OVER_IDS is False

    job = mock_querier_async_ids_new.launch_job_async(query, output_format=output_format, dump_to_file=dump_to_file)

    assert job.async_ is True
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is False

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 2 == len(results)

    print(results.columns)

    for colname, attrs in column_attrs_upper_case_new.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_vot_format_names(tmp_path_factory, column_attrs_lower_case_new, mock_querier_names_new):
    d = tmp_path_factory.mktemp("data") / 'launch_job.vot'
    d.write_text(JOB_DATA_NEW, encoding="utf-8")

    output_file = str(d)
    dump_to_file = True
    output_format = 'votable_plain'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    job = mock_querier_names_new.launch_job(query, output_file=output_file, output_format=output_format,
                                            dump_to_file=dump_to_file)

    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 2 == len(results)

    for colname, attrs in column_attrs_lower_case_new.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_launch_job_vot_format_ids(tmp_path_factory, column_attrs_upper_case_new, mock_querier_ids_new):
    d = tmp_path_factory.mktemp("data") / 'launch_job.vot'
    d.write_text(JOB_DATA_NEW, encoding="utf-8")

    output_file = str(d)
    dump_to_file = True
    output_format = 'votable_plain'
    query = "SELECT TOP 1 source_id, ra, dec, parallax from gaiadr3.gaia_source"

    job = mock_querier_ids_new.launch_job(query, output_file=output_file, output_format=output_format,
                                          dump_to_file=dump_to_file)

    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is False

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 2 == len(results)

    for colname, attrs in column_attrs_upper_case_new.items():
        assert results[colname].name == attrs.name
        assert results[colname].description == attrs.description
        assert results[colname].unit == attrs.unit
        assert results[colname].dtype == attrs.dtype


def test_cone_search_and_changing_MAIN_GAIA_TABLE(mock_querier_async):
    # Regression test for #2093 and #2099 - changing the MAIN_GAIA_TABLE
    # had no effect.
    job = mock_querier_async.cone_search_async(SKYCOORD, radius=RADIUS)
    assert 'gaiadr3.gaia_source' in job.parameters['query']
    with conf.set_temp("MAIN_GAIA_TABLE", "name_from_conf"):
        job = mock_querier_async.cone_search_async(SKYCOORD, radius=RADIUS)
        assert "name_from_conf" in job.parameters["query"]
        # Changing the value through the class should overrule conf.
        mock_querier_async.MAIN_GAIA_TABLE = "name_from_class"
        job = mock_querier_async.cone_search_async(SKYCOORD, radius=RADIUS)
        assert "name_from_class" in job.parameters["query"]


@pytest.mark.parametrize("overwrite_output_file", [True])
def test_datalink_querier_load_data_vot_exception(mock_datalink_querier, overwrite_output_file):
    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S") + '.zip'

    file_final = Path(os.getcwd(), output_file)

    Path(file_final).touch()

    assert os.path.exists(file_final)

    if not overwrite_output_file:

        with pytest.raises(ValueError) as excinfo:
            mock_datalink_querier.load_data(ids=[5937083312263887616], data_release='Gaia DR3',
                                            data_structure='INDIVIDUAL',
                                            retrieval_type="ALL",
                                            linking_parameter='SOURCE_ID', valid_data=False, band=None,
                                            avoid_datatype_check=False,
                                            format="votable", dump_to_file=True,
                                            overwrite_output_file=overwrite_output_file,
                                            verbose=False)

        assert str(
            excinfo.value) == (
                f"{file_final} file already exists. Please use overwrite_output_file='True' to overwrite output file.")

    else:
        mock_datalink_querier.load_data(ids=[5937083312263887616], data_release='Gaia DR3',
                                        data_structure='INDIVIDUAL',
                                        retrieval_type="ALL",
                                        linking_parameter='SOURCE_ID', valid_data=False, band=None,
                                        avoid_datatype_check=False,
                                        format="votable", dump_to_file=True,
                                        overwrite_output_file=overwrite_output_file,
                                        verbose=False)

    os.remove(file_final)

    assert not os.path.exists(file_final)


def test_datalink_querier_load_data_vot(mock_datalink_querier):
    result_dict = mock_datalink_querier.load_data(ids=[5937083312263887616], data_release='Gaia DR3',
                                                  data_structure='INDIVIDUAL',
                                                  retrieval_type="ALL",
                                                  linking_parameter='SOURCE_ID', valid_data=False, band=None,
                                                  avoid_datatype_check=False,
                                                  format="votable", dump_to_file=True, overwrite_output_file=True,
                                                  verbose=False)

    direc = os.getcwd()
    files = os.listdir(direc)
    # Filtering only the files.
    files = [f for f in files if
             Path(direc, f).is_file() and f.endswith(".zip") and f.startswith('datalink_output')]

    assert len(files) == 1
    datalink_output = files[0]

    extracted_files = []

    with zipfile.ZipFile(datalink_output, "r") as zip_ref:
        extracted_files.extend(zip_ref.namelist())

    assert len(extracted_files) == 3

    assert len(result_dict) == 3

    files = list(result_dict.keys())
    files.sort()
    assert files[0] == 'MCMC_MSC-Gaia DR3 5937083312263887616.xml'
    assert files[1] == 'XP_CONTINUOUS-Gaia DR3 5937083312263887616.xml'
    assert files[2] == 'XP_SAMPLED-Gaia DR3 5937083312263887616.xml'

    os.remove(os.path.join(os.getcwd(), datalink_output))

    assert not os.path.exists(os.path.join(os.getcwd(), datalink_output))


def test_datalink_querier_load_data_ecsv(mock_datalink_querier_ecsv):
    result_dict = mock_datalink_querier_ecsv.load_data(ids=[5937083312263887616], data_release='Gaia DR3',
                                                       data_structure='INDIVIDUAL',
                                                       retrieval_type="ALL",
                                                       linking_parameter='SOURCE_ID', valid_data=False, band=None,
                                                       avoid_datatype_check=False,
                                                       format="ecsv", dump_to_file=True, overwrite_output_file=True,
                                                       verbose=False)

    direc = os.getcwd()
    files = os.listdir(direc)
    # Filtering only the files.
    files = [f for f in files if
             Path(direc, f).is_file() and f.endswith(".zip") and f.startswith('datalink_output')]

    assert len(files) == 1
    datalink_output = files[0]

    extracted_files = []

    with zipfile.ZipFile(datalink_output, "r") as zip_ref:
        extracted_files.extend(zip_ref.namelist())

    assert len(extracted_files) == 3

    assert len(result_dict) == 3

    files = list(result_dict.keys())
    files.sort()
    assert files[0] == 'MCMC_MSC-Gaia DR3 5937083312263887616.ecsv'
    assert files[1] == 'XP_CONTINUOUS-Gaia DR3 5937083312263887616.ecsv'
    assert files[2] == 'XP_SAMPLED-Gaia DR3 5937083312263887616.ecsv'

    os.remove(os.path.join(os.getcwd(), datalink_output))

    assert not os.path.exists(datalink_output)


def test_datalink_querier_load_data_csv(mock_datalink_querier_csv):
    result_dict = mock_datalink_querier_csv.load_data(ids=[5937083312263887616], data_release='Gaia DR3',
                                                      data_structure='INDIVIDUAL',
                                                      retrieval_type="ALL",
                                                      linking_parameter='SOURCE_ID', valid_data=False, band=None,
                                                      avoid_datatype_check=False,
                                                      format="csv", dump_to_file=True, overwrite_output_file=True,
                                                      verbose=False)

    direc = os.getcwd()
    files = os.listdir(direc)
    # Filtering only the files.
    files = [f for f in files if
             Path(direc, f).is_file() and f.endswith(".zip") and f.startswith('datalink_output')]

    assert len(files) == 1
    datalink_output = files[0]

    extracted_files = []

    with zipfile.ZipFile(datalink_output, "r") as zip_ref:
        extracted_files.extend(zip_ref.namelist())

    assert len(extracted_files) == 3

    assert len(result_dict) == 3

    files = list(result_dict.keys())
    files.sort()
    assert files[0] == 'MCMC_MSC-Gaia DR3 5937083312263887616.csv'
    assert files[1] == 'XP_CONTINUOUS-Gaia DR3 5937083312263887616.csv'
    assert files[2] == 'XP_SAMPLED-Gaia DR3 5937083312263887616.csv'

    os.remove(os.path.join(os.getcwd(), datalink_output))

    assert not os.path.exists(datalink_output)


@pytest.mark.skip(reason="Thes fits files generate an error relatate to the unit 'log(cm.s**-2)")
def test_datalink_querier_load_data_fits(mock_datalink_querier_fits):
    result_dict = mock_datalink_querier_fits.load_data(ids=[5937083312263887616], data_release='Gaia DR3',
                                                       data_structure='INDIVIDUAL',
                                                       retrieval_type="ALL",
                                                       linking_parameter='SOURCE_ID', valid_data=False, band=None,
                                                       avoid_datatype_check=False,
                                                       format="fits", dump_to_file=True, overwrite_output_file=True,
                                                       verbose=False)

    direc = os.getcwd()
    files = os.listdir(direc)
    # Filtering only the files.
    files = [f for f in files if
             Path(direc, f).is_file() and f.endswith(".zip") and f.startswith('datalink_output')]

    assert len(files) == 1
    datalink_output = files[0]

    extracted_files = []

    with zipfile.ZipFile(datalink_output, "r") as zip_ref:
        extracted_files.extend(zip_ref.namelist())

    assert len(extracted_files) == 3

    assert len(result_dict) == 3

    files = list(result_dict.keys())
    files.sort()
    assert files[0] == 'MCMC_MSC-Gaia DR3 5937083312263887616.fits'
    assert files[1] == 'XP_CONTINUOUS-Gaia DR3 5937083312263887616.fits'
    assert files[2] == 'XP_SAMPLED-Gaia DR3 5937083312263887616.fits'

    os.remove(os.path.join(os.getcwd(), datalink_output))

    assert not os.path.exists(datalink_output)


def test_load_data_vot(monkeypatch, tmp_path, tmp_path_factory, patch_datetime_now):

    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S.%f") + '.zip'

    path = Path(os.getcwd(), output_file)

    with open(DL_PRODUCTS_VOT, 'rb') as file:
        zip_bytes = file.read()

    path.write_bytes(zip_bytes)

    def load_data_monkeypatched(self, params_dict, output_file, verbose):
        assert params_dict == {
            "VALID_DATA": "true",
            "ID": "1,2,3,4",
            "FORMAT": "votable",
            "RETRIEVAL_TYPE": "epoch_photometry",
            "DATA_STRUCTURE": "INDIVIDUAL",
            "USE_ZIP_ALWAYS": "true"}
        assert str(path) == output_file
        assert verbose is True

    monkeypatch.setattr(TapPlus, "load_data", load_data_monkeypatched)

    # Keep the tests, just remove the argument once the deprecation is removed
    with pytest.warns(AstropyDeprecationWarning,
                      match='"output_file" was deprecated in version 0.4.8'):
        GAIA_QUERIER.load_data(
            valid_data=True,
            ids="1,2,3,4",
            format='votable',
            retrieval_type="epoch_photometry",
            verbose=True,
            dump_to_file=True,
            overwrite_output_file=True,
            output_file=tmp_path / "output_file")

    path.unlink()


@pytest.mark.skip(reason="Thes fits files generate an error relatate to the unit 'log(cm.s**-2)")
def test_load_data_fits(monkeypatch, tmp_path, tmp_path_factory):
    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S") + '.zip'

    path = Path(os.getcwd(), output_file)

    with open(DL_PRODUCTS_FITS, 'rb') as file:
        zip_bytes = file.read()

    path.write_bytes(zip_bytes)

    def load_data_monkeypatched(self, params_dict, output_file, verbose):
        assert params_dict == {
            "VALID_DATA": "true",
            "ID": "1,2,3,4",
            "FORMAT": "fits",
            "RETRIEVAL_TYPE": "epoch_photometry",
            "DATA_STRUCTURE": "INDIVIDUAL",
            "USE_ZIP_ALWAYS": "true"}
        assert output_file == Path(os.getcwd(), 'datalink_output.zip')
        assert verbose is True

    monkeypatch.setattr(TapPlus, "load_data", load_data_monkeypatched)

    GAIA_QUERIER.load_data(
        valid_data=True,
        ids="1,2,3,4",
        format='fits',
        retrieval_type="epoch_photometry",
        verbose=True,
        dump_to_file=True,
        overwrite_output_file=True)

    path.unlink()


def test_load_data_csv(monkeypatch, tmp_path, tmp_path_factory, patch_datetime_now):

    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S.%f") + '.zip'

    path = Path(os.getcwd(), output_file)

    with open(DL_PRODUCTS_CSV, 'rb') as file:
        zip_bytes = file.read()

    path.write_bytes(zip_bytes)

    def load_data_monkeypatched(self, params_dict, output_file, verbose):
        assert params_dict == {
            "VALID_DATA": "true",
            "ID": "1,2,3,4",
            "FORMAT": "csv",
            "RETRIEVAL_TYPE": "epoch_photometry",
            "DATA_STRUCTURE": "INDIVIDUAL",
            "USE_ZIP_ALWAYS": "true"}
        assert str(path) == output_file
        assert verbose is True

    monkeypatch.setattr(TapPlus, "load_data", load_data_monkeypatched)

    GAIA_QUERIER.load_data(
        valid_data=True,
        ids="1,2,3,4",
        format='csv',
        retrieval_type="epoch_photometry",
        verbose=True,
        dump_to_file=True,
        overwrite_output_file=True)

    path.unlink()


def test_load_data_ecsv(monkeypatch, tmp_path, tmp_path_factory, patch_datetime_now):

    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S.%f") + '.zip'

    path = Path(os.getcwd(), output_file)

    with open(DL_PRODUCTS_ECSV, 'rb') as file:
        zip_bytes = file.read()

    path.write_bytes(zip_bytes)

    def load_data_monkeypatched(self, params_dict, output_file, verbose):
        assert params_dict == {
            "VALID_DATA": "true",
            "ID": "1,2,3,4",
            "FORMAT": "ecsv",
            "RETRIEVAL_TYPE": "epoch_photometry",
            "DATA_STRUCTURE": "INDIVIDUAL",
            "USE_ZIP_ALWAYS": "true"}
        assert str(path) == output_file
        assert verbose is True

    monkeypatch.setattr(TapPlus, "load_data", load_data_monkeypatched)

    GAIA_QUERIER.load_data(
        valid_data=True,
        ids="1,2,3,4",
        format='ecsv',
        retrieval_type="epoch_photometry",
        verbose=True,
        dump_to_file=True,
        overwrite_output_file=True)

    path.unlink()


def test_load_data_linking_parameter(monkeypatch, tmp_path, patch_datetime_now):

    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S.%f") + '.zip'

    path = Path(os.getcwd(), output_file)

    with open(DL_PRODUCTS_VOT, 'rb') as file:
        zip_bytes = file.read()

    path.write_bytes(zip_bytes)

    def load_data_monkeypatched(self, params_dict, output_file, verbose):
        assert params_dict == {
            "VALID_DATA": "true",
            "ID": "1,2,3,4",
            "FORMAT": "votable",
            "RETRIEVAL_TYPE": "epoch_photometry",
            "DATA_STRUCTURE": "INDIVIDUAL",
            "USE_ZIP_ALWAYS": "true"}
        assert str(path) == output_file
        assert verbose is True

    monkeypatch.setattr(TapPlus, "load_data", load_data_monkeypatched)

    GAIA_QUERIER.load_data(
        ids="1,2,3,4",
        retrieval_type="epoch_photometry",
        linking_parameter="SOURCE_ID",
        valid_data=True,
        verbose=True,
        dump_to_file=True,
        overwrite_output_file=True)

    path.unlink()


@pytest.mark.parametrize("linking_param", ['TRANSIT_ID', 'IMAGE_ID'])
def test_load_data_linking_parameter_with_values(monkeypatch, tmp_path, linking_param, patch_datetime_now):

    assert datetime.datetime.now(datetime.timezone.utc) == FAKE_TIME

    now = datetime.datetime.now(datetime.timezone.utc)
    output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S.%f") + '.zip'

    path = Path(os.getcwd(), output_file)

    with open(DL_PRODUCTS_VOT, 'rb') as file:
        zip_bytes = file.read()

    path.write_bytes(zip_bytes)

    def load_data_monkeypatched(self, params_dict, output_file, verbose):
        direc = os.getcwd()
        files = os.listdir(direc)
        # Filtering only the files.
        files = [f for f in files if
                 Path(direc, f).is_file() and f.endswith(".zip") and f.startswith('datalink_output')]

        assert len(files) == 1
        datalink_output = files[0]

        assert params_dict == {
            "VALID_DATA": "true",
            "ID": "1,2,3,4",
            "FORMAT": "votable",
            "RETRIEVAL_TYPE": "epoch_photometry",
            "DATA_STRUCTURE": "INDIVIDUAL",
            "LINKING_PARAMETER": linking_param,
            "USE_ZIP_ALWAYS": "true", }
        assert output_file == str(Path(os.getcwd(), datalink_output))
        assert verbose is True

    monkeypatch.setattr(TapPlus, "load_data", load_data_monkeypatched)

    GAIA_QUERIER.load_data(
        ids="1,2,3,4",
        retrieval_type="epoch_photometry",
        linking_parameter=linking_param,
        valid_data=True,
        verbose=True,
        dump_to_file=True,
        overwrite_output_file=True)

    path.unlink()


def test_get_datalinks(monkeypatch):
    def get_datalinks_monkeypatched(self, ids, linking_parameter, verbose):
        return Table()

    # `GaiaClass` is a subclass of `TapPlus`, but it does not inherit
    # `get_datalinks()`, it replaces it with a call to the `get_datalinks()`
    # of its `__gaiadata`.
    monkeypatch.setattr(TapPlus, "get_datalinks", get_datalinks_monkeypatched)
    result = GAIA_QUERIER.get_datalinks(ids=["1", "2", "3", "4"], verbose=True)
    assert isinstance(result, Table)


@pytest.mark.parametrize("linking_param", ['SOURCE_ID', 'TRANSIT_ID', 'IMAGE_ID'])
def test_get_datalinks_linking_parameter(monkeypatch, linking_param):
    def get_datalinks_monkeypatched(self, ids, linking_parameter, verbose):
        return Table()

    # `GaiaClass` is a subclass of `TapPlus`, but it does not inherit
    # `get_datalinks()`, it replaces it with a call to the `get_datalinks()`
    # of its `__gaiadata`.
    monkeypatch.setattr(TapPlus, "get_datalinks", get_datalinks_monkeypatched)
    result = GAIA_QUERIER.get_datalinks(ids=["1", "2", "3", "4"], linking_parameter=linking_param, verbose=True)
    assert isinstance(result, Table)


@pytest.mark.parametrize("id_int", ids_ints)
def test_get_datalinks_linking_parameter_ids_int(monkeypatch, id_int):
    def get_datalinks_monkeypatched(self, ids, linking_parameter, verbose):
        return Table()

    # `GaiaClass` is a subclass of `TapPlus`, but it does not inherit
    # `get_datalinks()`, it replaces it with a call to the `get_datalinks()`
    # of its `__gaiadata`.
    monkeypatch.setattr(TapPlus, "get_datalinks", get_datalinks_monkeypatched)
    result = GAIA_QUERIER.get_datalinks(ids=id_int, verbose=True)
    assert isinstance(result, Table)


@pytest.mark.parametrize("id_des", ids_designator)
def test_get_datalinks_linking_parameter_ids_designator(monkeypatch, id_des):
    def get_datalinks_monkeypatched(self, ids, linking_parameter, verbose):
        return Table()

    # `GaiaClass` is a subclass of `TapPlus`, but it does not inherit
    # `get_datalinks()`, it replaces it with a call to the `get_datalinks()`
    # of its `__gaiadata`.
    monkeypatch.setattr(TapPlus, "get_datalinks", get_datalinks_monkeypatched)
    result = GAIA_QUERIER.get_datalinks(ids=id_des, verbose=True)
    assert isinstance(result, Table)


def test_get_datalinks_exception(monkeypatch):
    def get_datalinks_monkeypatched(self, ids, linking_parameter, verbose):
        return Table()

    linking_parameter = 'NOT_VALID'
    # `GaiaClass` is a subclass of `TapPlus`, but it does not inherit
    # `get_datalinks()`, it replaces it with a call to the `get_datalinks()`
    # of its `__gaiadata`.
    monkeypatch.setattr(TapPlus, "get_datalinks", get_datalinks_monkeypatched)

    with pytest.raises(ValueError, match=f"^Invalid linking_parameter value '{linking_parameter}' .*"):
        GAIA_QUERIER.get_datalinks(ids=["1", "2", "3", "4"], linking_parameter=linking_parameter, verbose=True)


@pytest.mark.parametrize("background", [False, True])
def test_cross_match(background, cross_match_kwargs, mock_querier_async):
    job = mock_querier_async.cross_match(**cross_match_kwargs, background=background)
    assert job.async_ is True
    assert job.get_phase() == "EXECUTING" if background else "COMPLETED"
    assert job.failed is False


@pytest.mark.parametrize(
    "kwarg,invalid_value,error_message",
    [("full_qualified_table_name_a",
      "tableA",
      "^Not found schema name in full qualified table A: 'tableA'$"),
     ("full_qualified_table_name_b",
      "tableB",
      "^Not found schema name in full qualified table B: 'tableB'$"),
     ("results_table_name",
      "schema.results",
      "^Please, do not specify schema for 'results_table_name'$")])
def test_cross_match_invalid_mandatory_kwarg(
        cross_match_kwargs, kwarg, invalid_value, error_message
):
    cross_match_kwargs[kwarg] = invalid_value
    with pytest.raises(ValueError, match=error_message):
        GAIA_QUERIER.cross_match(**cross_match_kwargs)


@pytest.mark.parametrize("radius", [0.01, 10.1])
def test_cross_match_invalid_radius(cross_match_kwargs, radius):
    with pytest.raises(
            ValueError,
            match=rf"^Invalid radius value. Found {radius}, valid range is: 0.1 to 10.0$",
    ):
        GAIA_QUERIER.cross_match(**cross_match_kwargs, radius=radius)


@pytest.mark.parametrize(
    "missing_kwarg",
    ["full_qualified_table_name_a", "full_qualified_table_name_b", "results_table_name"])
def test_cross_match_missing_mandatory_kwarg(cross_match_kwargs, missing_kwarg):
    del cross_match_kwargs[missing_kwarg]
    with pytest.raises(
            TypeError, match=rf"missing 1 required keyword-only argument: '{missing_kwarg}'$"
    ):
        GAIA_QUERIER.cross_match(**cross_match_kwargs)


@patch.object(TapPlus, 'login')
def test_login(mock_login):
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    tap = GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)
    tap.login(user="user", password="password")
    assert (mock_login.call_count == 2)
    mock_login.side_effect = HTTPError("Login error")
    tap.login(user="user", password="password")
    assert (mock_login.call_count == 3)


@patch.object(TapPlus, 'login_gui')
@patch.object(TapPlus, 'login')
def test_login_gui(mock_login_gui, mock_login):
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    tap = GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)
    tap.login_gui()
    assert (mock_login_gui.call_count == 1)
    mock_login_gui.side_effect = HTTPError("Login error")
    tap.login(user="user", password="password")
    assert (mock_login.call_count == 1)


@patch.object(TapPlus, 'logout')
def test_logout(mock_logout):
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    tap = GaiaClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)
    tap.logout()
    assert (mock_logout.call_count == 2)
    mock_logout.side_effect = HTTPError("Login error")
    tap.logout()
    assert (mock_logout.call_count == 3)
