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

        with pytest.raises(AttributeError):
            job = Job(async_job=True)
            job.get_results()

    def test_job_get_results(self):
        job = Job(async_job=True)
        jobid = "12345"
        outputFormat = "votable"
        job.jobid = jobid
        job.parameters['format'] = outputFormat
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
        job.connHandler = connHandler

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

    def test_job_phase(self):
        job = Job(async_job=True)
        jobid = "12345"
        outputFormat = "votable"
        job.jobid = jobid
        job.parameters['format'] = outputFormat
        job.set_phase("COMPLETED")
        try:
            job.set_phase("RUN")
            self.fail("Exception expected. " +
                      "Phase cannot be changed for a finished job")
        except ValueError:
            # ok
            pass
        try:
            job.start()
            self.fail("Exception expected. " +
                      "A job in 'COMPLETE' phase cannot be started")
        except ValueError:
            # ok
            pass
        try:
            job.abort()
            self.fail("Exception expected. " +
                      "A job in 'COMPLETE' phase cannot be aborted")
        except ValueError:
            # ok
            pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
