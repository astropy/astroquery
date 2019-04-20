# Licensed under a 3-clause BSD style license - see LICENSE.rst

import unittest
import os
import tempfile
import numpy as np
import pytest

from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.cadc.cadctap.tests.DummyConnHandler import DummyConnHandlerCadc
from astroquery.cadc.cadctap.core import TapPlusCadc, TAP_CLIENT_ID
from astroquery.cadc.cadctap.job import JobCadc
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap import taputils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTapCadc(unittest.TestCase):

    def test_get_table(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
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
        tableRequest = "tables"
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
        self.__check_column(col, 'Table1 Column1 desc', '',
                            'VARCHAR', 'indexed')
        col = self.__find_column('table1_col2', columns)
        self.__check_column(col, 'Table1 Column2 desc', '', 'INTEGER', None)

    def test_launch_sync_job(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
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

    def test_launch_multipart_async_job(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
        jobid = '1234'
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(200)
        responseLaunchJob.set_message("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.read_file_content(jobDataFile)
        responseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        responseLaunchJob.set_data(method='POST',
                                   context=None,
                                   body=jobData,
                                   headers=responseHeaders)
        query = 'select top 5 * from table'
        upload_name = 'testtable'
        upload_resource = data_path('test_tables.xml')
        dTmp = {"q": query}
        dTmpEncoded = connHandler.url_encode(dTmp)
        p = dTmpEncoded.find("=")
        q = dTmpEncoded[p+1:]
        uTmp = {"u": str(upload_name)+",param:"+str(upload_name)}
        uTmpEncoded = connHandler.url_encode(uTmp)
        pos = uTmpEncoded.find("=")
        upload = uTmpEncoded[pos+1:]
        dictTmp = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "votable",
            "tapclient": str(TAP_CLIENT_ID),
            "QUERY": str(q),
            "UPLOAD": str(upload)}
        sortedKey = taputils.taputil_create_sorted_dict_key(dictTmp)
        jobRequest = "async?" + sortedKey
        connHandler.set_response(jobRequest, responseLaunchJob)

        # Phase response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(303)
        responsePhase.set_message("OK")
        responsePhaseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        responsePhase.set_data(method='POST',
                               context=None,
                               body="COMPLETED",
                               headers=responsePhaseHeaders)
        req = "async/" + jobid + "/phase?PHASE=RUN"
        connHandler.set_response(req, responsePhase)
        # Job Phase response
        jobPhase = DummyResponse()
        jobPhase.set_status_code(200)
        jobPhase.set_message("OK")
        jobPhaseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        jobPhase.set_data(method='GET',
                          context=None,
                          body="COMPLETED",
                          headers=jobPhaseHeaders)
        req = "async/" + jobid + "/phase"
        connHandler.set_response(req, jobPhase)
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

        job = tap.launch_job_async(query, upload_resource=upload_resource,
                                   upload_table_name=upload_name)
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

    def test_launch_async_job(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
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
        responsePhase.set_status_code(303)
        responsePhase.set_message("OK")
        responsePhaseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        responsePhase.set_data(method='POST',
                               context=None,
                               body="COMPLETED",
                               headers=responsePhaseHeaders)
        req = "async/" + jobid + "/phase?PHASE=RUN"
        connHandler.set_response(req, responsePhase)
        # Job Phase response
        jobPhase = DummyResponse()
        jobPhase.set_status_code(200)
        jobPhase.set_message("OK")
        jobPhaseHeaders = [
                ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        jobPhase.set_data(method='GET',
                          context=None,
                          body="COMPLETED",
                          headers=jobPhaseHeaders)
        req = "async/" + jobid + "/phase"
        connHandler.set_response(req, jobPhase)
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

    def test_job_load(self):
        connHandler = DummyConnHandlerCadc()
        job = JobCadc(async_job=True, query='query', connhandler=connHandler)
        jobid = 1234
        job.jobid = str(jobid)
        job.parameters['format'] = 'csv'
        # Job Phase response
        jobPhase = DummyResponse()
        jobPhase.set_status_code(200)
        jobPhase.set_message("OK")
        jobPhase.set_data(method='GET',
                          context=None,
                          body="ERROR",
                          headers=None)
        req = "async/" + str(jobid) + "/phase"
        connHandler.set_response(req, jobPhase)
        # Error response
        error = DummyResponse()
        error.set_status_code(200)
        error.set_message("OK")
        jobDataPath = data_path('test_jobs_async.xml')
        jobData = utils.read_file_content(jobDataPath)
        error.set_data(method='GET',
                       context=None,
                       body=jobData,
                       headers=None)
        req = "async/" + str(jobid)
        connHandler.set_response(req, error)

        with pytest.raises(Exception):
            job.get_results()

    def test_load_job(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
        jobid = 1234
        # Response
        response = DummyResponse()
        response.set_status_code(200)
        response.set_message("OK")
        jobDataPath = data_path('test_jobs_async.xml')
        jobData = utils.read_file_content(jobDataPath)
        response.set_data(method='GET',
                          context=None,
                          body=jobData,
                          headers=None)
        req = "async/" + str(jobid)
        connHandler.set_response(req, response)
        # Phase response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(200)
        responsePhase.set_message("OK")
        responsePhaseHeaders = [
                ['location', 'http://test:1111/tap/async/' + str(jobid)]
            ]
        responsePhase.set_data(method='POST',
                               context=None,
                               body="COMPLETED",
                               headers=responsePhaseHeaders)
        req = "async/" + str(jobid) + "/phase"
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
        req = "async/" + str(jobid) + "/results/result"
        connHandler.set_response(req, responseResultsJob)

        job = tap.load_async_job(jobid)

        assert job.jobid == '1234', "Jobid is wrong"
        assert job._phase == 'COMPLETED', 'Phase is wrong'
        assert job.startTime == '2016-11-17T13:33:50.755+0100', \
            "Start time is wrong"
        assert job.parameters['LANG'] == 'ADQL', 'LANG is wrong'
        assert job.parameters['QUERY'] == 'SELECT * FROM table', \
            'QUERY is wrong'
        assert job.errmessage == \
            'IllegalArgumentException:net.sf.jsqlparser.JSQLParserException',\
            'Error message is wrong'

    def test_save_results(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
        job = JobCadc(async_job=True, query='query', connhandler=connHandler)
        jobid = 1234
        job.jobid = str(jobid)
        job.parameters['format'] = 'csv'
        # Phase response
        responsePhase = DummyResponse()
        responsePhase.set_status_code(200)
        responsePhase.set_message("OK")
        responsePhaseHeaders = [
                ['location', 'http://test:1111/tap/async/' + str(jobid)]
            ]
        responsePhase.set_data(method='GET',
                               context=None,
                               body="COMPLETED",
                               headers=responsePhaseHeaders)
        req = "async/" + str(jobid) + "/phase"
        connHandler.set_response(req, responsePhase)
        # Results response
        responseResultsJob = DummyResponse()
        responseResultsJob.set_status_code(303)
        responseResultsJob.set_message("OK")
        responseResultsHeaders = [
            ['location', 'http://test:1111/tap/async/'+str(jobid)+'/redirect']
        ]

        responseResultsJob.set_data(method='GET',
                                    context=None,
                                    body=None,
                                    headers=responseResultsHeaders)
        req = "async/" + str(jobid) + "/results/result"
        connHandler.set_response(req, responseResultsJob)
        # Results redirect response
        responseRedirect = DummyResponse()
        responseRedirect.set_status_code(200)
        responseRedirect.set_message("OK")

        jobDataFile = data_path('job_1.vot')
        jobData = utils.read_file_content(jobDataFile)
        responseRedirect.set_data(method='GET',
                                  context=None,
                                  body=jobData,
                                  headers=None)
        req = "http://test:1111/tap/async/" + str(jobid) + "/redirect"
        connHandler.set_response(req, responseRedirect)
        tap.save_results(job, 'file.txt')

    def test_login_cert(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)

        fd, path = tempfile.mkstemp()

        tap.login(certificate_file=path)
        assert tap._TapPlus__getconnhandler()._TapConn__connectionHandler. \
            _ConnectionHandlerCadc__certificate == path, \
            "Certificate was not set"

    def test_login_failure(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)

        fd, path = tempfile.mkstemp()

        with pytest.raises(Exception):
            tap.login()
        assert tap._TapPlus__user is None, \
            "User was set"
        assert tap._TapPlus__pwd is None, \
            "Password was set"
        assert tap._TapPlusCadc__certificate is None, \
            "Certificate was set"

        with pytest.raises(Exception):
            tap.login(user='username', password='password',
                      certificate_file=path)
        assert tap._TapPlus__user is None, \
            "User was set"
        assert tap._TapPlus__pwd is None, \
            "Password was set"
        assert tap._TapPlusCadc__certificate is None, \
            "Certificate was set"

        with pytest.raises(Exception):
            tap.login(user='username')
        assert tap._TapPlus__user is None, \
            "User was set"
        assert tap._TapPlus__pwd is None, \
            "Password was set"

        with pytest.raises(Exception):
            tap.login(certificate_file='notrealfile.txt')
        assert tap._TapPlusCadc__certificate is None, \
            "Certificate was set"

        tap._TapPlus__getconnhandler().set_cookie('cookie')
        with pytest.raises(Exception):
            tap.login(certificate_file=path)
        assert tap._TapPlusCadc__certificate is None, \
            "Certificate was set"

    def test_logout(self):
        connHandler = DummyConnHandlerCadc()
        tap = TapPlusCadc("http://test:1111/tap", connhandler=connHandler)
        tap.logout()
        assert tap._TapPlus__user is None, \
            "User was set"
        assert tap._TapPlus__pwd is None, \
            "Password was set"
        assert tap._TapPlusCadc__certificate is None, \
            "Certificate was set"

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
            "Wrong description for results column '%s'. " \
            "Expected: '%s', found '%s'" % \
            (columnName, description, c.description)
        assert c.unit == unit, \
            "Wrong unit for results column '%s'. " \
            "Expected: '%s', found '%s'" % \
            (columnName, unit, c.unit)
        assert c.dtype == dataType, \
            "Wrong dataType for results column '%s'. " \
            "Expected: '%s', found '%s'" % \
            (columnName, dataType, c.dtype)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
