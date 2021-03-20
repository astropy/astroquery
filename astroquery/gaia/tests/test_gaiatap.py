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
import pytest

from astroquery.gaia.core import GaiaClass
from astroquery.gaia.tests.DummyTapHandler import DummyTapHandler
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
import astropy.units as u
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.units import Quantity
import numpy as np
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap.core import TapPlus, TAP_CLIENT_ID
from astroquery.utils.tap import taputils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTap(unittest.TestCase):

    def test_query_object(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(connHandler, tapplus)
        # Launch response: we use default response because the query contains
        # decimals
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(200)
        responseLaunchJob.set_message("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.read_file_content(jobDataFile)
        responseLaunchJob.set_data(method='POST',
                                   context=None,
                                   body=jobData,
                                   headers=None)
        # The query contains decimals: force default response
        connHandler.set_default_response(responseLaunchJob)
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree),
                      frame='icrs')
        with pytest.raises(ValueError) as err:
            tap.query_object(sc)
        assert "Missing required argument: width" in err.value.args[0]

        width = Quantity(12, u.deg)

        with pytest.raises(ValueError) as err:
            tap.query_object(sc, width=width)
        assert "Missing required argument: height" in err.value.args[0]

        height = Quantity(10, u.deg)
        table = tap.query_object(sc, width=width, height=height)
        assert len(table) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(table))
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        # by radius
        radius = Quantity(1, u.deg)
        table = tap.query_object(sc, radius=radius)
        assert len(table) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(table))
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_query_object_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(connHandler, tapplus)
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
        connHandler.set_default_response(responseLaunchJob)
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
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree),
                      frame='icrs')
        width = Quantity(12, u.deg)
        height = Quantity(10, u.deg)
        table = tap.query_object_async(sc, width=width, height=height)
        assert len(table) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(table))
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        # by radius
        radius = Quantity(1, u.deg)
        table = tap.query_object_async(sc, radius=radius)
        assert len(table) == 3, \
            "Wrong job results (num rows). Expected: %d, found %d" % \
            (3, len(table))
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_cone_search_sync(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(connHandler, tapplus)
        # Launch response: we use default response because the query contains
        # decimals
        responseLaunchJob = DummyResponse()
        responseLaunchJob.set_status_code(200)
        responseLaunchJob.set_message("OK")
        jobDataFile = data_path('job_1.vot')
        jobData = utils.read_file_content(jobDataFile)
        responseLaunchJob.set_data(method='POST',
                                   context=None,
                                   body=jobData,
                                   headers=None)
        ra = 19.0
        dec = 20.0
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        connHandler.set_default_response(responseLaunchJob)
        job = tap.cone_search(sc, radius)
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
                                    object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_cone_search_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(connHandler, tapplus)
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
        ra = 19
        dec = 20
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        connHandler.set_default_response(responseLaunchJob)
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
        job = tap.cone_search_async(sc, radius)
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
                                    object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def __check_results_column(self, results, columnName, description, unit,
                               dataType):
        c = results[columnName]
        assert c.description == description, \
            "Wrong description for results column '%s'. " % \
            "Expected: '%s', found '%s'" % \
            (columnName, description, c.description)
        assert c.unit == unit, \
            "Wrong unit for results column '%s'. " % \
            "Expected: '%s', found '%s'" % \
            (columnName, unit, c.unit)
        assert c.dtype == dataType, \
            "Wrong dataType for results column '%s'. " % \
            "Expected: '%s', found '%s'" % \
            (columnName, dataType, c.dtype)

    def test_load_data(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        ids = "1,2,3,4"
        retrieval_type = "epoch_photometry"
        valid_data = True
        band = None
        format = "votable"
        verbose = True
        data_structure = "INDIVIDUAL"
        output_file = os.path.abspath("output_file")
        path_to_end_with = os.path.join("gaia", "test", "output_file")
        if not output_file.endswith(path_to_end_with):
            output_file = os.path.abspath(path_to_end_with)

        params_dict = {}
        params_dict['VALID_DATA'] = "true"
        params_dict['ID'] = ids
        params_dict['FORMAT'] = str(format)
        params_dict['RETRIEVAL_TYPE'] = str(retrieval_type)
        params_dict['DATA_STRUCTURE'] = str(data_structure)
        params_dict['USE_ZIP_ALWAYS'] = 'true'

        tap.load_data(ids=ids,
                      retrieval_type=retrieval_type,
                      valid_data=valid_data,
                      band=band,
                      format=format,
                      verbose=verbose,
                      output_file=output_file)
        parameters = {}
        parameters['params_dict'] = params_dict
        # Output file name contains a timestamp: cannot be verified
        of = dummyHandler._DummyTapHandler__parameters['output_file']
        parameters['output_file'] = of
        parameters['verbose'] = verbose
        dummyHandler.check_call('load_data', parameters)

    def test_get_datalinks(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)
        ids = ["1", "2", "3", "4"]
        verbose = True
        parameters = {}
        parameters['ids'] = ids
        parameters['verbose'] = verbose
        tap.get_datalinks(ids, verbose)
        dummyHandler.check_call('get_datalinks', parameters)
        tap.get_datalinks(ids, verbose)
        dummyHandler.check_call('get_datalinks', parameters)

    def test_xmatch(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(connHandler, tapplus)
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
        connHandler.set_default_response(responseLaunchJob)
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
        query = ("SELECT crossmatch_positional(",
                 "'schemaA','tableA','schemaB','tableB',1.0,'results')",
                 "FROM dual;")
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
        # check parameters
        # missing table A
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a=None,
                            full_qualified_table_name_b='schemaB.tableB',
                            results_table_name='results')
        assert "Table name A argument is mandatory" in err.value.args[0]
        # missing schema A
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='tableA',
                            full_qualified_table_name_b='schemaB.tableB',
                            results_table_name='results')
        assert "Not found schema name in full qualified table A: 'tableA'" \
            in err.value.args[0]
        # missing table B
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                            full_qualified_table_name_b=None,
                            results_table_name='results')
        assert "Table name B argument is mandatory" in err.value.args[0]
        # missing schema B
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                            full_qualified_table_name_b='tableB',
                            results_table_name='results')
        assert "Not found schema name in full qualified table B: 'tableB'" \
            in err.value.args[0]
        # missing results table
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                            full_qualified_table_name_b='schemaB.tableB',
                            results_table_name=None)
        assert "Results table name argument is mandatory" in err.value.args[0]
        # wrong results table (with schema)
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                            full_qualified_table_name_b='schemaB.tableB',
                            results_table_name='schema.results')
        assert "Please, do not specify schema for 'results_table_name'" \
            in err.value.args[0]
        # radius < 0.1
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                            full_qualified_table_name_b='schemaB.tableB',
                            results_table_name='results', radius=0.01)
        assert "Invalid radius value. Found 0.01, valid range is: 0.1 to 10.0" \
            in err.value.args[0]
        # radius > 10.0
        with pytest.raises(ValueError) as err:
            tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                            full_qualified_table_name_b='schemaB.tableB',
                            results_table_name='results', radius=10.1)
        assert "Invalid radius value. Found 10.1, valid range is: 0.1 to 10.0" \
            in err.value.args[0]
        # check default parameters
        parameters = {}
        query = "SELECT crossmatch_positional(\
            'schemaA','tableA',\
            'schemaB','tableB',\
            1.0,\
            'results')\
            FROM dual;"
        parameters['query'] = query
        parameters['name'] = 'results'
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['background'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        job = tap.cross_match(full_qualified_table_name_a='schemaA.tableA',
                              full_qualified_table_name_b='schemaB.tableB',
                              results_table_name='results')
        assert job.async_ is True, "Expected an asynchronous job"
        assert job.get_phase() == 'COMPLETED', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('COMPLETED', job.get_phase())
        assert job.failed is False, "Wrong job status (set Failed = True)"
        job = tap.cross_match(
                        full_qualified_table_name_a='schemaA.tableA',
                        full_qualified_table_name_b='schemaB.tableB',
                        results_table_name='results',
                        background=True)
        assert job.async_ is True, "Expected an asynchronous job"
        assert job.get_phase() == 'EXECUTING', \
            "Wrong job phase. Expected: %s, found %s" % \
            ('EXECUTING', job.get_phase())
        assert job.failed is False, "Wrong job status (set Failed = True)"


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
