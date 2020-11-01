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
from astroquery.utils.tap.xmlparser.tableSaxParser import TableSaxParser
from astroquery.utils.tap.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.utils.tap.xmlparser.jobSaxParser import JobSaxParser
from astroquery.utils.tap.xmlparser import utils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_jobs_list_parser():
    fileName = data_path('test_jobs_list.xml')
    file = open(fileName, 'r')
    parser = JobListSaxParser()
    jobs = parser.parseData(file)
    assert len(jobs) == 2
    __check_job(jobs[0], "1479386030738O", "COMPLETED", None)
    __check_job(jobs[1], "14793860307381", "ERROR", None)
    file.close()


def test_jobs_parser():
    fileName = data_path('test_jobs_async.xml')
    file = open(fileName, 'r')
    parser = JobSaxParser()
    jobs = parser.parseData(file)
    assert len(jobs) == 2
    __check_job(jobs[0], "1479386030738O", "COMPLETED", "anonymous")
    __check_job(jobs[1], "14793860307381", "ERROR", "anonymous")
    file.close()


def test_table_list_parser():
    fileName = data_path('test_tables.xml')
    file = open(fileName, 'r')
    parser = TableSaxParser()
    tables = parser.parseData(file)
    assert len(tables) == 2
    __check_table(tables[0],
                  "table1",
                  2,
                  ['table1_col1', 'table1_col2'])
    __check_table(tables[1],
                  "table2",
                  3,
                  ['table2_col1', 'table2_col2', 'table2_col3'])
    file.close()


def test_job_results_parser():
    fileName = data_path('test_job_results.xml')
    file = open(fileName, 'rb')
    resultTable = utils.read_http_response(file, 'votable')
    assert len(resultTable.columns) == 57
    file.close()


def __check_table(table, baseName, numColumns, columnsData):
    qualifiedName = f"public.{baseName}"
    assert str(table.get_qualified_name()) == str(qualifiedName)
    c = table.columns
    assert len(c) == numColumns
    for i in range(0, numColumns):
        assert str(c[i].name) == str(columnsData[i])


def __check_job(job, jobid, jobPhase, jobOwner):
    assert str(job.jobid) == str(jobid)
    p = job.get_phase()
    assert str(p) == str(jobPhase)
    o = job.ownerid
    assert str(o) == str(jobOwner)
