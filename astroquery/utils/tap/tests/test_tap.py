# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016
"""
import os
from unittest.mock import patch

import numpy as np
import pytest
from requests import HTTPError

from astroquery.utils.tap.model.tapcolumn import TapColumn

from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.core import TapPlus, TAP_CLIENT_ID
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap import taputils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_load_tables():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    responseLoadTable = DummyResponse()
    responseLoadTable.set_status_code(500)
    responseLoadTable.set_message("ERROR")
    tableDataFile = data_path('test_tables.xml')
    tableData = utils.read_file_content(tableDataFile)
    responseLoadTable.set_data(method='GET',
                               context=None,
                               body=tableData,
                               headers=None)
    tableRequest = "tables"
    connHandler.set_response(tableRequest, responseLoadTable)
    with pytest.raises(Exception):
        tap.load_tables()

    responseLoadTable.set_status_code(200)
    responseLoadTable.set_message("OK")
    res = tap.load_tables()
    assert len(res) == 2

    # Table 1
    table = __find_table('public', 'table1', res)
    assert table.description == 'Table1 desc'
    columns = table.columns
    assert len(columns) == 2
    col = __find_column('table1_col1', columns)
    __check_column(col, 'Table1 Column1 desc', '', 'VARCHAR', 'indexed')
    col = __find_column('table1_col2', columns)
    __check_column(col, 'Table1 Column2 desc', '', 'INTEGER', None)

    # Table 2
    table = __find_table('public', 'table2', res)
    assert table.description == 'Table2 desc'
    columns = table.columns
    assert len(columns) == 3
    col = __find_column('table2_col1', columns)
    __check_column(col, 'Table2 Column1 desc', '', 'VARCHAR', 'indexed')
    col = __find_column('table2_col2', columns)
    __check_column(col, 'Table2 Column2 desc', '', 'INTEGER', None)
    col = __find_column('table2_col3', columns)
    __check_column(col, 'Table2 Column3 desc', '', 'INTEGER', None)


def test_load_tables_parameters():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    responseLoadTable = DummyResponse()
    responseLoadTable.set_status_code(200)
    responseLoadTable.set_message("OK")
    tableDataFile = data_path('test_tables.xml')
    tableData = utils.read_file_content(tableDataFile)
    responseLoadTable.set_data(method='GET',
                               context=None,
                               body=tableData,
                               headers=None)
    tableRequest = "tables"
    connHandler.set_response(tableRequest, responseLoadTable)

    # empty request
    tap.load_tables()
    request = connHandler.get_last_request()
    assert request == tableRequest

    # flag only_names=false & share_accessible=false: equals to
    # empty request
    tap.load_tables(only_names=False, include_shared_tables=False)
    request = connHandler.get_last_request()
    assert request == tableRequest

    # flag only_names
    tableRequest = "tables?only_tables=true"
    connHandler.set_response(tableRequest, responseLoadTable)
    tap.load_tables(only_names=True)
    request = connHandler.get_last_request()
    assert request == tableRequest

    # flag share_accessible=true
    tableRequest = "tables?share_accessible=true"
    connHandler.set_response(tableRequest, responseLoadTable)
    tap.load_tables(include_shared_tables=True)
    request = connHandler.get_last_request()
    assert request == tableRequest

    # flag only_names=true & share_accessible=true
    tableRequest = "tables?only_tables=true&share_accessible=true"
    connHandler.set_response(tableRequest, responseLoadTable)
    tap.load_tables(only_names=True, include_shared_tables=True)
    request = connHandler.get_last_request()
    assert request == tableRequest


def test_load_table():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)

    # No arguments
    with pytest.raises(Exception):
        tap.load_table()

    responseLoadTable = DummyResponse()
    responseLoadTable.set_status_code(500)
    responseLoadTable.set_message("ERROR")
    tableDataFile = data_path('test_table1.xml')
    tableData = utils.read_file_content(tableDataFile)
    responseLoadTable.set_data(method='GET',
                               context=None,
                               body=tableData,
                               headers=None)
    tableSchema = "public"
    tableName = "table1"
    fullQualifiedTableName = f"{tableSchema}.{tableName}"
    tableRequest = f"tables?tables={fullQualifiedTableName}"
    connHandler.set_response(tableRequest, responseLoadTable)

    with pytest.raises(Exception):
        tap.load_table(fullQualifiedTableName)

    responseLoadTable.set_status_code(200)
    responseLoadTable.set_message("OK")
    table = tap.load_table(fullQualifiedTableName)
    assert table is not None
    assert table.description == 'Table1 desc'
    columns = table.columns
    assert len(columns) == 2
    col = __find_column('table1_col1', columns)
    __check_column(col, 'Table1 Column1 desc', '', 'VARCHAR', 'indexed')
    col = __find_column('table1_col2', columns)
    __check_column(col, 'Table1 Column2 desc', '', 'INTEGER', None)


def test_launch_sync_job():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    responseLaunchJob = DummyResponse()
    responseLaunchJob.set_status_code(500)
    responseLaunchJob.set_message("ERROR")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=jobData,
                               headers=None)
    query = 'select top 5 * from table'
    dTmp = {"q": query}
    dTmpEncoded = connHandler.url_encode(dTmp)
    p = dTmpEncoded.find("=")
    q = dTmpEncoded[p + 1:]
    dictTmp = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "votable",
        "tapclient": str(TAP_CLIENT_ID),
        "PHASE": "RUN",
        "QUERY": str(q)}
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    jobRequest = f"sync?{sortedKey}"
    connHandler.set_response(jobRequest, responseLaunchJob)

    with pytest.raises(Exception):
        tap.launch_job(query)

    responseLaunchJob.set_status_code(200)
    responseLaunchJob.set_message("OK")
    job = tap.launch_job(query)

    assert job is not None
    assert job.async_ is False
    assert job.get_phase() == 'COMPLETED'
    assert job.failed is False

    # results
    results = job.get_results()
    assert len(results) == 3
    __check_results_column(results,
                           'ra',
                           'ra',
                           None,
                           np.float64)
    __check_results_column(results,
                           'dec',
                           'dec',
                           None,
                           np.float64)
    __check_results_column(results,
                           'source_id',
                           'source_id',
                           None,
                           object)
    __check_results_column(results,
                           'table1_oid',
                           'table1_oid',
                           None,
                           np.int32)


def test_launch_sync_job_redirect():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    responseLaunchJob = DummyResponse()
    responseLaunchJob.set_status_code(500)
    responseLaunchJob.set_message("ERROR")
    jobid = '12345'
    resultsReq = f'sync/{jobid}'
    resultsLocation = f'http://test:1111/tap/{resultsReq}'
    launchResponseHeaders = [
        ['location', resultsLocation]
    ]
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=None)
    query = 'select top 5 * from table'
    dTmp = {"q": query}
    dTmpEncoded = connHandler.url_encode(dTmp)
    p = dTmpEncoded.find("=")
    q = dTmpEncoded[p + 1:]
    dictTmp = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "votable",
        "tapclient": str(TAP_CLIENT_ID),
        "PHASE": "RUN",
        "QUERY": str(q)}
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    jobRequest = f"sync?{sortedKey}"
    connHandler.set_response(jobRequest, responseLaunchJob)
    # Results response
    responseResultsJob = DummyResponse()
    responseResultsJob.set_status_code(500)
    responseResultsJob.set_message("ERROR")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseResultsJob.set_data(method='GET',
                                context=None,
                                body=jobData,
                                headers=None)
    connHandler.set_response(resultsReq, responseResultsJob)

    with pytest.raises(Exception):
        tap.launch_job(query)

    # Response is redirect (303)
    # No location available
    responseLaunchJob.set_status_code(303)
    responseLaunchJob.set_message("OK")
    with pytest.raises(Exception):
        tap.launch_job(query)

    # Response is redirect (303)
    # Location available
    # Results raises error (500)
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=launchResponseHeaders)
    responseResultsJob.set_status_code(500)
    responseResultsJob.set_message("ERROR")
    with pytest.raises(Exception):
        tap.launch_job(query)

    # Response is redirect (303)
    # Results is 200
    # Location available
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    job = tap.launch_job(query)
    assert job is not None
    assert job.async_ is False
    assert job.get_phase() == 'COMPLETED'
    assert job.failed is False

    # Results
    results = job.get_results()
    assert len(results) == 3
    __check_results_column(results,
                           'ra',
                           'ra',
                           None,
                           np.float64)
    __check_results_column(results,
                           'dec',
                           'dec',
                           None,
                           np.float64)
    __check_results_column(results,
                           'source_id',
                           'source_id',
                           None,
                           object)
    __check_results_column(results,
                           'table1_oid',
                           'table1_oid',
                           None,
                           np.int32)


def test_launch_async_job():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    jobid = '12345'
    # Launch response
    responseLaunchJob = DummyResponse()
    responseLaunchJob.set_status_code(500)
    responseLaunchJob.set_message("ERROR")
    # list of list (httplib implementation for headers in response)
    launchResponseHeaders = [
        ['location', f'http://test:1111/tap/async/{jobid}']
    ]
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=launchResponseHeaders)
    query = 'query'
    dictTmp = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "votable",
        "tapclient": str(TAP_CLIENT_ID),
        "PHASE": "RUN",
        "QUERY": str(query)}
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    req = f"async?{sortedKey}"
    connHandler.set_response(req, responseLaunchJob)
    # Phase response
    responsePhase = DummyResponse()
    responsePhase.set_status_code(500)
    responsePhase.set_message("ERROR")
    responsePhase.set_data(method='GET',
                           context=None,
                           body="COMPLETED",
                           headers=None)
    req = f"async/{jobid}/phase"
    connHandler.set_response(req, responsePhase)
    # Results response
    responseResultsJob = DummyResponse()
    responseResultsJob.set_status_code(500)
    responseResultsJob.set_message("ERROR")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseResultsJob.set_data(method='GET',
                                context=None,
                                body=jobData,
                                headers=None)
    req = f"async/{jobid}/results/result"
    connHandler.set_response(req, responseResultsJob)

    with pytest.raises(Exception):
        tap.launch_job_async(query)

    responseLaunchJob.set_status_code(303)
    responseLaunchJob.set_message("OK")
    with pytest.raises(Exception):
        tap.launch_job_async(query)

    responsePhase.set_status_code(200)
    responsePhase.set_message("OK")
    with pytest.raises(Exception):
        tap.launch_job_async(query)

    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    job = tap.launch_job_async(query)
    assert job is not None
    assert job.async_ is True
    assert job.get_phase() == 'COMPLETED'
    assert job.failed is False

    # results
    results = job.get_results()
    assert len(results) == 3
    __check_results_column(results,
                           'ra',
                           'ra',
                           None,
                           np.float64)
    __check_results_column(results,
                           'dec',
                           'dec',
                           None,
                           np.float64)
    __check_results_column(results,
                           'source_id',
                           'source_id',
                           None,
                           object)
    __check_results_column(results,
                           'table1_oid',
                           'table1_oid',
                           None,
                           np.int32)


def test_start_job():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    jobid = '12345'
    # Phase POST response
    responsePhase = DummyResponse()
    responsePhase.set_status_code(200)
    responsePhase.set_message("OK")
    responsePhase.set_data(method='POST',
                           context=None,
                           body=None,
                           headers=None)
    req = f"async/{jobid}/phase?PHASE=RUN"
    connHandler.set_response(req, responsePhase)
    # Launch response
    responseLaunchJob = DummyResponse()
    responseLaunchJob.set_status_code(303)
    responseLaunchJob.set_message("OK")
    # list of list (httplib implementation for headers in response)
    launchResponseHeaders = [
        ['location', f'http://test:1111/tap/async/{jobid}']
    ]
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=launchResponseHeaders)
    query = 'query'
    dictTmp = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "votable",
        "tapclient": str(TAP_CLIENT_ID),
        "QUERY": str(query)}
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    req = f"async?{sortedKey}"
    connHandler.set_response(req, responseLaunchJob)
    # Phase response
    responsePhase = DummyResponse()
    responsePhase.set_status_code(200)
    responsePhase.set_message("OK")
    responsePhase.set_data(method='GET',
                           context=None,
                           body="COMPLETED",
                           headers=None)
    req = f"async/{jobid}/phase"
    connHandler.set_response(req, responsePhase)
    # Results response
    responseResultsJob = DummyResponse()
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseResultsJob.set_data(method='GET',
                                context=None,
                                body=jobData,
                                headers=None)
    req = f"async/{jobid}/results/result"
    connHandler.set_response(req, responseResultsJob)

    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    job = tap.launch_job_async(query, autorun=False)
    assert job is not None
    assert job.get_phase() == 'PENDING'

    # start job
    job.start()
    assert job.get_phase() == 'QUEUED'

    # results
    results = job.get_results()
    assert len(results) == 3
    assert job.get_phase() == 'COMPLETED'
    # try to start again
    with pytest.raises(Exception):
        job.start()


def test_abort_job():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    jobid = '12345'
    # Phase POST response
    responsePhase = DummyResponse()
    responsePhase.set_status_code(200)
    responsePhase.set_message("OK")
    responsePhase.set_data(method='POST',
                           context=None,
                           body=None,
                           headers=None)
    req = f"async/{jobid}/phase?PHASE=ABORT"
    connHandler.set_response(req, responsePhase)
    # Launch response
    responseLaunchJob = DummyResponse()
    responseLaunchJob.set_status_code(303)
    responseLaunchJob.set_message("OK")
    # list of list (httplib implementation for headers in response)
    launchResponseHeaders = [
        ['location', f'http://test:1111/tap/async/{jobid}']
    ]
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=launchResponseHeaders)
    query = 'query'
    dictTmp = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "votable",
        "tapclient": str(TAP_CLIENT_ID),
        "QUERY": str(query)}
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    req = f"async?{sortedKey}"
    connHandler.set_response(req, responseLaunchJob)

    job = tap.launch_job_async(query, autorun=False)
    assert job is not None
    assert job.get_phase() == 'PENDING'
    # abort job
    job.abort()
    assert job.get_phase() == 'ABORT'
    # try to abort again
    with pytest.raises(Exception):
        job.abort()


def test_job_parameters():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    jobid = '12345'
    # Launch response
    responseLaunchJob = DummyResponse()
    responseLaunchJob.set_status_code(303)
    responseLaunchJob.set_message("OK")
    # list of list (httplib implementation for headers in response)
    launchResponseHeaders = [
        ['location', f'http://test:1111/tap/async/{jobid}']
    ]
    responseLaunchJob.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=launchResponseHeaders)
    query = 'query'
    dictTmp = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "votable",
        "tapclient": str(TAP_CLIENT_ID),
        "QUERY": str(query)}
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    req = f"async?{sortedKey}"
    connHandler.set_response(req, responseLaunchJob)
    # Phase response
    responsePhase = DummyResponse()
    responsePhase.set_status_code(200)
    responsePhase.set_message("OK")
    responsePhase.set_data(method='GET',
                           context=None,
                           body="COMPLETED",
                           headers=None)
    req = f"async/{jobid}/phase"
    connHandler.set_response(req, responsePhase)
    # Results response
    responseResultsJob = DummyResponse()
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseResultsJob.set_data(method='GET',
                                context=None,
                                body=jobData,
                                headers=None)
    req = f"async/{jobid}/results/result"
    connHandler.set_response(req, responseResultsJob)

    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    job = tap.launch_job_async(query, autorun=False)
    assert job is not None
    assert job.get_phase() == 'PENDING'

    # parameter response
    responseParameters = DummyResponse()
    responseParameters.set_status_code(200)
    responseParameters.set_message("OK")
    responseParameters.set_data(method='GET',
                                context=None,
                                body=None,
                                headers=None)
    req = f"async/{jobid}?param1=value1"
    connHandler.set_response(req, responseParameters)
    # Phase POST response
    responsePhase = DummyResponse()
    responsePhase.set_status_code(200)
    responsePhase.set_message("OK")
    responsePhase.set_data(method='POST',
                           context=None,
                           body=None,
                           headers=None)
    req = f"async/{jobid}/phase?PHASE=RUN"
    connHandler.set_response(req, responsePhase)

    # send parameter OK
    job.send_parameter("param1", "value1")
    # start job
    job.start()
    assert job.get_phase() == 'QUEUED'
    # try to send a parameter after execution
    with pytest.raises(Exception):
        job.send_parameter("param2", "value2")


def test_list_async_jobs():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    response = DummyResponse()
    response.set_status_code(500)
    response.set_message("ERROR")
    jobDataFile = data_path('jobs_list.xml')
    jobData = utils.read_file_content(jobDataFile)
    response.set_data(method='GET',
                      context=None,
                      body=jobData,
                      headers=None)
    req = "async"
    connHandler.set_response(req, response)
    with pytest.raises(Exception):
        tap.list_async_jobs()

    response.set_status_code(200)
    response.set_message("OK")
    jobs = tap.list_async_jobs()
    assert len(jobs) == 2
    assert jobs[0].jobid == '12345'
    assert jobs[0].get_phase() == 'COMPLETED'
    assert jobs[1].jobid == '77777'
    assert jobs[1].get_phase() == 'ERROR'


def test_data():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap",
                  data_context="data",
                  connhandler=connHandler)
    responseResultsJob = DummyResponse()
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseResultsJob.set_data(method='GET',
                                context=None,
                                body=jobData,
                                headers=None)
    req = "?ID=1%2C2&format=votable"
    connHandler.set_response(req, responseResultsJob)
    req = "?ID=1%2C2"
    connHandler.set_response(req, responseResultsJob)

    # error
    responseResultsJob.set_status_code(500)
    responseResultsJob.set_message("ERROR")
    params_dict = {}
    params_dict['ID'] = "1,2"
    with pytest.raises(Exception):
        tap.load_data(params_dict)

    # OK
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")

    # results
    results = tap.load_data(params_dict)
    assert len(results) == 3
    # error: no params dictionary
    with pytest.raises(Exception):
        # no dictionary: exception
        tap.load_data("1,2")
    params_dict['format'] = "votable"
    results = tap.load_data(params_dict)
    assert len(results) == 3


def test_datalink():
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap",
                  datalink_context="datalink",
                  connhandler=connHandler)
    responseResultsJob = DummyResponse()
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    jobDataFile = data_path('job_1.vot')
    jobData = utils.read_file_content(jobDataFile)
    responseResultsJob.set_data(method='GET',
                                context=None,
                                body=jobData,
                                headers=None)
    req = "links?ID=1,2"
    connHandler.set_response(req, responseResultsJob)

    # error
    responseResultsJob.set_status_code(500)
    responseResultsJob.set_message("ERROR")
    with pytest.raises(Exception):
        # missing IDS parameter
        tap.get_datalinks(ids=None)

    # OK
    responseResultsJob.set_status_code(200)
    responseResultsJob.set_message("OK")
    # results
    results = tap.get_datalinks("1,2")
    assert len(results) == 3
    results = tap.get_datalinks([1, 2])
    assert len(results) == 3
    results = tap.get_datalinks(['1', '2'])
    assert len(results) == 3


def test_get_new_column_values_for_update():
    # Different column (no modifications)
    list_of_changes = [['column2', 'flags', 'Dec'],
                       ['column2', 'indexed', 'true'],
                       ['column2', 'ucd', 'new_ucd_column2'],
                       ['column2', 'utype', 'new_utype_column2']]
    column_name = 'column'
    c_flags = 'Ra'
    c_indexed = 'false'
    c_ucd = 'ucd'
    c_utype = 'utype_'
    flags, indexed, ucd, utype = TapPlus.get_new_column_values_for_update(
        list_of_changes, column_name, c_flags, c_indexed, c_ucd, c_utype)
    assert flags == c_flags
    assert indexed == c_indexed
    assert ucd == c_ucd
    assert utype == c_utype

    # Modifciations
    list_of_changes = [['column2', 'flags', 'Dec'],
                       ['column2', 'indexed', 'true'],
                       ['column2', 'ucd', 'new_ucd_column2'],
                       ['column2', 'utype', 'new_utype_column2'],
                       ['column', 'flags', 'Dec'],
                       ['column', 'indexed', 'true'],
                       ['column', 'ucd', 'new_ucd'],
                       ['column', 'utype', 'new_utype']]
    column_name = 'column'
    c_flags = 'Ra'
    c_indexed = 'false'
    c_ucd = 'ucd'
    c_utype = 'utype'
    n_flags = 'Dec'
    n_indexed = 'True'
    n_ucd = 'new_ucd'
    n_utype = 'new_utype'
    flags, indexed, ucd, utype = TapPlus.get_new_column_values_for_update(
        list_of_changes, column_name, c_flags, c_indexed, c_ucd, c_utype)
    assert flags == n_flags
    assert indexed == n_indexed
    assert ucd == n_ucd
    assert utype == n_utype

    # Previous value Ra/indexed, new value remove Ra/indexed
    list_of_changes = [['column', 'flags', ''],
                       ['column', 'indexed', 'false']]
    column_name = 'column'
    c_flags = 'Ra'
    c_indexed = 'true'
    n_flags = ''
    n_indexed = 'false'
    flags, indexed, ucd, utype = TapPlus.get_new_column_values_for_update(
        list_of_changes, column_name, c_flags, c_indexed, c_ucd, c_utype)
    assert flags == n_flags
    assert indexed == n_indexed

    # Test if flag is Ra, indexed is True
    list_of_changes = [['column', 'flags', 'Ra'],
                       ['column', 'indexed', 'false']]
    column_name = 'column'
    c_flags = 'Ra'
    c_indexed = 'true'
    n_flags = 'Ra'
    n_indexed = 'True'
    flags, indexed, ucd, utype = TapPlus.get_new_column_values_for_update(
        list_of_changes, column_name, c_flags, c_indexed, c_ucd, c_utype)
    assert flags == n_flags
    assert indexed == n_indexed


def test_get_current_column_values_for_update():
    column = TapColumn(None)
    column.name = 'colname'
    column.flags = 0
    column.flag = None
    column.ucd = 'ucd'
    column.utype = 'utype'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert column_name == 'colname'
    assert flags is None
    assert indexed is False
    assert ucd == 'ucd'
    assert utype == 'utype'

    column.flags = '1'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Ra'
    assert indexed is True
    column.flags = '2'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Dec'
    assert indexed is True
    column.flags = '4'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Flux'
    assert indexed is False
    column.flags = '8'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Mag'
    assert indexed is False
    column.flags = '16'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'PK'
    assert indexed is True
    column.flags = '33'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Ra'
    assert indexed is True
    column.flags = '34'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Dec'
    assert indexed is True
    column.flags = '38'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Flux'
    assert indexed is False
    column.flags = '40'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'Mag'
    assert indexed is False
    column.flags = '48'
    column_name, flags, indexed, ucd, utype = \
        TapPlus.get_current_column_values_for_update(column)
    assert flags == 'PK'
    assert indexed is True


def test_update_user_table():
    tableName = 'table'
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    dummyResponse = DummyResponse()
    dummyResponse.set_status_code(200)
    dummyResponse.set_message("OK")
    tableDataFile = data_path('test_table_update.xml')
    tableData = utils.read_file_content(tableDataFile)
    dummyResponse.set_data(method='GET',
                           context=None,
                           body=tableData,
                           headers=None)
    tableRequest = f"tables?tables={tableName}"
    connHandler.set_response(tableRequest, dummyResponse)

    with pytest.raises(Exception):
        tap.update_user_table()
    with pytest.raises(Exception):
        tap.update_user_table(table_name=tableName)
    with pytest.raises(Exception):
        tap.update_user_table(table_name=tableName, list_of_changes=[])
    with pytest.raises(Exception):
        tap.update_user_table(table_name=tableName, list_of_changes=[[]])
    with pytest.raises(Exception):
        tap.update_user_table(table_name=tableName, list_of_changes=[['', '', '']])

    # Test Ra & Dec are provided
    list_of_changes = [['alpha', 'flags', 'Ra']]
    with pytest.raises(Exception):
        tap.update_user_table(table_name=tableName, list_of_changes=list_of_changes)
    list_of_changes = [['delta', 'flags', 'Dec']]
    with pytest.raises(Exception):
        tap.update_user_table(table_name=tableName, list_of_changes=list_of_changes)

    # OK
    responseEditTable = DummyResponse()
    responseEditTable.set_status_code(200)
    responseEditTable.set_message("OK")
    dictTmp = {
        "ACTION": "edit",
        "NUMTABLES": "1",
        "TABLE0": tableName,
        "TABLE0_COL0": "table6_oid",
        "TABLE0_COL0_FLAGS": "PK",
        "TABLE0_COL0_INDEXED": "True",
        "TABLE0_COL0_UCD": "",
        "TABLE0_COL0_UTYPE": "",
        "TABLE0_COL1": "source_id",
        "TABLE0_COL1_FLAGS": "None",
        "TABLE0_COL1_INDEXED": "False",
        "TABLE0_COL1_UCD": "None",
        "TABLE0_COL1_UTYPE": "None",
        "TABLE0_COL2": "alpha",
        "TABLE0_COL2_FLAGS": "Ra",
        "TABLE0_COL2_INDEXED": "False",
        "TABLE0_COL2_UCD": "",
        "TABLE0_COL2_UTYPE": "",
        "TABLE0_COL3": "delta",
        "TABLE0_COL3_FLAGS": "Dec",
        "TABLE0_COL3_INDEXED": "False",
        "TABLE0_COL3_UCD": "",
        "TABLE0_COL3_UTYPE": "",
        "TABLE0_NUMCOLS": "4"
    }
    sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
    req = f"tableEdit?{sortedKey}"
    connHandler.set_response(req, responseEditTable)

    list_of_changes = [['alpha', 'flags', 'Ra'], ['delta', 'flags', 'Dec']]
    tap.update_user_table(table_name=tableName, list_of_changes=list_of_changes)


def test_rename_table():
    tableName = 'user_test.table_test_rename'
    newTableName = 'user_test.table_test_rename_new'
    newColumnNames = {'ra': 'alpha', 'dec': 'delta'}
    connHandler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
    dummyResponse = DummyResponse()
    dummyResponse.set_status_code(200)
    dummyResponse.set_message("OK")
    tableDataFile = data_path('test_table_rename.xml')
    tableData = utils.read_file_content(tableDataFile)
    dummyResponse.set_data(method='GET',
                           context=None,
                           body=tableData,
                           headers=None)

    with pytest.raises(Exception):
        tap.rename_table()
    with pytest.raises(Exception):
        tap.rename_table(table_name=tableName)
    with pytest.raises(Exception):
        tap.rename_table(table_name=tableName, new_table_name=None, new_column_names_dict=None)

    # Test OK.
    responseRenameTable = DummyResponse()
    responseRenameTable.set_status_code(200)
    responseRenameTable.set_message("OK")
    dictArgs = {
        "action": "rename",
        "new_column_names": "ra:alpha,dec:delta",
        "new_table_name": newTableName,
        "table_name": tableName,
    }
    data = connHandler.url_encode(dictArgs)
    req = f"TableTool?{data}"
    connHandler.set_response(req, responseRenameTable)
    tap.rename_table(table_name=tableName, new_table_name=newTableName, new_column_names_dict=newColumnNames)


def __find_table(schemaName, tableName, tables):
    qualifiedName = f"{schemaName}.{tableName}"
    for table in (tables):
        if table.get_qualified_name() == qualifiedName:
            return table
    # not found: raise exception
    pytest.fail(f"Table '{qualifiedName}' not found")


def __find_column(columnName, columns):
    for c in (columns):
        if c.name == columnName:
            return c
    # not found: raise exception
    pytest.fail(f"Column '{columnName}' not found")


def __check_column(column, description, unit, dataType, flag):
    assert column.description == description
    assert column.unit == unit
    assert column.data_type == dataType
    assert column.flag == flag


def __check_results_column(results, columnName, description, unit,
                           dataType):
    c = results[columnName]
    assert c.description == description
    assert c.unit == unit
    assert c.dtype == dataType


@patch.object(TapPlus, 'login')
def test_login(mock_login):
    conn_handler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=conn_handler)
    tap.login("user", "password")
    assert (mock_login.call_count == 1)
    mock_login.side_effect = HTTPError("Login error")
    with pytest.raises(HTTPError):
        tap.login("user", "password")
    assert (mock_login.call_count == 2)


@patch.object(TapPlus, 'login_gui')
@patch.object(TapPlus, 'login')
def test_login_gui(mock_login_gui, mock_login):
    conn_handler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=conn_handler)
    tap.login_gui()
    assert (mock_login_gui.call_count == 0)
    mock_login_gui.side_effect = HTTPError("Login error")
    with pytest.raises(HTTPError):
        tap.login("user", "password")
    assert (mock_login.call_count == 1)


@patch.object(TapPlus, 'logout')
def test_logout(mock_logout):
    conn_handler = DummyConnHandler()
    tap = TapPlus("http://test:1111/tap", connhandler=conn_handler)
    tap.logout()
    assert (mock_logout.call_count == 1)
    mock_logout.side_effect = HTTPError("Login error")
    with pytest.raises(HTTPError):
        tap.logout()
    assert (mock_logout.call_count == 2)
