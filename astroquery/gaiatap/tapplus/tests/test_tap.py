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
import unittest
import os
import numpy as np
import astropy.units as u
from gaiatap.tapplus.model.job import Job
from gaiatap.tapplus.conn.tests.DummyConnHandler import DummyConnHandler
from gaiatap.tapplus.conn.tests.DummyResponse import DummyResponse
from gaiatap.tapplus.tap import TapPlus
from gaiatap.tapplus.xmlparser import utils
from gaiatap.tapplus import taputils
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.units import Quantity


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class TestTap(unittest.TestCase):

    def testLoadTables(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        responseLoadTable = DummyResponse()
        responseLoadTable.setStatusCode(500)
        responseLoadTable.setMessage("ERROR")
        tableDataFile = data_path('test_tables.xml')
        tableData = utils.readFileContent(tableDataFile)
        responseLoadTable.setData(method='GET', context=None, body=tableData, headers=None)
        tableRequest = "tables"
        connHandler.setResponse(tableRequest, responseLoadTable)
        try:
            tap.load_tables()
            self.fail("Exception expected: no connection handeler defined")
        except:
            pass
        responseLoadTable.setStatusCode(200)
        responseLoadTable.setMessage("OK")
        res = tap.load_tables()
        assert len(res) == 2, "Number of tables expected: %d, found: %d" % (2, len(res))
        #Table 1
        table = self.__findTable('public', 'table1', res)
        assert table.get_description() == 'Table1 desc', "Wrong description for table1. Expected: %s, found %s" % ('Table1 desc', table.get_description())
        columns = table.get_columns()
        assert len(columns) == 2, "Number of columns for table1. Expected: %d, found: %d" % (2, len(columns))
        col = self.__findColumn('table1_col1', columns)
        self.__checkColumn(col, 'Table1 Column1 desc', '', 'VARCHAR', 'indexed')
        col = self.__findColumn('table1_col2', columns)
        self.__checkColumn(col, 'Table1 Column2 desc', '', 'INTEGER', None)
        #Table 2
        table = self.__findTable('public', 'table2', res)
        assert table.get_description() == 'Table2 desc', "Wrong description for table2. Expected: %s, found %s" % ('Table2 desc', table.get_description())
        columns = table.get_columns()
        assert len(columns) == 3, "Number of columns for table2. Expected: %d, found: %d" % (3, len(columns))
        col = self.__findColumn('table2_col1', columns)
        self.__checkColumn(col, 'Table2 Column1 desc', '', 'VARCHAR', 'indexed')
        col = self.__findColumn('table2_col2', columns)
        self.__checkColumn(col, 'Table2 Column2 desc', '', 'INTEGER', None)
        col = self.__findColumn('table2_col3', columns)
        self.__checkColumn(col, 'Table2 Column3 desc', '', 'INTEGER', None)
        pass
    
    def testLoadTable(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        responseLoadTable = DummyResponse()
        responseLoadTable.setStatusCode(500)
        responseLoadTable.setMessage("ERROR")
        tableDataFile = data_path('test_table1.xml')
        tableData = utils.readFileContent(tableDataFile)
        responseLoadTable.setData(method='GET', context=None, body=tableData, headers=None)
        tableSchema = "public"
        tableName = "table1"
        fullQualifiedTableName = tableSchema + "." + tableName
        tableRequest = "tables?tables=" + fullQualifiedTableName
        connHandler.setResponse(tableRequest, responseLoadTable)
        try:
            tap.load_table(fullQualifiedTableName)
            self.fail("Exception expected: no connection handeler defined")
        except:
            pass
        responseLoadTable.setStatusCode(200)
        responseLoadTable.setMessage("OK")
        table = tap.load_table(fullQualifiedTableName)
        assert table is not None, "Table '%s' not found" % (fullQualifiedTableName)
        assert table.get_description() == 'Table1 desc', "Wrong description for table1. Expected: %s, found %s" % ('Table1 desc', table.get_description())
        columns = table.get_columns()
        assert len(columns) == 2, "Number of columns for table1. Expected: %d, found: %d" % (2, len(columns))
        col = self.__findColumn('table1_col1', columns)
        self.__checkColumn(col, 'Table1 Column1 desc', '', 'VARCHAR', 'indexed')
        col = self.__findColumn('table1_col2', columns)
        self.__checkColumn(col, 'Table1 Column2 desc', '', 'INTEGER', None)
        pass
    
    def testLaunchSyncJob(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        responseLaunchJob = DummyResponse()
        responseLaunchJob.setStatusCode(500)
        responseLaunchJob.setMessage("ERROR")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.readFileContent(jobDataFile)
        responseLaunchJob.setData(method='POST', context=None, body=jobData, headers=None)
        query = 'select top 5 * from table'
        dTmp = {"q": query}
        dTmpEncoded = connHandler.url_encode(dTmp)
        p = dTmpEncoded.find("=")
        q = dTmpEncoded[p+1:]
        dictTmp = {
            "REQUEST": "doQuery", \
            "LANG":    "ADQL", \
            "FORMAT":  "votable", \
            "PHASE":  "RUN", \
            "QUERY":   str(q)}
        sortedKey = taputils.tapUtilCreateSortedDictKey(dictTmp)
        jobRequest = "sync?" + sortedKey
        connHandler.setResponse(jobRequest, responseLaunchJob)
        try:
            tap.launch_job(query)
            self.fail("Exception expected: no connection handler defined")
        except:
            pass
        responseLaunchJob.setStatusCode(200)
        responseLaunchJob.setMessage("OK")
        job = tap.launch_job(query)
        assert job is not None, "Expected a valid job"
        assert job.is_sync() == True, "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', "Wrong job phase. Expected: %s, found %s" % ('COMPLETED', job.get_phase())
        assert job.is_failed() == False, "Wrong job status (set Failed = True)"
        #results
        results = job.get_results()
        assert len(results) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(results))
        self.__checkResultsColumn(results, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(results, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(results, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(results, 'table1_oid', 'table1_oid', None, np.int32)
        pass
    
    def testLauncAsyncJob(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        jobid = '12345'
        #Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.setStatusCode(500)
        responseLaunchJob.setMessage("ERROR")
        #list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
            ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        responseLaunchJob.setData(method='POST', context=None, body=None, headers=launchResponseHeaders)
        query = 'query'
        dictTmp = {
            "REQUEST": "doQuery", \
            "LANG":    "ADQL", \
            "FORMAT":  "votable", \
            "PHASE":  "RUN", \
            "QUERY":   str(query)}
        sortedKey = taputils.tapUtilCreateSortedDictKey(dictTmp)
        req = "async?" + sortedKey
        connHandler.setResponse(req, responseLaunchJob)
        #Phase response
        responsePhase = DummyResponse()
        responsePhase.setStatusCode(500)
        responsePhase.setMessage("ERROR")
        responsePhase.setData(method='GET', context=None, body="COMPLETED", headers=None)
        req = "async/" + jobid + "/phase"
        connHandler.setResponse(req, responsePhase)
        #Results response
        responseResultsJob = DummyResponse()
        responseResultsJob.setStatusCode(500)
        responseResultsJob.setMessage("ERROR")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.readFileContent(jobDataFile)
        responseResultsJob.setData(method='GET', context=None, body=jobData, headers=None)
        req = "async/" + jobid + "/results/result"
        connHandler.setResponse(req, responseResultsJob)
        try:
            tap.launch_job(query, async=True)
            self.fail("Exception expected: job launch response 500")
        except:
            pass
        responseLaunchJob.setStatusCode(303)
        responseLaunchJob.setMessage("OK")
        try:
            tap.launch_job(query, async=True)
            self.fail("Exception expected: job phase response 500")
        except:
            pass
        responsePhase.setStatusCode(200)
        responsePhase.setMessage("OK")
        try:
            tap.launch_job(query, async=True)
            self.fail("Exception expected: job results response 500")
        except:
            pass
        responseResultsJob.setStatusCode(200)
        responseResultsJob.setMessage("OK")
        job = tap.launch_job(query, async=True)
        assert job is not None, "Expected a valid job"
        assert job.is_sync() == False, "Expected an asynchronous job"
        assert job.get_phase() == 'COMPLETED', "Wrong job phase. Expected: %s, found %s" % ('COMPLETED', job.get_phase())
        assert job.is_failed() == False, "Wrong job status (set Failed = True)"
        #results
        results = job.get_results()
        assert len(results) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(results))
        self.__checkResultsColumn(results, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(results, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(results, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(results, 'table1_oid', 'table1_oid', None, np.int32)
        pass
    
    def testListAsyncJobs(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        response = DummyResponse()
        response.setStatusCode(500)
        response.setMessage("ERROR")
        jobDataFile = data_path('jobs_list.xml')
        jobData = utils.readFileContent(jobDataFile)
        response.setData(method='GET', context=None, body=jobData, headers=None)
        req = "async"
        connHandler.setResponse(req, response)
        try:
            tap.list_async_jobs()
            self.fail("Exception expected: job list response 500")
        except:
            pass
        response.setStatusCode(200)
        response.setMessage("OK")
        jobs = tap.list_async_jobs()
        assert len(jobs) == 2,  "Wrong jobs number. Expected: %d, found %d" % (2, len(jobs))
        assert jobs[0].get_jobid() == '12345', "Wrong job id. Expected: %s, found %s" % ('12345', jobs[0].get_jobid())
        assert jobs[0].get_phase() == 'COMPLETED', "Wrong job phase for job %s. Expected: %s, found %s" % (jobs[0].get_jobid(), 'COMPLETED', jobs[0].get_phase())
        assert jobs[1].get_jobid() == '77777', "Wrong job id. Expected: %s, found %s" % ('77777', jobs[1].get_jobid())
        assert jobs[1].get_phase() == 'ERROR', "Wrong job phase for job %s. Expected: %s, found %s" % (jobs[1].get_jobid(), 'ERROR', jobs[1].get_phase())
        pass
    
    def testQueryObject(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        #Launch response: we use default response because the query contains decimals 
        responseLaunchJob = DummyResponse()
        responseLaunchJob.setStatusCode(200)
        responseLaunchJob.setMessage("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.readFileContent(jobDataFile)
        responseLaunchJob.setData(method='POST', context=None, body=jobData, headers=None)
        #The query contains decimals: force default response
        connHandler.setDefaultResponse(responseLaunchJob)
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree), frame='icrs')
        try:
            tap.query_object(sc)
            self.fail("Exception expected: Missing width")
        except:
            pass
        width = Quantity(12, u.deg)
        try:
            tap.query_object(sc, width=width)
            self.fail("Exception expected: Missing height")
        except:
            pass
        height = Quantity(10, u.deg)
        table = tap.query_object(sc, width=width, height=height)
        assert len(table) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(table))
        self.__checkResultsColumn(table, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(table, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(table, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(table, 'table1_oid', 'table1_oid', None, np.int32)
        #by radius
        radius = Quantity(1,u.deg)
        table = tap.query_object(sc, radius=radius)
        assert len(table) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(table))
        self.__checkResultsColumn(table, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(table, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(table, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(table, 'table1_oid', 'table1_oid', None, np.int32)
        pass
    
    def testQueryObjectAsync(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        jobid = '12345'
        #Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.setStatusCode(303)
        responseLaunchJob.setMessage("OK")
        #list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
            ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        responseLaunchJob.setData(method='POST', context=None, body=None, headers=launchResponseHeaders)
        connHandler.setDefaultResponse(responseLaunchJob)
        #Phase response
        responsePhase = DummyResponse()
        responsePhase.setStatusCode(200)
        responsePhase.setMessage("OK")
        responsePhase.setData(method='GET', context=None, body="COMPLETED", headers=None)
        req = "async/" + jobid + "/phase"
        connHandler.setResponse(req, responsePhase)
        #Results response
        responseResultsJob = DummyResponse()
        responseResultsJob.setStatusCode(200)
        responseResultsJob.setMessage("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.readFileContent(jobDataFile)
        responseResultsJob.setData(method='GET', context=None, body=jobData, headers=None)
        req = "async/" + jobid + "/results/result"
        connHandler.setResponse(req, responseResultsJob)
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree), frame='icrs')
        width = Quantity(12, u.deg)
        height = Quantity(10, u.deg)
        table = tap.query_object_async(sc, width=width, height=height)
        assert len(table) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(table))
        self.__checkResultsColumn(table, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(table, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(table, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(table, 'table1_oid', 'table1_oid', None, np.int32)
        #by radius
        radius = Quantity(1,u.deg)
        table = tap.query_object_async(sc, radius=radius)
        assert len(table) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(table))
        self.__checkResultsColumn(table, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(table, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(table, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(table, 'table1_oid', 'table1_oid', None, np.int32)
        pass
    
    def testConeSearchSync(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        #Launch response: we use default response because the query contains decimals 
        responseLaunchJob = DummyResponse()
        responseLaunchJob.setStatusCode(200)
        responseLaunchJob.setMessage("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.readFileContent(jobDataFile)
        responseLaunchJob.setData(method='POST', context=None, body=jobData, headers=None)
        ra = 19.0
        dec = 20.0
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        #MAIN_GAIA_TABLE_RA = "ra"
        #MAIN_GAIA_TABLE_DEC = "dec"
        #MAIN_GAIA_TABLE = "gaiadr1.gaia_source"
        #query = "SELECT  TOP 2000 DISTANCE(POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"), \
        #    POINT('ICRS',"+str(ra)+","+str(dec)+")) AS dist, * \
        #    FROM "+str(MAIN_GAIA_TABLE)+" WHERE CONTAINS(\
        #    POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"),\
        #    CIRCLE('ICRS',"+str(ra)+","+str(dec)+", "+str(radius)+"))=1 \
        #    ORDER BY dist ASC"
        #dTmp = {"q": query}
        #dTmpEncoded = connHandler.url_encode(dTmp)
        #p = dTmpEncoded.find("=")
        #q = dTmpEncoded[p+1:]
        #dictTmp = {
        #    "REQUEST": "doQuery", \
        #    "LANG":    "ADQL", \
        #    "FORMAT":  "votable", \
        #    "PHASE":  "RUN", \
        #    "QUERY":   str(q)}
        #sortedKey = taputils.tapUtilCreateSortedDictKey(dictTmp)
        #jobRequest = "sync?" + sortedKey
        connHandler.setDefaultResponse(responseLaunchJob)
        job = tap.cone_search(sc, radius, async=False)
        assert job is not None, "Expected a valid job"
        assert job.is_sync() == True, "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', "Wrong job phase. Expected: %s, found %s" % ('COMPLETED', job.get_phase())
        assert job.is_failed() == False, "Wrong job status (set Failed = True)"
        #results
        results = job.get_results()
        assert len(results) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(results))
        self.__checkResultsColumn(results, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(results, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(results, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(results, 'table1_oid', 'table1_oid', None, np.int32)
        pass
    
    def testConeSearchAsync(self):
        connHandler = DummyConnHandler()
        tap = TapPlus("http://test:1111/tap", connhandler=connHandler)
        jobid = '12345'
        #Launch response
        responseLaunchJob = DummyResponse()
        responseLaunchJob.setStatusCode(303)
        responseLaunchJob.setMessage("OK")
        #list of list (httplib implementation for headers in response)
        launchResponseHeaders = [
            ['location', 'http://test:1111/tap/async/' + jobid]
            ]
        responseLaunchJob.setData(method='POST', context=None, body=None, headers=launchResponseHeaders)
        ra = 19
        dec = 20
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        #MAIN_GAIA_TABLE_RA = "ra"
        #MAIN_GAIA_TABLE_DEC = "dec"
        #MAIN_GAIA_TABLE = "gaiadr1.gaia_source"
        #query = "SELECT DISTANCE(POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"), \
        #    POINT('ICRS',"+str(ra)+","+str(dec)+")) AS dist, * \
        #    FROM "+str(MAIN_GAIA_TABLE)+" WHERE CONTAINS(\
        #    POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"),\
        #    CIRCLE('ICRS',"+str(ra)+","+str(dec)+", "+str(radius)+"))=1 \
        #    ORDER BY dist ASC"
        #dTmp = {"q": query}
        #dTmpEncoded = connHandler.url_encode(dTmp)
        #p = dTmpEncoded.find("=")
        #q = dTmpEncoded[p+1:]
        #dictTmp = {
        #    "REQUEST": "doQuery", \
        #    "LANG":    "ADQL", \
        #    "FORMAT":  "votable", \
        #    "PHASE":  "RUN", \
        #    "QUERY":   str(q)}
        #sortedKey = taputils.tapUtilCreateSortedDictKey(dictTmp)
        #req = "async?" + sortedKey
        connHandler.setDefaultResponse(responseLaunchJob)
        #Phase response
        responsePhase = DummyResponse()
        responsePhase.setStatusCode(200)
        responsePhase.setMessage("OK")
        responsePhase.setData(method='GET', context=None, body="COMPLETED", headers=None)
        req = "async/" + jobid + "/phase"
        connHandler.setResponse(req, responsePhase)
        #Results response
        responseResultsJob = DummyResponse()
        responseResultsJob.setStatusCode(200)
        responseResultsJob.setMessage("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.readFileContent(jobDataFile)
        responseResultsJob.setData(method='GET', context=None, body=jobData, headers=None)
        req = "async/" + jobid + "/results/result"
        connHandler.setResponse(req, responseResultsJob)
        job = tap.cone_search(sc, radius, async=True)
        assert job is not None, "Expected a valid job"
        assert job.is_sync() == False, "Expected an asynchronous job"
        assert job.get_phase() == 'COMPLETED', "Wrong job phase. Expected: %s, found %s" % ('COMPLETED', job.get_phase())
        assert job.is_failed() == False, "Wrong job status (set Failed = True)"
        #results
        results = job.get_results()
        assert len(results) == 3,  "Wrong job results (num rows). Expected: %d, found %d" % (3, len(results))
        self.__checkResultsColumn(results, 'alpha', 'alpha', None, np.float64)
        self.__checkResultsColumn(results, 'delta', 'delta', None, np.float64)
        self.__checkResultsColumn(results, 'source_id', 'source_id', None, np.object)
        self.__checkResultsColumn(results, 'table1_oid', 'table1_oid', None, np.int32)
        pass
    
    def __findTable(self, schemaName, tableName, tables):
        qualifiedName = schemaName + "." + tableName
        for table in (tables):
            if table.get_qualified_name() == qualifiedName:
                return table
            pass
        #not found: raise exception
        self.fail("Table '"+qualifiedName+"' not found")
        pass
    
    def __findColumn(self, columnName, columns):
        for c in (columns):
            if c.get_name() == columnName:
                return c
            pass
        #not found: raise exception
        self.fail("Column '"+columnName+"' not found")
        pass
    
    def __checkColumn(self, column, description, unit, dataType, flag):
        assert column.get_description() == description, "Wrong description for table %s. Expected: '%s', found '%s'" % (column.get_name(), description, column.get_description())
        assert column.get_unit() == unit, "Wrong unit for table %s. Expected: '%s', found '%s'" % (column.get_name(), unit, column.get_unit())
        assert column.get_data_type() == dataType, "Wrong dataType for table %s. Expected: '%s', found '%s'" % (column.get_name(), dataType, column.get_data_type())
        assert column.get_flag() == flag, "Wrong flag for table %s. Expected: '%s', found '%s'" % (column.get_name(), flag, column.get_flag())
        pass
    
    def __checkResultsColumn(self, results, columnName, description, unit, dataType):
        c = results[columnName]
        assert c.description == description, "Wrong description for results column '%s'. Expected: '%s', found '%s'" % (columnName, description, c.description)
        assert c.unit == unit, "Wrong unit for results column '%s'. Expected: '%s', found '%s'" % (columnName, unit, c.unit)
        assert c.dtype == dataType, "Wrong dataType for results column '%s'. Expected: '%s', found '%s'" % (columnName, dataType, c.dtype)
        pass
    
    pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()