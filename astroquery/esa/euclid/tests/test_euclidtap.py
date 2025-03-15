# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
Euclid TAP plus
===============
European Space Astronomy Centre (ESAC)
European Space Agency (ESA)
"""
import glob
import os
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import astropy.units as u
import numpy as np
import pytest
from astropy import coordinates
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.table import Column, Table
from astropy.utils.data import get_pkg_data_filename
from requests import HTTPError

from astroquery.esa.euclid.core import EuclidClass
from astroquery.esa.euclid.core import conf
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.core import TapPlus

package = "astroquery.esa.euclid.tests"

JOB_DATA_FILE_NAME = get_pkg_data_filename(os.path.join("data", 'job_1.vot'), package=package)
JOB_DATA = Path(JOB_DATA_FILE_NAME).read_text()

JOB_ASYNC_FILE_NAME = get_pkg_data_filename(os.path.join("data", 'jobs.xml'), package=package)
JOBS_ASYNC_DATA = Path(JOB_ASYNC_FILE_NAME).read_text()

TABLE_FILE_NAME = get_pkg_data_filename(os.path.join("data", '1714556098855O-result.vot'), package=package)
TABLE_DATA = Path(TABLE_FILE_NAME).read_text()

RADIUS = 1 * u.deg
SKYCOORD = SkyCoord(ra=19 * u.deg, dec=20 * u.deg, frame="icrs")

PRODUCT_LIST_FILE_NAME = get_pkg_data_filename(os.path.join("data", 'test_get_product_list.vot'), package=package)
TEST_GET_PRODUCT_LIST = Path(PRODUCT_LIST_FILE_NAME).read_text()


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    yield
    remove_temp_dir()


@pytest.fixture(scope="module")
def mock_querier():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA)
    # The query contains decimals: default response is more robust.
    conn_handler.set_default_response(launch_response)

    return EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)


@pytest.fixture(scope="module")
def mock_querier_async():
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    cutout_handler = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
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

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body=JOBS_ASYNC_DATA)
    conn_handler.set_response("async/1479386030738O", phase_response)

    phase_response = DummyResponse(200)
    phase_response.set_data(method="GET", body="COMPLETED")
    conn_handler.set_response("async/1479386030738O/phase", phase_response)

    results_response = DummyResponse(200)
    results_response.set_data(method="GET", body=JOB_DATA)
    conn_handler.set_response("async/1479386030738O/results/result", results_response)

    return EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, cutout_handler=cutout_handler,
                       show_server_messages=False)


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


def test_load_environments():
    tap = EuclidClass(environment='PDR')

    assert tap is not None

    tap = EuclidClass(environment='IDR')

    assert tap is not None

    tap = EuclidClass(environment='OTF')

    assert tap is not None

    tap = EuclidClass(environment='REG')

    assert tap is not None

    environment = 'WRONG'
    try:
        tap = EuclidClass(environment='WRONG')
    except Exception as e:
        assert str(e).startswith(f"Invalid environment {environment}. Valid values: {list(conf.ENVIRONMENTS.keys())}")


def test_query_async_object(column_attrs, mock_querier_async):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier_async.query_object(coordinate=coord, width=u.Quantity(0.1, u.deg),
                                            height=u.Quantity(0.1, u.deg), async_job=True)

    assert table is not None

    assert len(table) == 3
    for colname, attrs in column_attrs.items():
        assert table[colname].attrs_equal(attrs)


def test_query_async_object_columns(column_attrs, mock_querier_async):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier_async.query_object(coordinate=coord, width=u.Quantity(0.1, u.deg),
                                            height=u.Quantity(0.1, u.deg), columns=("alpha",), async_job=True)

    assert table is not None

    assert len(table) == 3

    assert table["alpha"].attrs_equal(column_attrs["alpha"])


def test_query_object(column_attrs, mock_querier):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier.query_object(coordinate=coord, width=u.Quantity(0.1, u.deg),
                                      height=u.Quantity(0.1, u.deg))

    assert table is not None

    assert len(table) == 3
    for colname, attrs in column_attrs.items():
        assert table[colname].attrs_equal(attrs)


def test_query_object_columns(column_attrs, mock_querier):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier.query_object(coordinate=coord, width=u.Quantity(0.1, u.deg),
                                      height=u.Quantity(0.1, u.deg), columns=("alpha",))

    assert table is not None

    assert len(table) == 3
    assert table["alpha"].attrs_equal(column_attrs["alpha"])


def test_query_object_async_radius(column_attrs, mock_querier_async):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier_async.query_object(coordinate=coord, radius=RADIUS, async_job=True)

    assert table is not None

    assert len(table) == 3
    for colname, attrs in column_attrs.items():
        assert table[colname].attrs_equal(attrs)

        def test_query_object_radius(column_attrs, mock_querier):
            coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
            table = mock_querier.query_object(coordinate=coord, radius=RADIUS)

            assert table is not None

            assert len(table) == 3
            for colname, attrs in column_attrs.items():
                assert table[colname].attrs_equal(attrs)


def test_query_object_async_radius_columns(column_attrs, mock_querier_async):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier_async.query_object(coordinate=coord, radius=RADIUS, columns=("alpha",), async_job=True)

    assert table is not None

    assert len(table) == 3
    assert table["alpha"].attrs_equal(column_attrs["alpha"])


def test_query_object_radius(column_attrs, mock_querier):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier.query_object(coordinate=coord, radius=RADIUS)

    assert table is not None

    assert len(table) == 3
    for colname, attrs in column_attrs.items():
        assert table[colname].attrs_equal(attrs)


def test_query_object_radius_columns(column_attrs, mock_querier):
    coord = SkyCoord(ra=60.3372780005097, dec=-49.93184727724773, unit=(u.degree, u.degree), frame='icrs')
    table = mock_querier.query_object(coordinate=coord, radius=RADIUS, columns=("alpha",))

    assert table is not None

    assert len(table) == 3
    assert table["alpha"].attrs_equal(column_attrs["alpha"])


def test_load_tables():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='GET', context=None, body=TABLE_DATA, headers=None)

    conn_handler.set_response("tables", responseLaunchJob)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    table = tap.load_tables()

    assert table is not None

    conn_handler.set_response('tables?only_tables=true&share_accessible=true', responseLaunchJob)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    table = tap.load_tables(only_names=True, include_shared_tables=True, verbose=True)

    assert table is not None


def test_load_table():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='GET', context=None, body=TABLE_DATA, headers=None)

    table = 'my_table'
    conn_handler.set_response(f"tables?tables={table}", responseLaunchJob)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    table = tap.load_table(table)

    assert table is not None


def test_launch_sync_job(tmp_path_factory):
    query = "select alpha, delta, source_id, table1_oid from caca"

    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA)
    conn_handler.set_default_response(launch_response)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    job = tap.launch_job(query, output_format="votable")

    assert job is not None
    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 3 == len(results), len(results)

    # test with parameters
    d = tmp_path_factory.mktemp("data") / 'job_1.vot'
    d.write_text(JOB_DATA, encoding="utf-8")

    name = 'name'
    output_file = str(d)
    output_format = 'votable'
    verbose = True
    dump_to_file = True

    job = tap.launch_job(query,
                         name=name,
                         output_file=output_file,
                         output_format=output_format,
                         verbose=verbose,
                         dump_to_file=dump_to_file)

    assert job is not None
    assert job.async_ is False
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 3 == len(results), len(results)


@patch.object(TapPlus, 'launch_job')
def test_launch_sync_job_exception(mock_launch_job, caplog):
    query = "select alpha, delta, source_id, table1_oid from caca"

    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    launch_response = DummyResponse(200)
    launch_response.set_data(method="POST", body=JOB_DATA)
    conn_handler.set_default_response(launch_response)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    mock_launch_job.side_effect = HTTPError("launch_job HTTPError")

    tap.launch_job(query, output_format="votable")

    mssg = "Query failed: select alpha, delta, source_id, table1_oid from caca: HTTP error: launch_job HTTPError"
    assert caplog.records[0].msg == mssg

    mock_launch_job.side_effect = Exception("launch_job Exception")

    tap.launch_job(query, output_format="votable")

    mssg = "Query failed: select alpha, delta, source_id, table1_oid from caca, launch_job Exception"
    assert caplog.records[1].msg == mssg


def test_launch_async_job():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    jobid = '12345'

    # Launch response
    responseLaunchJob = DummyResponse(303)
    # list of list (httplib implementation for headers in response)
    launchResponseHeaders = [['location', 'http://test:1111/tap/async/' + jobid]]
    responseLaunchJob.set_data(method='POST', headers=launchResponseHeaders)
    conn_handler.set_default_response(responseLaunchJob)

    # Phase response
    responsePhase = DummyResponse(200)
    responsePhase.set_data(method='GET', body="COMPLETED")
    req = "async/" + jobid + "/phase"
    conn_handler.set_response(req, responsePhase)

    # Results response
    responseResultsJob = DummyResponse(200)
    responseResultsJob.set_data(method='GET', body=JOB_DATA)
    req = "async/" + jobid + "/results/result"
    conn_handler.set_response(req, responseResultsJob)

    query = "select alpha, delta, source_id, table1_oid from caca"

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    job = tap.launch_job_async(query, output_format="votable")

    assert job is not None
    assert job.async_ is True
    assert job.get_phase() == "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 3 == len(results), len(results)

    # test with parameters
    name = 'name'
    output_file = 'output'
    output_format = 'votable'
    verbose = True
    dump_to_file = True
    background = True

    job = tap.launch_job_async(query,
                               name=name,
                               output_file=output_file,
                               output_format=output_format,
                               verbose=verbose,
                               dump_to_file=dump_to_file,
                               background=background)

    assert job is not None
    assert job.async_ is True
    assert job.get_phase() == "EXECUTING" if background else "COMPLETED"
    assert job.failed is False
    assert job.use_names_over_ids is True

    # results
    results = job.get_results()

    assert type(results) is Table
    assert 3 == len(results), len(results)


@patch.object(TapPlus, 'launch_job_async')
def test_launch_async_job_exception(mock_launch_job_async, caplog):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)
    query = "select alpha, delta, source_id, table1_oid from caca"

    mock_launch_job_async.side_effect = HTTPError("launch_job_async HTTPError")

    tap.launch_job_async(query, output_format="votable")

    mssg = "Query failed: select alpha, delta, source_id, table1_oid from caca: HTTP error: launch_job_async HTTPError"
    assert caplog.records[0].msg == mssg

    mock_launch_job_async.side_effect = Exception("launch_job_async Exception")

    tap.launch_job_async(query, output_format="votable")

    mssg = "Query failed: select alpha, delta, source_id, table1_oid from caca, launch_job_async Exception"
    assert caplog.records[1].msg == mssg


def test_list_async_jobs():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='GET', context=None, body=JOBS_ASYNC_DATA, headers=None)

    conn_handler.set_default_response(responseLaunchJob)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    jobs = tap.list_async_jobs()

    assert jobs is not None
    assert 0 == len(jobs), len(jobs)


def test_cone_search_sync():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body=JOB_DATA, headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    job = tap.cone_search(SKYCOORD, radius=RADIUS, output_format='votable')
    assert job is not None, "Expected a valid job"
    assert job.async_ is False, "Expected a synchronous job"
    assert job.get_phase() == 'COMPLETED', "Wrong job phase. Expected: %s, found %s" % (
        'COMPLETED', job.get_phase())
    assert job.failed is False, "Wrong job status (set Failed = True)"
    # results
    results = job.get_results()
    assert len(results) == 3, "Wrong job results (num rows). Expected: %d, found %d" % (3, len(results))
    __check_results_column(results, 'alpha', 'alpha', None, np.float64)
    __check_results_column(results, 'delta', 'delta', None, np.float64)
    __check_results_column(results, 'source_id', 'source_id', None, object)
    __check_results_column(results, 'table1_oid', 'table1_oid', None, np.int32)


def test_cone_search_async():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    jobid = '12345'

    # Launch response
    responseLaunchJob = DummyResponse(303)
    # list of list (httplib implementation for headers in response)
    launchResponseHeaders = [['location', 'http://test:1111/tap/async/' + jobid]]
    responseLaunchJob.set_data(method='POST', headers=launchResponseHeaders)
    conn_handler.set_default_response(responseLaunchJob)

    # Phase response
    responsePhase = DummyResponse(200)
    responsePhase.set_data(method='GET', body="COMPLETED")
    req = "async/" + jobid + "/phase"
    conn_handler.set_response(req, responsePhase)

    # Results response
    responseResultsJob = DummyResponse(200)
    responseResultsJob.set_data(method='GET', body=JOB_DATA)
    req = "async/" + jobid + "/results/result"
    conn_handler.set_response(req, responseResultsJob)

    euclid = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)
    job = euclid.cone_search(SKYCOORD, radius=RADIUS, async_job=True, output_format='votable')

    assert job is not None, "Expected a valid job"
    assert job.async_ is True, "Expected an asynchronous job"
    assert job.get_phase() == 'COMPLETED', \
        "Wrong job phase. Expected: %s, found %s" % \
        ('COMPLETED', job.get_phase())
    assert job.failed is False, "Wrong job status (set Failed = True)"
    # results
    results = job.get_results()
    assert len(results) == 3, "Wrong job results (num rows). Expected: %d, found %d" % (3, len(results))
    __check_results_column(results, 'alpha', 'alpha', None, np.float64)
    __check_results_column(results, 'delta', 'delta', None, np.float64)
    __check_results_column(results, 'source_id', 'source_id', None, object)
    __check_results_column(results, 'table1_oid', 'table1_oid', None, np.int32)


def __check_results_column(results, columnName, description, unit, dataType):
    c = results[columnName]
    assert c.description == description, \
        "Wrong description for results column '%s'. Expected: '%s', found '%s'" % (
            columnName, description, c.description)
    assert c.unit == unit, "Wrong unit for results column '%s'. Expected: '%s', found '%s'" % (
        columnName, unit, c.unit)
    assert c.dtype == dataType, \
        "Wrong dataType for results column '%s'. Expected: '%s', found '%s'" % (columnName, dataType, c.dtype)


def test_get_product_list():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body=TEST_GET_PRODUCT_LIST, headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)
    results = tap.get_product_list(observation_id='13', product_type='DpdNirStackedFrame')
    # results
    assert results is not None, "Expected a valid table"

    assert len(results) == 4, "Wrong job results (num rows). Expected: %d, found %d" % (4, len(results))
    __check_results_column(results, 'observation_id', None, None, np.dtype('<U255'))
    __check_results_column(results, 'observation_stk_oid', None, None, np.int64)

    for product_type in conf.OBSERVATION_STACK_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.BASIC_DOWNLOAD_DATA_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.MER_SEGMENTATION_MAP_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.RAW_FRAME_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.CALIBRATED_FRAME_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.FRAME_CATALOG_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.COMBINED_SPECTRA_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.SIR_SCIENCE_FRAME_PRODUCTS:
        results = tap.get_product_list(observation_id='13', product_type=product_type)
        assert results is not None, "Expected a valid table"


def test_get_product_list_by_tile_index():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body=TEST_GET_PRODUCT_LIST, headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)
    results = tap.get_product_list(tile_index='13', product_type='DpdMerBksMosaic')
    # results
    assert results is not None, "Expected a valid table"

    assert len(results) == 4, "Wrong job results (num rows). Expected: %d, found %d" % (4, len(results))
    __check_results_column(results, 'observation_id', None, None, np.dtype('<U255'))
    __check_results_column(results, 'observation_stk_oid', None, None, np.int64)

    for product_type in conf.MOSAIC_PRODUCTS:
        results = tap.get_product_list(tile_index='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.BASIC_DOWNLOAD_DATA_PRODUCTS:
        results = tap.get_product_list(tile_index='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.COMBINED_SPECTRA_PRODUCTS:
        results = tap.get_product_list(tile_index='13', product_type=product_type)
        assert results is not None, "Expected a valid table"

    for product_type in conf.MER_SEGMENTATION_MAP_PRODUCTS:
        results = tap.get_product_list(tile_index='13', product_type=product_type)
        assert results is not None, "Expected a valid table"


def test_get_product_list_errors():
    tap = EuclidClass()

    with pytest.raises(ValueError, match="Missing required argument: 'product_type'"):
        tap.get_product_list(observation_id='13', product_type=None)

    with pytest.raises(ValueError,
                       match="Missing required argument: 'observation_id'; Missing required argument: 'tile_id'"):
        tap.get_product_list(observation_id=None, tile_index=None, product_type='DpdNirStackedFrame')

    with pytest.raises(ValueError, match="Incompatible: 'observation_id' and 'tile_id'. Use only one."):
        tap.get_product_list(observation_id='13', tile_index='13', product_type='DpdNirStackedFrame')

    with pytest.raises(ValueError, match="Invalid product type DpdNirStackedFrame."):
        tap.get_product_list(tile_index='13', product_type='DpdNirStackedFrame')

    with pytest.raises(ValueError, match="Missing required argument: 'product_type'"):
        tap.get_product_list(tile_index='13', product_type=None)

    with pytest.raises(ValueError, match="Invalid product type DpdMerBksMosaic."):
        tap.get_product_list(observation_id='13', product_type='DpdMerBksMosaic')


def test_get_product_by_product_id(tmp_path_factory):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    result = tap.get_product(product_id='123456789', output_file=None)

    assert result is not None

    now = datetime.now()
    dirs = glob.glob(os.path.join(os.getcwd(), "temp_" + now.strftime("%Y%m%d") + '_*'))

    assert len(dirs) == 1
    assert dirs[0] is not None

    remove_temp_dir()

    fits_file = os.path.join(tmp_path_factory.mktemp("euclid_tmp"), 'my_fits_file.fits')

    result = tap.get_product(product_id='123456789', output_file=fits_file)

    assert result is not None


def test_get_product():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    result = tap.get_product(file_name='EUC_SIM_NISRGS180-8-1_20220722T094150.427Z_PV023_NISP-S_8_18_0.fits',
                             output_file=None)

    assert result is not None

    now = datetime.now()
    dirs = glob.glob(os.path.join(os.getcwd(), "temp_" + now.strftime("%Y%m%d") + '_*'))

    assert len(dirs) == 1
    assert dirs[0] is not None

    remove_temp_dir()


def test_get_product_exceptions():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    with pytest.raises(ValueError, match="'file_name' and 'product_id' are both None"):
        tap.get_product(file_name=None, product_id=None, output_file=None)


@patch.object(TapPlus, 'load_data')
def test_get_product_exceptions_2(mock_load_data, caplog):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    mock_load_data.side_effect = HTTPError("launch_job_async HTTPError")

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    tap.get_product(file_name='hola.fits', output_file=None)

    mssg = "Cannot retrieve products for file_name hola.fits or product_id None. HTTP error: launch_job_async HTTPError"
    assert caplog.records[0].msg == mssg

    mock_load_data.side_effect = Exception("launch_job_async Exception")

    tap.get_product(file_name='hola.fits', output_file=None)

    mssg = "Cannot retrieve products for file_name hola.fits or product_id None: launch_job_async Exception"
    assert caplog.records[1].msg == mssg

    now = datetime.now()
    dirs = glob.glob(os.path.join(os.getcwd(), "temp_" + now.strftime("%Y%m%d") + '_*'))

    assert len(dirs) == 1
    assert dirs[0] is not None

    remove_temp_dir()


def test_get_observation_products(tmp_path_factory):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    result = tap.get_observation_products(id='13', product_type='observation', filter='VIS', output_file=None)

    assert result is not None

    result = tap.get_observation_products(id='13', product_type='mosaic', filter='VIS', output_file=None)

    assert result is not None

    now = datetime.now()
    dirs = glob.glob(os.path.join(os.getcwd(), "temp_" + now.strftime("%Y%m%d") + '_*'))

    assert len(dirs) == 1
    assert dirs[0] is not None

    remove_temp_dir()

    fits_file = os.path.join(tmp_path_factory.mktemp("euclid_tmp"), 'my_fits_file.fits')

    result = tap.get_observation_products(id='13', product_type='mosaic', filter='VIS', output_file=fits_file)

    assert result is not None


def test_get_observation_products_exceptions():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    with pytest.raises(ValueError, match="Missing required argument: 'observation_id'"):
        tap.get_observation_products(id=None, product_type='observation', filter='VIS', output_file=None)

    with pytest.raises(ValueError, match="Missing required argument: 'product_type'"):
        tap.get_observation_products(id='12', product_type=None, filter='VIS', output_file=None)

    with pytest.raises(ValueError, match="Invalid product type XXXXXXXX. Valid values: \\['observation', 'mosaic'\\]"):
        tap.get_observation_products(id='12', product_type='XXXXXXXX', filter='VIS', output_file=None)


@patch.object(TapPlus, 'load_data')
def test_get_observation_products_exceptions_2(mock_load_data, caplog):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    mock_load_data.side_effect = HTTPError("launch_job_async HTTPError")

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    tap.get_observation_products(id='12345', product_type='observation', filter='VIS', output_file=None)

    mssg = "Cannot retrieve products for observation 12345. HTTP error: launch_job_async HTTPError"
    assert caplog.records[0].msg == mssg

    mock_load_data.side_effect = Exception("launch_job_async Exception")

    tap.get_observation_products(id='12345', product_type='observation', filter='VIS', output_file=None)

    mssg = "Cannot retrieve products for observation 12345: launch_job_async Exception"
    assert caplog.records[1].msg == mssg

    remove_temp_dir()


def test_get_cutout():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='cutout', client_id='ASTROQUERY',
                       connhandler=conn_handler)

    cutout_handler = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                             connhandler=conn_handler)
    # tap.set_cutout_context()
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    c = coordinates.SkyCoord("187.89d 29.54d", frame='icrs')
    r = 1 * u.arcmin

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, cutout_handler=cutout_handler,
                      show_server_messages=False)

    result = tap.get_cutout(
        file_path='/data/repository/NIR/19704/EUC_NIR_W-STACK_NIR-J-19704_20190718T001858.5Z_00.00.fits',
        instrument='NISP', id='19704', coordinate=c, radius=r, output_file=None)

    assert result is not None

    remove_temp_dir()


def test_get_cutout_exception():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='cutout', client_id='ASTROQUERY',
                       connhandler=conn_handler)

    cutout_handler = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                             connhandler=conn_handler)
    # tap.set_cutout_context()
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    c = coordinates.SkyCoord("187.89d 29.54d", frame='icrs')
    r = 1 * u.arcmin
    file_path = '/data/repository/NIR/19704/EUC_NIR_W-STACK_NIR-J-19704_20190718T001858.5Z_00.00.fits',

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, cutout_handler=cutout_handler,
                      show_server_messages=False)

    with pytest.raises(ValueError, match="Radius cannot be greater than 30 arcminutes"):
        tap.get_cutout(file_path=file_path, instrument='NISP', id='19704', coordinate=c, radius=100 * u.arcmin,
                       output_file=None)

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_cutout(file_path=None, instrument='NISP', id='19704', coordinate=c, radius=r, output_file=None)

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_cutout(file_path=file_path, instrument=None, id='19704', coordinate=c, radius=r, output_file=None)

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_cutout(file_path=file_path, instrument='NISP', id=None, coordinate=c, radius=r, output_file=None)

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_cutout(file_path=file_path, instrument='NISP', id='19704', coordinate=None, radius=r, output_file=None)

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_cutout(file_path=file_path, instrument='NISP', id='19704', coordinate=c, radius=None, output_file=None)


@patch.object(TapPlus, 'load_data')
def test_get_cutout_exceptions_2(mock_load_data, caplog):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='cutout', client_id='ASTROQUERY',
                       connhandler=conn_handler)

    cutout_handler = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                             connhandler=conn_handler)
    # tap.set_cutout_context()
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, cutout_handler=cutout_handler,
                      show_server_messages=False)

    mock_load_data.side_effect = HTTPError("launch_job_async HTTPError")

    tap.get_cutout(file_path='hola.fits', instrument='NISP', id='19704', coordinate=SKYCOORD, radius=1 * u.arcmin,
                   output_file=None)

    mssg = ("Cannot retrieve the product for file_path hola.fits, obsId 19704, and collection NISP. HTTP error: "
            "launch_job_async HTTPError")
    assert caplog.records[0].msg == mssg

    mock_load_data.side_effect = Exception("launch_job_async Exception")

    tap.get_cutout(file_path='hola.fits', instrument='NISP', id='19704', coordinate=SKYCOORD, radius=1 * u.arcmin,
                   output_file=None)

    mssg = ("Cannot retrieve the product for file_path hola.fits, obsId 19704, and collection NISP: launch_job_async "
            "Exception")
    assert caplog.records[1].msg == mssg


def test_get_spectrum(tmp_path_factory):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    result = tap.get_spectrum(source_id='2417660845403252054', schema='sedm_sc8', output_file=None)

    assert result is not None

    now = datetime.now()
    dirs = glob.glob(os.path.join(os.getcwd(), "temp_" + now.strftime("%Y%m%d") + '_*'))

    assert len(dirs) == 1
    assert dirs[0] is not None

    remove_temp_dir()

    fits_file = os.path.join(tmp_path_factory.mktemp("euclid_tmp"), 'my_fits_file.fits')

    result = tap.get_spectrum(source_id='2417660845403252054', schema='sedm_sc8', output_file=fits_file)

    assert result is not None


@patch.object(TapPlus, 'load_data')
def test_get_spectrum_exceptions_2(mock_load_data, caplog):
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    mock_load_data.side_effect = HTTPError("launch_job_async HTTPError")

    tap.get_spectrum(source_id='2417660845403252054', schema='sedm_sc8', output_file=None)

    mssg = ("Cannot retrieve spectrum for source_id 2417660845403252054, schema sedm_sc8. HTTP error: launch_job_async "
            "HTTPError")
    assert caplog.records[0].msg == mssg

    mock_load_data.side_effect = Exception("launch_job_async Exception")

    tap.get_spectrum(source_id='2417660845403252054', schema='sedm_sc8', output_file=None)

    mssg = "Cannot retrieve spectrum for source_id 2417660845403252054, schema sedm_sc8: launch_job_async Exception"
    assert caplog.records[1].msg == mssg


def test_get_spectrum_exceptions():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    # if source_id is None or schema is None:

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_spectrum(source_id=None, schema='sedm_sc8', output_file=None)

    with pytest.raises(ValueError, match="Missing required argument"):
        tap.get_spectrum(source_id='2417660845403252054', schema=None, output_file=None)

    with pytest.raises(ValueError, match=(
            "Invalid argument value for 'retrieval_type'. Found hola, expected: 'ALL' or any of \\['SPECTRA_BGS', "
            "'SPECTRA_RGS'\\]")):
        tap.get_spectrum(retrieval_type='hola', source_id='2417660845403252054', schema='schema', output_file=None)


@patch.object(TapPlus, 'login')
def test_login(mock_login):
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="https://test:1111/tap", connhandler=conn_handler)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)
    tap.login(user="user", password="password")
    assert (mock_login.call_count == 3)
    mock_login.side_effect = HTTPError("Login error")
    tap.login(user="user", password="password")
    assert (mock_login.call_count == 4)


@patch.object(TapPlus, 'login_gui')
@patch.object(TapPlus, 'login')
def test_login_gui(mock_login_gui, mock_login):
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)
    tap.login_gui()
    assert (mock_login_gui.call_count == 2)
    mock_login_gui.side_effect = HTTPError("Login error")
    tap.login(user="user", password="password")
    assert (mock_login.call_count == 1)


@patch.object(TapPlus, 'logout')
def test_logout(mock_logout):
    conn_handler = DummyConnHandler()
    tapplus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tapplus, show_server_messages=False)
    tap.logout()
    assert (mock_logout.call_count == 3)
    mock_logout.side_effect = HTTPError("Login error")
    tap.logout()
    assert (mock_logout.call_count == 4)


def test_get_datalinks(monkeypatch):
    def get_datalinks_monkeypatched(self, ids, linking_parameter, verbose):
        return Table()

    # `GaiaClass` is a subclass of `TapPlus`, but it does not inherit
    # `get_datalinks()`, it replaces it with a call to the `get_datalinks()`
    # of its `__gaiadata`.
    monkeypatch.setattr(TapPlus, "get_datalinks", get_datalinks_monkeypatched)
    euclid = EuclidClass(show_server_messages=False)

    result = euclid.get_datalinks(ids=[12345678], verbose=True)
    assert isinstance(result, Table)


def test_load_async_job(mock_querier_async):
    jobid = '1479386030738O'
    name = None
    job = mock_querier_async.load_async_job(jobid=jobid, name=name, verbose=False)

    assert job is not None

    assert job.jobid == jobid


def remove_temp_dir():
    dirs = glob.glob('./temp_*')
    for dir_path in dirs:
        try:
            print(dir_path)
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error: %s : %s" % (dir_path, e.strerror))
