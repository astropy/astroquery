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
import pytest

from astroquery.utils.tap.model.job import Job
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.xmlparser import utils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestJob(unittest.TestCase):

    def test_job_basic(self):
        job = Job(async_job=False)
        res = job.is_sync()
        assert res, \
            "Sync job, expected: %s, found: %s" % (str(True), str(res))
        res = job.is_async()
        assert res is False, \
            "Sync job, expected: %s, found: %s" % (str(False), str(res))
        job = Job(async_job=True)
        res = job.is_sync()
        assert res is False, \
            "Async job, expected: %s, found: %s" % (str(False), str(res))
        res = job.is_async()
        assert res, \
            "Async job, expected: %s, found: %s" % (str(True), str(res))

        with pytest.raises(AttributeError):
            job.get_results()

        # parameters
        query = "query"
        jobid = "jobid"
        remoteLocation = "remoteLocation"
        phase = "phase"
        outputFile = "outputFile"
        responseStatus = "responseStatus"
        responseMsg = "responseMsg"
        runid = "runid"
        ownerid = "ownerid"
        startTime = "startTime"
        endTime = "endTime"
        creationTime = "creationTime"
        executionDuration = "executionDuration"
        destruction = "destruction"
        locationid = "locationid"
        name = "name"
        quote = "quote"
        job = Job(async_job=False, query=query)
        job.set_jobid(jobid)
        job.set_remote_location(remoteLocation)
        job.set_phase(phase)
        job.set_output_file(outputFile)
        job.set_response_status(responseStatus, responseMsg)
        job.set_runid(runid)
        job.set_ownerid(ownerid)
        job.set_start_time(startTime)
        job.set_end_time(endTime)
        job.set_creation_time(creationTime)
        job.set_execution_duration(executionDuration)
        job.set_destruction(destruction)
        job.set_locationid(locationid)
        job.set_name(name)
        job.set_quote(quote)
        assert job.get_query() == query, \
            "query, expected: %s, found: %s" % (query,
                                                job.get_query())
        assert job.get_jobid() == jobid, \
            "jobid, expected: %s, found: %s" % (jobid,
                                                job.get_jobid())
        assert job.get_remote_location() == remoteLocation, \
            "remoteLocation, expected: %s, found: %s" % (remoteLocation,
                                                         job.get_remote_location())
        assert job.get_phase() == phase, \
            "phase, expected: %s, found: %s" % (phase,
                                                job.get_phase())
        assert job.get_output_file() == outputFile, \
            "outputFile, expected: %s, found: %s" % (outputFile,
                                                     job.get_output_file())
        assert job.get_response_status() == responseStatus, \
            "responseStatus, expected: %s, found: %s" % (responseStatus,
                                                         job.get_response_status())
        assert job.get_response_msg() == responseMsg, \
            "responseMsg, expected: %s, found: %s" % (responseMsg,
                                                      job.get_response_msg())
        assert job.get_results() is None, \
            "results, expected: %s, found: %s" % (str(None),
                                                  job.get_results())
        assert job.get_runid() == runid, \
            "runid, expected: %s, found: %s" % (runid,
                                                job.get_runid())
        assert job.get_ownerid() == ownerid, \
            "ownerid, expected: %s, found: %s" % (ownerid,
                                                  job.get_ownerid())
        assert job.get_start_time() == startTime, \
            "startTime, expected: %s, found: %s" % (startTime,
                                                    job.get_start_time())
        assert job.get_end_time() == endTime, \
            "endTime, expected: %s, found: %s" % (endTime,
                                                  job.get_end_time())
        assert job.get_creation_time() == creationTime, \
            "creationTime, expected: %s, found: %s" % (creationTime,
                                                       job.get_creation_time())
        assert job.get_execution_duration() == executionDuration, \
            "executionDuration, expected: %s, found: %s" % (executionDuration,
                                                            job.get_execution_duration())
        assert job.get_destruction() == destruction, \
            "destruction, expected: %s, found: %s" % (destruction,
                                                      job.get_destruction())
        assert job.get_locationid() == locationid, \
            "locationid, expected: %s, found: %s" % (locationid,
                                                     job.get_locationid())
        assert job.get_name() == name, \
            "name, expected: %s, found: %s" % (name,
                                               job.get_name())
        assert job.get_quote() == quote, \
            "quote, expected: %s, found: %s" % (quote,
                                                job.get_quote())

    def test_job_get_results(self):
        job = Job(async_job=True)
        jobid = "12345"
        outputFormat = "votable"
        job.set_jobid(jobid)
        job.set_output_format(outputFormat)
        responseCheckPhase = DummyResponse()
        responseCheckPhase.set_status_code(500)
        responseCheckPhase.set_message("ERROR")
        responseCheckPhase.set_data(method='GET',
                                    context=None,
                                    body='FINISHED',
                                    headers=None)
        waitRequest = "async/"+str(jobid)+"/phase"
        connHandler = DummyConnHandler()
        connHandler.set_response(waitRequest, responseCheckPhase)
        job.set_connhandler(connHandler)

        with pytest.raises(Exception):
            job.get_results()

        responseCheckPhase.set_status_code(200)
        responseCheckPhase.set_message("OK")
        responseGetData = DummyResponse()
        responseGetData.set_status_code(500)
        responseGetData.set_message("ERROR")
        jobContentFileName = data_path('result_1.vot')
        jobContent = utils.read_file_content(jobContentFileName)
        responseGetData.set_data(method='GET',
                                context=None,
                                body=jobContent,
                                headers=None)
        dataRequest = "async/" + str(jobid) + "/results/result"
        connHandler.set_response(dataRequest, responseGetData)

        with pytest.raises(Exception):
            job.get_results()

        responseGetData.set_status_code(200)
        responseGetData.set_message("OK")
        res = job.get_results()
        assert len(res) == 3, \
            "Num rows. Expected %d, found %d" % (3, len(res))
        assert len(res.columns) == 4, \
            "Num cols. Expected %d, found %d" % (4, len(res.columns))
        for cn in ['alpha', 'delta', 'source_id', 'table1_oid']:
            if cn not in res.colnames:
                self.fail(cn + " column name not found" + str(res.colnames))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
