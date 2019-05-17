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
import unittest
import os
import numpy as np
import pytest

from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.core import TapPlus, TAP_CLIENT_ID
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap import taputils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTap(unittest.TestCase):

    def test_load_tables(self):
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
        assert len(res) == 2, \
            "Number of tables expected: %d, found: %d" % (2, len(res))
        # Table 1
        table = self.__find_table('public', 'table1', res)
        assert table.description == 'Table1 desc', \
            "Wrong description for table1. Expected: %s, found %s" % \
            ('Table1 desc', table.description)
        columns = table.columns
        assert len(columns) == 2, \
            "Number of columns for table1. Expected: %d, found: %d" % \
            (2, len(columns))
        col = self.__find_column('table1_col1', columns)
        self.__check_column(col, 'Table1 Column1 desc', '', 'VARCHAR',
                            'indexed')
        col = self.__find_column('table1_col2', columns)
        self.__check_column(col, 'Table1 Column2 desc', '', 'INTEGER',
                            None)
        # Table 2
        table = self.__find_table('public', 'table2', res)
        assert table.description == 'Table2 desc', \
            "Wrong description for table2. Expected: %s, found %s" % \
            ('Table2 desc', table.description)
        columns = table.columns
        assert len(columns) == 3, \
            "Number of columns for table2. Expected: %d, found: %d" % \
            (3, len(columns))
        col = self.__find_column('table2_col1', columns)
        self.__check_column(col, 'Table2 Column1 desc', '', 'VARCHAR',
                            'indexed')
        col = self.__find_column('table2_col2', columns)
        self.__check_column(col, 'Table2 Column2 desc', '', 'INTEGER',
                            None)
        col = self.__find_column('table2_col3', columns)
        self.__check_column(col, 'Table2 Column3 desc', '', 'INTEGER',
                            None)

    def test_load_tables_parameters(self):
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
        assert request == tableRequest, \
            "Empty request. Expected: '%s', found: '%s'" % \
            (tableRequest, request)
        # flag only_names=false & share_accessible=false: equals to
        # empty request
        tap.load_tables(only_names=False, include_shared_tables=False)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Empty request. Expected: '%s', found: '%s'" % \
            (tableRequest, request)
        # flag only_names
        tableRequest = "tables?only_tables=true"
        connHandler.set_response(tableRequest, responseLoadTable)
        tap.load_tables(only_names=True)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Flag only_names. Expected: '%s', found: '%s'" % \
            (tableRequest, request)
        # flag share_accessible=true
        tableRequest = "tables?share_accessible=true"
        connHandler.set_response(tableRequest, responseLoadTable)
        tap.load_tables(include_shared_tables=True)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Flag share_accessigle. Expected: '%s', found: '%s'" % \
            (tableRequest, request)
        # flag only_names=true & share_accessible=true
        tableRequest = "tables?only_tables=true&share_accessible=true"
        connHandler.set_response(tableRequest, responseLoadTable)
        tap.load_tables(only_names=True, include_shared_tables=True)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Flags only_names and share_accessible. " +\
            "Expected: '%s', found: '%s'" % \
            (tableRequest, request)

    def test_load_table(self):
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
        fullQualifiedTableName = tableSchema + "." + tableName
        tableRequest = "tables?tables=" + fullQualifiedTableName
        connHandler.set_response(tableRequest, responseLoadTable)

        with pytest.raises(Exception):
            tap.load_table(fullQualifiedTableName)

        responseLoadTable.set_status_code(200)
        responseLoadTable.set_message("OK")
        table = tap.load_table(fullQualifiedTableName)
        assert table is not None, \
            "Table '%s' not found" % (fullQualifiedTableName)
        assert table.description == 'Table1 desc', \
            "Wrong description for table1. Expected: %s, found %s" % \
            ('Table1 desc', table.description)
        columns = table.columns
        assert len(columns) == 2, \
            "Number of columns for table1. Expected: %d, found: %d" % \
            (2, len(columns))
        col = self.__find_column('table1_col1', columns)
        self.__check_column(col, 'Table1 Column1 desc', '', 'VARCHAR',
                            'indexed')
        col = self.__find_column('table1_col2', columns)
        self.__check_column(col, 'Table1 Column2 desc', '', 'INTEGER',
                            None)

    def test_launch_sync_job(self):
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
        q = dTmpEncoded[p+1:]
        dictTmp = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "votable",
            "tapclient": str(TAP_CLIENT_ID),
            "PHASE": "RUN",
            "QUERY": str(q)}
        sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
        jobRequest = "sync?" + sortedKey
        connHandler.set_response(jobRequest, responseLaunchJob)

        with pytest.raises(Exception):
            tap.launch_job(query)

        responseLaunchJob.set_status_code(200)
        responseLaunchJob.set_message("OK")
        job = tap.launch_job(query)
        assert job is not None, "Expected a valid job"
        assert job.async_ is False, "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.failed is False, "Wrong job status (set Failed = True)"
        # results
        results = job.get_results()
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        self.__check_results_column(results,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'source_id',
                                    'source_id',
                                    None,
                                    np.object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_launch_sync_job_redirect(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(500)
        responseLaunchJob.set_message("ERROR")
        jobid = '12345'
        resultsReq = 'sync/' + jobid
        resultsLocation = 'http://test:1111/tap/' + resultsReq
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
        q = dTmpEncoded[p+1:]
        dictTmp = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "votable",
            "tapclient": str(TAP_CLIENT_ID),
            "PHASE": "RUN",
            "QUERY": str(q)}
        sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
        jobRequest = "sync?" + sortedKey
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
        assert job is not None, "Expected a valid job"
        assert job.async_ is False, "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.failed is False, "Wrong job status (set Failed = True)"
        # Results
        results = job.get_results()
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        self.__check_results_column(results,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'source_id',
                                    'source_id',
                                    None,
                                    np.object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_launch_async_job(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        jobid = '12345'
        # Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(500)
        responseLaunchJob.set_message("ERROR")
        # list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
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
        req = "async?" + sortedKey
        connHandler.set_response(req, responseLaunchJob)
        # Phase response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(500)
        responsePhase.set_message("ERROR")
        responsePhase.set_data(method='GET',
                               context=None,
                               body="COMPLETED",
                               headers=None)
        req = "async/" + jobid + "/phase"
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
        req = "async/" + jobid + "/results/result"
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
        assert job is not None, "Expected a valid job"
        assert job.async_ is True, "Expected an asynchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.failed is False, "Wrong job status (set Failed = True)"
        # results
        results = job.get_results()
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        self.__check_results_column(results,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'source_id',
                                    'source_id',
                                    None,
                                    np.object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_start_job(self):
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
        req = "async/" + jobid + "/phase?PHASE=RUN"
        connHandler.set_response(req, responsePhase)
        # Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(303)
        responseLaunchJob.set_message("OK")
        # list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
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
        req = "async?" + sortedKey
        connHandler.set_response(req, responseLaunchJob)
        # Phase response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(200)
        responsePhase.set_message("OK")
        responsePhase.set_data(method='GET',
                               context=None,
                               body="COMPLETED",
                               headers=None)
        req = "async/" + jobid + "/phase"
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
        req = "async/" + jobid + "/results/result"
        connHandler.set_response(req, responseResultsJob)

        responseResultsJob.set_status_code(200)
        responseResultsJob.set_message("OK")
        job = tap.launch_job_async(query, autorun=False)
        assert job is not None, "Expected a valid job"
        assert job.get_phase() == 'PENDING', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('PENDING', job.get_phase())
        # start job
        job.start()
        assert job.get_phase() == 'QUEUED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('QUEUED', job.get_phase())
        # results
        results = job.get_results()
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        # try to start again
        with pytest.raises(Exception):
            job.start()

    def test_abort_job(self):
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
        req = "async/" + jobid + "/phase?PHASE=ABORT"
        connHandler.set_response(req, responsePhase)
        # Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(303)
        responseLaunchJob.set_message("OK")
        # list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
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
        req = "async?" + sortedKey
        connHandler.set_response(req, responseLaunchJob)

        job = tap.launch_job_async(query, autorun=False)
        assert job is not None, "Expected a valid job"
        assert job.get_phase() == 'PENDING', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('PENDING', job.get_phase())
        # abort job
        job.abort()
        assert job.get_phase() == 'ABORT', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('ABORT', job.get_phase())
        # try to abort again
        with pytest.raises(Exception):
            job.abort()

    def test_job_parameters(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        jobid = '12345'
        # Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(303)
        responseLaunchJob.set_message("OK")
        # list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
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
        req = "async?" + sortedKey
        connHandler.set_response(req, responseLaunchJob)
        # Phase response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(200)
        responsePhase.set_message("OK")
        responsePhase.set_data(method='GET',
                               context=None,
                               body="COMPLETED",
                               headers=None)
        req = "async/" + jobid + "/phase"
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
        req = "async/" + jobid + "/results/result"
        connHandler.set_response(req, responseResultsJob)

        responseResultsJob.set_status_code(200)
        responseResultsJob.set_message("OK")
        job = tap.launch_job_async(query, autorun=False)
        assert job is not None, "Expected a valid job"
        assert job.get_phase() == 'PENDING', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('PENDING', job.get_phase())
        # parameter response
        responseParameters = DummyResponse()
        responseParameters.set_status_code(200)
        responseParameters.set_message("OK")
        responseParameters.set_data(method='GET',
                                    context=None,
                                    body=None,
                                    headers=None)
        req = "async/" + jobid + "?param1=value1"
        connHandler.set_response(req, responseParameters)
        # Phase POST response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(200)
        responsePhase.set_message("OK")
        responsePhase.set_data(method='POST',
                               context=None,
                               body=None,
                               headers=None)
        req = "async/" + jobid + "/phase?PHASE=RUN"
        connHandler.set_response(req, responsePhase)
        # send parameter OK
        job.send_parameter("param1", "value1")
        # start job
        job.start()
        assert job.get_phase() == 'QUEUED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('QUEUED', job.get_phase())
        # try to send a parameter after execution
        with pytest.raises(Exception):
            job.send_parameter("param2", "value2")

    def test_list_async_jobs(self):
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
        assert len(jobs) == 2, \
            "Wrong jobs number. Expected: %d, found %d" % \
            (2, len(jobs))
        assert jobs[0].jobid == '12345', \
            "Wrong job id. Expected: %s, found %s" % \
            ('12345', jobs[0].get_jobid())
        assert jobs[0].get_phase() == 'COMPLETED', \
            "Wrong job phase for job %s. Expected: %s, found %s" % \
            (jobs[0].jobid, 'COMPLETED', jobs[0].get_phase())
        assert jobs[1].jobid == '77777', \
            "Wrong job id. Expected: %s, found %s" % \
            ('77777', jobs[1].jobid)
        assert jobs[1].get_phase() == 'ERROR', \
            "Wrong job phase for job %s. Expected: %s, found %s" % \
            (jobs[1].jobid, 'ERROR', jobs[1].get_phase())

    def test_data(self):
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
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        # error: no params dictionary
        with pytest.raises(Exception):
            # no dictionary: exception
            tap.load_data("1,2")
        params_dict['format'] = "votable"
        results = tap.load_data(params_dict)
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))

    def test_datalink(self):
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
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        results = tap.get_datalinks([1, 2])
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))
        results = tap.get_datalinks(['1', '2'])
        assert len(results) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(results))

    def __find_table(self, schemaName, tableName, tables):
        qualifiedName = schemaName + "." + tableName
        for table in (tables):
            if table.get_qualified_name() == qualifiedName:
                return table
        # not found: raise exception
        self.fail("Table '"+qualifiedName+"' not found")

    def __find_column(self, columnName, columns):
        for c in (columns):
            if c.name == columnName:
                return c
        # not found: raise exception
        self.fail("Column '"+columnName+"' not found")

    def __check_column(self, column, description, unit, dataType, flag):
        assert column.description == description, \
            "Wrong description for table %s. Expected: '%s', found '%s'" % \
            (column.name, description, column.description)
        assert column.unit == unit, \
            "Wrong unit for table %s. Expected: '%s', found '%s'" % \
            (column.name, unit, column.unit)
        assert column.data_type == dataType, \
            "Wrong dataType for table %s. Expected: '%s', found '%s'" % \
            (column.name, dataType, column.data_type)
        assert column.flag == flag, \
            "Wrong flag for table %s. Expected: '%s', found '%s'" % \
            (column.name, flag, column.flag)

    def __check_results_column(self, results, columnName, description, unit,
                               dataType):
        c = results[columnName]
        assert c.description == description, \
            "Wrong description for results column '%s'. " +\
            "Expected: '%s', found '%s'" % \
            (columnName, description, c.description)
        assert c.unit == unit, \
            "Wrong unit for results column '%s'. " +\
            "Expected: '%s', found '%s'" % \
            (columnName, unit, c.unit)
        assert c.dtype == dataType, \
            "Wrong dataType for results column '%s'. " +\
            "Expected: '%s', found '%s'" % \
            (columnName, dataType, c.dtype)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
