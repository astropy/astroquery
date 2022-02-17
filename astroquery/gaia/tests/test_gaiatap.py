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
from unittest.mock import patch

import pytest
from requests import HTTPError

from astroquery.gaia import conf
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
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        # Launch response: we use default response because the query contains
        # decimals
        response_launch_job = DummyResponse()
        response_launch_job.set_status_code(200)
        response_launch_job.set_message("OK")
        job_data_file = data_path('job_1.vot')
        job_data = utils.read_file_content(job_data_file)
        response_launch_job.set_data(method='POST',
                                     context=None,
                                     body=job_data,
                                     headers=None)
        # The query contains decimals: force default response
        conn_handler.set_default_response(response_launch_job)
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
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        jobid = '12345'
        # Launch response
        response_launch_job = DummyResponse()
        response_launch_job.set_status_code(303)
        response_launch_job.set_message("OK")
        # list of list (httplib implementation for headers in response)
        launch_response_headers = [
            ['location', 'http://test:1111/tap/async/' + jobid]
        ]
        response_launch_job.set_data(method='POST',
                                     context=None,
                                     body=None,
                                     headers=launch_response_headers)
        conn_handler.set_default_response(response_launch_job)
        # Phase response
        response_phase = DummyResponse()
        response_phase.set_status_code(200)
        response_phase.set_message("OK")
        response_phase.set_data(method='GET',
                                context=None,
                                body="COMPLETED",
                                headers=None)
        req = "async/" + jobid + "/phase"
        conn_handler.set_response(req, response_phase)
        # Results response
        response_results_job = DummyResponse()
        response_results_job.set_status_code(200)
        response_results_job.set_message("OK")
        job_data_file = data_path('job_1.vot')
        job_data = utils.read_file_content(job_data_file)
        response_results_job.set_data(method='GET',
                                      context=None,
                                      body=job_data,
                                      headers=None)
        req = "async/" + jobid + "/results/result"
        conn_handler.set_response(req, response_results_job)
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
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        # Launch response: we use default response because the query contains
        # decimals
        response_launch_job = DummyResponse()
        response_launch_job.set_status_code(200)
        response_launch_job.set_message("OK")
        job_data_file = data_path('job_1.vot')
        job_data = utils.read_file_content(job_data_file)
        response_launch_job.set_data(method='POST',
                                     context=None,
                                     body=job_data,
                                     headers=None)
        ra = 19.0
        dec = 20.0
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        conn_handler.set_default_response(response_launch_job)
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
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        jobid = '12345'
        # Launch response
        response_launch_job = DummyResponse()
        response_launch_job.set_status_code(303)
        response_launch_job.set_message("OK")
        # list of list (httplib implementation for headers in response)
        launch_response_headers = [
            ['location', 'http://test:1111/tap/async/' + jobid]
        ]
        response_launch_job.set_data(method='POST',
                                     context=None,
                                     body=None,
                                     headers=launch_response_headers)
        ra = 19
        dec = 20
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        conn_handler.set_default_response(response_launch_job)
        # Phase response
        response_phase = DummyResponse()
        response_phase.set_status_code(200)
        response_phase.set_message("OK")
        response_phase.set_data(method='GET',
                                context=None,
                                body="COMPLETED",
                                headers=None)
        req = "async/" + jobid + "/phase"
        conn_handler.set_response(req, response_phase)
        # Results response
        response_results_job = DummyResponse()
        response_results_job.set_status_code(200)
        response_results_job.set_message("OK")
        job_data_file = data_path('job_1.vot')
        job_data = utils.read_file_content(job_data_file)
        response_results_job.set_data(method='GET',
                                      context=None,
                                      body=job_data,
                                      headers=None)
        req = "async/" + jobid + "/results/result"
        conn_handler.set_response(req, response_results_job)
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

        # Regression test for #2093 and #2099 - changing the MAIN_GAIA_TABLE
        # had no effect.
        # The preceding tests should have used the default value.
        assert 'gaiadr2.gaia_source' in job.parameters['query']
        # Test changing the table name through conf.
        conf.MAIN_GAIA_TABLE = 'name_from_conf'
        job = tap.cone_search_async(sc, radius)
        assert 'name_from_conf' in job.parameters['query']
        # Changing the value through the class should overrule conf.
        tap.MAIN_GAIA_TABLE = 'name_from_class'
        job = tap.cone_search_async(sc, radius)
        assert 'name_from_class' in job.parameters['query']
        # Cleanup.
        conf.reset('MAIN_GAIA_TABLE')

    def __check_results_column(self, results, column_name, description, unit,
                               data_type):
        c = results[column_name]
        assert c.description == description, \
            "Wrong description for results column '%s'. " % \
            "Expected: '%s', found '%s'" % \
            (column_name, description, c.description)
        assert c.unit == unit, \
            "Wrong unit for results column '%s'. " % \
            "Expected: '%s', found '%s'" % \
            (column_name, unit, c.unit)
        assert c.dtype == data_type, \
            "Wrong dataType for results column '%s'. " % \
            "Expected: '%s', found '%s'" % \
            (column_name, data_type, c.dtype)

    def test_load_data(self):
        dummy_handler = DummyTapHandler()
        tap = GaiaClass(dummy_handler, dummy_handler)

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
        of = dummy_handler._DummyTapHandler__parameters['output_file']
        parameters['output_file'] = of
        parameters['verbose'] = verbose
        dummy_handler.check_call('load_data', parameters)

    def test_get_datalinks(self):
        dummy_handler = DummyTapHandler()
        tap = GaiaClass(dummy_handler, dummy_handler)
        ids = ["1", "2", "3", "4"]
        verbose = True
        parameters = {}
        parameters['ids'] = ids
        parameters['verbose'] = verbose
        tap.get_datalinks(ids, verbose)
        dummy_handler.check_call('get_datalinks', parameters)

    def test_xmatch(self):
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        jobid = '12345'
        # Launch response
        response_launch_job = DummyResponse()
        response_launch_job.set_status_code(303)
        response_launch_job.set_message("OK")
        # list of list (httplib implementation for headers in response)
        launch_response_headers = [
            ['location', 'http://test:1111/tap/async/' + jobid]
        ]
        response_launch_job.set_data(method='POST',
                                     context=None,
                                     body=None,
                                     headers=launch_response_headers)
        conn_handler.set_default_response(response_launch_job)
        # Phase response
        response_phase = DummyResponse()
        response_phase.set_status_code(200)
        response_phase.set_message("OK")
        response_phase.set_data(method='GET',
                                context=None,
                                body="COMPLETED",
                                headers=None)
        req = "async/" + jobid + "/phase"
        conn_handler.set_response(req, response_phase)
        # Results response
        response_results_job = DummyResponse()
        response_results_job.set_status_code(200)
        response_results_job.set_message("OK")
        job_data_file = data_path('job_1.vot')
        job_data = utils.read_file_content(job_data_file)
        response_results_job.set_data(method='GET',
                                      context=None,
                                      body=job_data,
                                      headers=None)
        req = "async/" + jobid + "/results/result"
        conn_handler.set_response(req, response_results_job)
        query = ("SELECT crossmatch_positional(",
                 "'schemaA','tableA','schemaB','tableB',1.0,'results')",
                 "FROM dual;")
        d_tmp = {"q": query}
        d_tmp_encoded = conn_handler.url_encode(d_tmp)
        p = d_tmp_encoded.find("=")
        q = d_tmp_encoded[p + 1:]
        dict_tmp = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "votable",
            "tapclient": str(TAP_CLIENT_ID),
            "PHASE": "RUN",
            "QUERY": str(q)}
        sorted_key = taputils.taputil_create_sorted_dict_key(dict_tmp)
        job_request = "sync?" + sorted_key
        conn_handler.set_response(job_request, response_launch_job)
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

    @patch.object(TapPlus, 'login')
    def test_login(self, mock_login):
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        tap.login("user", "password")
        assert (mock_login.call_count == 2)
        mock_login.side_effect = HTTPError("Login error")
        tap.login("user", "password")
        assert (mock_login.call_count == 3)

    @patch.object(TapPlus, 'login_gui')
    @patch.object(TapPlus, 'login')
    def test_login_gui(self, mock_login_gui, mock_login):
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        tap.login_gui()
        assert (mock_login_gui.call_count == 1)
        mock_login_gui.side_effect = HTTPError("Login error")
        tap.login("user", "password")
        assert (mock_login.call_count == 1)

    @patch.object(TapPlus, 'logout')
    def test_logout(self, mock_logout):
        conn_handler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=conn_handler)
        tap = GaiaClass(conn_handler, tapplus)
        tap.logout()
        assert (mock_logout.call_count == 2)
        mock_logout.side_effect = HTTPError("Login error")
        tap.logout()
        assert (mock_logout.call_count == 3)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
