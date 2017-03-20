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
from astroquery.utils.tap.xmlparser.tableSaxParser import TableSaxParser
from astroquery.utils.tap.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.utils.tap.xmlparser.jobSaxParser import JobSaxParser
from astroquery.utils.tap.xmlparser import utils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class XmlParserTest(unittest.TestCase):

    def test_jobs_list_parser(self):
        fileName = data_path('test_jobs_list.xml')
        file = open(fileName, 'r')
        parser = JobListSaxParser()
        jobs = parser.parseData(file)
        assert len(jobs) == 2, \
            "Expected table list size: 1, found %d" % len(jobs)
        self.__check_job(jobs[0], "1479386030738O", "COMPLETED", None)
        self.__check_job(jobs[1], "14793860307381", "ERROR", None)
        file.close()

    def test_jobs_parser(self):
        fileName = data_path('test_jobs_async.xml')
        file = open(fileName, 'r')
        parser = JobSaxParser()
        jobs = parser.parseData(file)
        assert len(jobs) == 2, \
            "Expected table list size: 1, found %d" % len(jobs)
        self.__check_job(jobs[0], "1479386030738O", "COMPLETED", "anonymous")
        self.__check_job(jobs[1], "14793860307381", "ERROR", "anonymous")
        file.close()

    def test_table_list_parser(self):
        fileName = data_path('test_tables.xml')
        file = open(fileName, 'r')
        parser = TableSaxParser()
        tables = parser.parseData(file)
        assert len(tables) == 2, \
            "Expected table list size: 2, found %d" % len(tables)
        self.__check_table(tables[0],
                           "table1",
                           2,
                           ['table1_col1', 'table1_col2'])
        self.__check_table(tables[1],
                           "table2",
                           3,
                           ['table2_col1', 'table2_col2', 'table2_col3'])
        file.close()

    def test_job_results_parser(self):
        fileName = data_path('test_job_results.xml')
        file = open(fileName, 'rb')
        resultTable = utils.read_http_response(file, 'votable')
        assert len(resultTable.columns) == 57, \
            "Expected 57 columsn, found %d" % len(resultTable.columns)
        file.close()

    def __check_table(self, table, baseName, numColumns, columnsData):
        qualifiedName = "public.%s" % baseName
        assert str(table.get_qualified_name()) == str(qualifiedName), \
            "Expected qualified table name: '%s', found '%s'" % \
            (qualifiedName, table.get_qualified_name())
        c = table.get_columns()
        assert len(c) == numColumns, \
            "Expected table1 num columns: %d, found %d" % (numColumns, len(c))
        for i in range(0, numColumns):
            assert str(c[i].get_name()) == str(columnsData[i]), \
                "Expected column name '%s', found: '%s'" % \
                (columnsData[i], c[i].get_name())

    def __check_job(self, job, jobid, jobPhase, jobOwner):
        assert str(job.get_jobid()) == str(jobid), \
            "Expected job id: '%s', found '%s'" % (jobid, job.get_jobid())
        p = job.get_phase()
        assert str(p) == str(jobPhase), \
            "Expected job phase: %s, found %s" % (jobPhase, p)
        o = job.get_ownerid()
        assert str(o) == str(jobOwner), \
            "Expected job owner: %s, found %s" % (jobOwner, o)
