# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
Euclid TAP plus
===============
@author: Juan Carlos Segovia (original code from Gaia) / John Hoar (Euclid adaptation)
@contact: juan.carlos.segovia@sciops.esa.int
European Space Astronomy Centre (ESAC)
European Space Agency (ESA)
Created on 30 jun. 2016
Euclid adaptation: 15 March 2018
"""
import os
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy import coordinates
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.table import Table
from astropy.utils.data import get_pkg_data_filename

from astroquery.esa.euclid.core import EuclidClass
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.core import TapPlus
from astroquery.esa.euclid.core import conf

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


def test_launch_async_job():
    conn_handler = DummyConnHandler()

    tap_plus = TapPlus(url="http://test:1111/tap", connhandler=conn_handler)
    query = "select alpha, delta, source_id, table1_oid from caca"

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


def test_get_product():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    try:
        tap.get_product(file_name='EUC_SIM_NISRGS180-8-1_20220722T094150.427Z_PV023_NISP-S_8_18_0.fits',
                        output_file=None)
    except Exception as e:
        assert str(e).startswith('Cannot retrieve products')


def test_get_obs_products():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    try:
        tap.get_obs_products(id='13', product_type='observation', filter='VIS', output_file=None)
    except Exception as e:
        assert str(e).startswith('Cannot retrieve products')


def test_get_cutout():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='cutout', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # tap.set_cutout_context()
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    c = coordinates.SkyCoord("187.89d 29.54d", frame='icrs')
    r = 1 * u.arcmin

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    try:
        tap.get_cutout(
            file_path='/data/repository/NIR/19704/EUC_NIR_W-STACK_NIR-J-19704_20190718T001858.5Z_00.00.fits',
            instrument='NISP', id='19704', coordinate=c, radius=r, output_file=None)
    except Exception as e:
        assert str(e).startswith('Cannot retrieve the product')


def test_get_spectrum():
    conn_handler = DummyConnHandler()
    tap_plus = TapPlus(url="http://test:1111/tap", data_context='data', client_id='ASTROQUERY',
                       connhandler=conn_handler)
    # Launch response: we use default response because the query contains decimals
    responseLaunchJob = DummyResponse(200)
    responseLaunchJob.set_data(method='POST', context=None, body='', headers=None)

    conn_handler.set_default_response(responseLaunchJob)

    tap = EuclidClass(tap_plus_conn_handler=conn_handler, datalink_handler=tap_plus, show_server_messages=False)

    try:
        tap.get_spectrum(source_id='2417660845403252054', schema='sedm_sc8', output_file=None)
    except Exception as e:
        assert str(e).startswith('Cannot retrieve spectrum')
