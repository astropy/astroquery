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

from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.utils.tap.xmlparser.jobSaxParser import JobSaxParser
from astroquery.utils.tap.xmlparser.tableSaxParser import TableSaxParser


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
                  "public.table1",
                  2,
                  ['table1_col1', 'table1_col2'])
    __check_table(tables[1],
                  "public.table2",
                  3,
                  ['table2_col1', 'table2_col2', 'table2_col3'])
    file.close()


def test_table_list_parser_with_size_bytes():
    fileName = data_path('test_tables_gaia.xml')
    file = open(fileName, 'r', encoding="utf8")
    parser = TableSaxParser()
    tables = parser.parseData(file)
    assert len(tables) == 3

    __check_table(tables[0],
                  "external.apassdr9",
                  25,
                  ['recno', 'raj2000', 'dej2000', 'e_ra', 'e_dec', 'field', 'nobs', 'mobs', 'b_v', 'e_b_v', 'vmag',
                   'e_vmag', 'u_e_vmag', 'bmag', 'e_bmag', 'u_e_bmag', 'g_mag', 'e_g_mag', 'u_e_g_mag', 'r_mag',
                   'e_r_mag', 'u_e_r_mag', 'i_mag', 'e_i_mag', 'u_e_i_mag'], 22474547200)

    __check_table(tables[1],
                  "external.catwise2020",
                  71,
                  ['obj_id', 'ra_icrs', 'e_ra_icrs', 'de_icrs', 'e_de_icrs', 'name', 'e_pos', 'xpos', 'ypos', 'sky_w1',
                   'e_sky_w1', 'conf_w1', 'sky_w2', 'e_sky_w2', 'conf_w2', 'n_w1', 'm_w1', 'n_w2', 'm_w2', 'mjd',
                   'ra_pm_deg', 'e_ra_pm_deg', 'de_pm_deg', 'e_de_pm_deg', 'e_pos_pm', 'pm_ra', 'e_pm_ra', 'pm_de',
                   'e_pm_de', 'snr_w1pm', 'snr_w2pm', 'fw1pm', 'e_fw1pm', 'fw2pm', 'e_fw2pm', 'w1mpro_pm',
                   'e_w1mpro_pm', 'chi2_w1pm', 'w2mpro_pm', 'e_w2mpro_pm', 'chi2_w2pm', 'chi2pm', 'pm_qual', 'dist',
                   'd_w1mpro', 'chi2d_w1mpro', 'd_w2mpro', 'chi2d_w2mpro', 'elon_avg', 'e_elon_avg', 'elat_avg',
                   'e_elat_avg', 'd_elon', 'e_d_elon', 'd_elat', 'e_d_elat', 'snrd_elon', 'snrd_elat', 'chi2pm_ra',
                   'chi2pm_de', 'ka', 'k1', 'k2', 'km', 'plx1', 'e_plx1', 'plx2', 'e_plx2', 'sep', 'ccf', 'abf'],
                  1366190997504)
    file.close()


def test_job_results_parser():
    fileName = data_path('test_job_results.xml')
    file = open(fileName, 'rb')
    result_table = utils.read_http_response(file, 'votable', use_names_over_ids=False)
    assert len(result_table.columns) == 57
    assert ('solution_id' in result_table.columns) and ('source_id' in result_table.columns)
    file.close()


def test_job_results_parser_vot():
    file_name = data_path('1714556098855O-result.vot')
    file = open(file_name, 'rb')
    result_table = utils.read_http_response(file, 'votable')
    assert len(result_table.columns) == 152
    assert ('solution_id' in result_table.columns) and ('DESIGNATION' in result_table.columns) and (
        'SOURCE_ID' in result_table.columns)
    file.close()


def test_job_results_parser_vot_lower_case():
    file_name = data_path('1714556098855O-result.vot')
    file = open(file_name, 'rb')
    result_table = utils.read_http_response(file, 'votable', use_names_over_ids=True)
    assert len(result_table.columns) == 152
    assert ('solution_id' in result_table.columns) and ('designation' in result_table.columns) and (
        'source_id' in result_table.columns)
    file.close()


def test_job_results_parser_json():
    file_name = data_path('test.json')
    file = open(file_name, 'rb')
    result_table = utils.read_http_response(file, 'json')
    assert len(result_table.columns) == 152
    assert ('solution_id' in result_table.columns) and ('designation' in result_table.columns) and (
        'source_id' in result_table.columns)
    file.close()


def test_job_results_parser_csv():
    file_name = data_path('1714556098855O-result.csv')
    file = open(file_name, 'rb')
    result_table = utils.read_http_response(file, 'csv')
    assert len(result_table.columns) == 152
    assert ('solution_id' in result_table.columns) and ('designation' in result_table.columns) and (
        'source_id' in result_table.columns)
    file.close()


def test_job_results_parser_ecsv():
    file_name = data_path('1714556098855O-result.ecsv')
    file = open(file_name, 'rb')
    result_table = utils.read_http_response(file, 'ecsv')
    assert len(result_table.columns) == 152
    print(result_table.columns)
    assert ('solution_id' in result_table.columns) and ('designation' in result_table.columns) and (
        'source_id' in result_table.columns)
    file.close()


def __check_table(table, qualifiedName, numColumns, columnsData, size_bytes=None):
    assert str(table.get_qualified_name()) == str(qualifiedName)
    c = table.columns
    assert len(c) == numColumns
    if size_bytes is not None:
        assert size_bytes == table.size_bytes

    for i in range(0, numColumns):
        assert str(c[i].name) == str(columnsData[i])


def __check_job(job, jobid, jobPhase, jobOwner):
    assert str(job.jobid) == str(jobid)
    p = job.get_phase()
    assert str(p) == str(jobPhase)
    o = job.ownerid
    assert str(o) == str(jobOwner)
