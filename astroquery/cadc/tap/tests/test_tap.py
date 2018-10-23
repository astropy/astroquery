# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""
import unittest
import os
import numpy as np
import pytest

from astroquery.cadc import auth
from astroquery.cadc.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.cadc.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.cadc.tap.core import TapPlus, TAP_CLIENT_ID
from astroquery.cadc.tap.xmlparser import utils
from astroquery.cadc.tap import taputils

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class TestTap(unittest.TestCase):
    def test_get_tables(self):
        anon = auth.AnonAuthMethod()
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
            tap.get_tables(authentication=anon)

        responseLoadTable.set_status_code(200)
        responseLoadTable.set_message("OK")
        res = tap.get_tables(authentication=anon)
        assert len(res) == 2, \
            "Number of tables expected: %d, found: %d" % (2, len(res))
        # Table 1
        table = self.__find_table('public', 'table1', res)
        assert table.get_description() == 'Table1 desc', \
            "Wrong description for table1. Expected: %s, found %s" % \
            ('Table1 desc', table.get_description())
        columns = table.get_columns()
        assert len(columns) == 2, \
            "Number of columns for table1. Expected: %d, found: %d" % \
            (2, len(columns))
        col = self.__find_column('table1_col1', columns)
        self.__check_column(col, 'Table1 Column1 desc', '', 'VARCHAR', 'indexed')
        col = self.__find_column('table1_col2', columns)
        self.__check_column(col, 'Table1 Column2 desc', '', 'INTEGER', None)
        # Table 2
        table = self.__find_table('public', 'table2', res)
        assert table.get_description() == 'Table2 desc', \
            "Wrong description for table2. Expected: %s, found %s" % \
            ('Table2 desc', table.get_description())
        columns = table.get_columns()
        assert len(columns) == 3, \
            "Number of columns for table2. Expected: %d, found: %d" % \
            (3, len(columns))
        col = self.__find_column('table2_col1', columns)
        self.__check_column(col, 'Table2 Column1 desc', '', 'VARCHAR', 'indexed')
        col = self.__find_column('table2_col2', columns)
        self.__check_column(col, 'Table2 Column2 desc', '', 'INTEGER', None)
        col = self.__find_column('table2_col3', columns)
        self.__check_column(col, 'Table2 Column3 desc', '', 'INTEGER', None)

    def test_get_tables_parameters(self):
        anon = auth.AnonAuthMethod()
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
        tap.get_tables(authentication=anon)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Empty request. Expected: '%s', found: '%s'" % \
            (tableRequest, request)
        # flag only_names=false: equals to empty request
        tap.get_tables(only_names=False, authentication=anon)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Empty request. Expected: '%s', found: '%s'" % \
            (tableRequest, request)
        # flag only_names
        tableRequest = "tables?only_tables=true"
        connHandler.set_response(tableRequest, responseLoadTable)
        tap.get_tables(only_names=True, authentication=anon)
        request = connHandler.get_last_request()
        assert request == tableRequest, \
            "Flag only_names. Expected: '%s', found: '%s'" % \
            (tableRequest, request)

    def test_get_table(self):
        anon = auth.AnonAuthMethod()
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
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
            tap.get_table(fullQualifiedTableName, authentication=anon)

        responseLoadTable.set_status_code(200)
        responseLoadTable.set_message("OK")
        table = tap.get_table(fullQualifiedTableName, authentication=anon)
        assert table is not None, \
            "Table '%s' not found" % (fullQualifiedTableName)
        assert table.get_description() == 'Table1 desc', \
            "Wrong description for table1. Expected: %s, found %s" % \
            ('Table1 desc', table.get_description())
        columns = table.get_columns()
        assert len(columns) == 2, \
            "Number of columns for table1. Expected: %d, found: %d" % \
            (2, len(columns))
        col = self.__find_column('table1_col1', columns)
        self.__check_column(col, 'Table1 Column1 desc', '', 'VARCHAR', 'indexed')
        col = self.__find_column('table1_col2', columns)
        self.__check_column(col, 'Table1 Column2 desc', '', 'INTEGER', None)

    def test_run_query_sync(self):
        anon = auth.AnonAuthMethod()
        operation = 'sync'
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
            "QUERY": str(q)}
        sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
        jobRequest = "sync?" + sortedKey
        connHandler.set_response(jobRequest, responseLaunchJob)

        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        responseLaunchJob.set_status_code(200)
        responseLaunchJob.set_message("OK")
        job = tap.run_query(query, operation, authentication=anon)
        assert job is not None, "Expected a valid job"
        assert job.is_sync(), "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.is_failed() is False, "Wrong job status (set Failed = True)"
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

    def test_run_query_sync__redirect(self):
        anon = auth.AnonAuthMethod()
        operation = 'sync'
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
        query = 'select  TOP 2000 * from table'
        dTmp = {"q": query}
        dTmpEncoded = connHandler.url_encode(dTmp)
        p = dTmpEncoded.find("=")
        q = dTmpEncoded[p+1:]
        dictTmp = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "votable",
            "tapclient": str(TAP_CLIENT_ID),
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

        query = 'select * from table'

        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        # Response is redirect (303)
        # No location available
        responseLaunchJob.set_status_code(303)
        responseLaunchJob.set_message("OK")
        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

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
            tap.run_query(query, operation, authentication=anon)

        # Response is redirect (303)
        # Results is 200
        # Location available
        responseResultsJob.set_status_code(200)
        responseResultsJob.set_message("OK")
        job = tap.run_query(query, operation, authentication=anon)
        assert job is not None, "Expected a valid job"
        assert job.is_sync(), "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.is_failed() is False, "Wrong job status (set Failed = True)"
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

    def test_run_query_async_redirect(self):
        anon = auth.AnonAuthMethod()
        operation = 'async'
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(500)
        responseLaunchJob.set_message("ERROR")
        jobid = '12345'
        resultsReq = 'async/' + jobid
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
            "QUERY": str(q)}
        sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
        jobRequest = "async?" + sortedKey
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
        req = "async/" + jobid + "/results/result"
        connHandler.set_response(req, responseResultsJob)
        # Run phase response
        runPhase = DummyResponse()
        runPhase.set_status_code(303)
        runPhase.set_message("SEE OTHER")
        runPhase.set_data(method='GET',
                          context=None,
                          body="COMPLETED",
                          headers=None)
        req = "async/" + jobid + "/phase?PHASE=RUN"
        connHandler.set_response(req, runPhase)

        # Check phase response
        checkPhase = DummyResponse()
        checkPhase.set_status_code(200)
        checkPhase.set_message("OK")
        checkPhase.set_data(method='GET',
                            context=None,
                            body="COMPLETED",
                            headers=None)
        req = "async/" + jobid + "/phase"
        connHandler.set_response(req, checkPhase)

        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        # Response is redirect (303)
        # No location available
        responseLaunchJob.set_status_code(303)
        responseLaunchJob.set_message("SEE OTHER")
        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

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
            tap.run_query(query, operation, authentication=anon)

        # Response is redirect (303)
        # Results is 200
        # Location available
        responseResultsJob.set_status_code(200)
        responseResultsJob.set_message("OK")
        responseLaunchJob.set_data(method='POST',
                                   context=None,
                                   body=None,
                                   headers=launchResponseHeaders)
        responseResultsJob.set_status_code(500)
        responseResultsJob.set_message("ERROR")
        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        # Response is redirect (303)
        # Results is 200
        # Location available
        responseResultsJob.set_status_code(200)
        responseResultsJob.set_message("OK")
        job = tap.run_query(query, operation, authentication=anon)
        assert job is not None, "Expected a valid job"
        assert job.is_async(), "Expected a asynchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.is_failed() is False, "Wrong job status (set Failed = True)"
        # Results
        results = job.get_results(authentication=anon)
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
        newLocation = 'http://secondwebsite:2222/tap/async/12345'
        newHeaders = [
            ['location', newLocation]
        ]
        responseResultsJob.set_data(method='POST',
                                    context=None,
                                    body=None,
                                    headers=newHeaders)
        responseResultsJob.set_status_code(303)
        responseResultsJob.set_message("SEE OTHER")
        # Redirect response
        redirectResultsJob = DummyResponse()
        redirectResultsJob.set_status_code(200)
        redirectResultsJob.set_message("OK")
        redirectDataFile = data_path('job_1.vot')
        redirectData = utils.read_file_content(redirectDataFile)
        redirectResultsJob.set_data(method='GET',
                                    context=None,
                                    body=redirectData,
                                    headers=None)
        req = "async/12345/redirect"
        connHandler.set_response(req, redirectResultsJob)
        job = tap.run_query(query, operation, authentication=anon)
        assert job is not None, "Expected a valid job"
        assert job.is_async(), "Expected a asynchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.is_failed() is False, "Wrong job status (set Failed = True)"
        # Results
        results = job.get_results(authentication=anon)
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

    def test_run_query_async(self):
        anon = auth.AnonAuthMethod()
        operation = 'async'
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

        # Run phase response
        runPhase = DummyResponse()
        runPhase.set_status_code(303)
        runPhase.set_message("SEE OTHER")
        runPhase.set_data(method='GET',
                          context=None,
                          body="COMPLETED",
                          headers=None)
        req = "async/" + jobid + "/phase?PHASE=RUN"
        connHandler.set_response(req, runPhase)

        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        responseLaunchJob.set_status_code(303)
        responseLaunchJob.set_message("OK")
        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        responsePhase.set_status_code(200)
        responsePhase.set_message("OK")
        with pytest.raises(Exception):
            tap.run_query(query, operation, authentication=anon)

        responseResultsJob.set_status_code(200)
        responseResultsJob.set_message("OK")
        job = tap.run_query(query, operation, authentication=anon)
        assert job is not None, "Expected a valid job"
        assert job.is_sync() is False, "Expected an asynchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.is_failed() is False, "Wrong job status (set Failed = True)"
        # results
        results = job.get_results(authentication=anon)
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

    def test_list_async_jobs(self):
        netrc = auth.NetrcAuthMethod(filename=data_path('netrc.txt'))
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
        req = "auth-async"
        connHandler.set_response(req, response)
        with pytest.raises(Exception):
            tap.list_async_jobs(authentication=netrc)

        response.set_status_code(200)
        response.set_message("OK")
        jobs = tap.list_async_jobs(authentication=netrc)
        assert len(jobs) == 2, \
            "Wrong jobs number. Expected: %d, found %d" % \
            (2, len(jobs))
        assert jobs[0].get_jobid() == '12345', \
            "Wrong job id. Expected: %s, found %s" % \
            ('12345', jobs[0].get_jobid())
        assert jobs[0].get_phase() == 'COMPLETED', \
            "Wrong job phase for job %s. Expected: %s, found %s" % \
            (jobs[0].get_jobid(), 'COMPLETED', jobs[0].get_phase())
        assert jobs[1].get_jobid() == '77777', \
            "Wrong job id. Expected: %s, found %s" % \
            ('77777', jobs[1].get_jobid())
        assert jobs[1].get_phase() == 'ERROR', \
            "Wrong job phase for job %s. Expected: %s, found %s" % \
            (jobs[1].get_jobid(), 'ERROR', jobs[1].get_phase())

    def __find_table(self, schemaName, tableName, tables):
        qualifiedName = schemaName + "." + tableName
        for table in (tables):
            if table.get_qualified_name() == qualifiedName:
                return table
        # not found: raise exception
        self.fail("Table '"+qualifiedName+"' not found")

    def __find_column(self, columnName, columns):
        for c in (columns):
            if c.get_name() == columnName:
                return c
        # not found: raise exception
        self.fail("Column '"+columnName+"' not found")

    def __check_column(self, column, description, unit, dataType, flag):
        assert column.get_description() == description, \
            "Wrong description for table %s. Expected: '%s', found '%s'" % \
            (column.get_name(), description, column.get_description())
        assert column.get_unit() == unit, \
            "Wrong unit for table %s. Expected: '%s', found '%s'" % \
            (column.get_name(), unit, column.get_unit())
        assert column.get_data_type() == dataType, \
            "Wrong dataType for table %s. Expected: '%s', found '%s'" % \
            (column.get_name(), dataType, column.get_data_type())
        assert column.get_flag() == flag, \
            "Wrong flag for table %s. Expected: '%s', found '%s'" % \
            (column.get_name(), flag, column.get_flag())

    def __check_results_column(self, results, columnName, description, unit,
                               dataType):
        c = results[columnName]
        assert c.description == description, \
            "Wrong description for results column '%s'. Expected: '%s', found '%s'" % \
            (columnName, description, c.description)
        assert c.unit == unit, \
            "Wrong unit for results column '%s'. Expected: '%s', found '%s'" % \
            (columnName, unit, c.unit)
        assert c.dtype == dataType, \
            "Wrong dataType for results column '%s'. Expected: '%s', found '%s'" % \
            (columnName, dataType, c.dtype)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
