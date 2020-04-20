# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
JWST TAP plus
=============

@author: Raul Gutierrez-Sanchez
@contact: raul.gutierrez@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 24 oct. 2018


"""
import unittest
import os
import pytest
import shutil

from astroquery.jwst import JwstClass
from astroquery.jwst.tests.DummyTapHandler import DummyTapHandler
from astroquery.jwst.tests.DummyDataHandler import DummyDataHandler
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
import astropy.units as u
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.units import Quantity
import numpy as np
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap.core import TapPlus


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTap(unittest.TestCase):

    def test_load_tables(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['only_names'] = False
        parameters['include_shared_tables'] = False
        parameters['verbose'] = False
        tap.load_tables()
        dummyTapHandler.check_call('load_tables', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['only_names'] = True
        parameters['include_shared_tables'] = True
        parameters['verbose'] = True
        tap.load_tables(True, True, True)
        dummyTapHandler.check_call('load_tables', parameters)

    def test_load_table(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = False
        tap.load_table('table')
        dummyTapHandler.check_call('load_table', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = True
        tap.load_table('table', verbose=True)
        dummyTapHandler.check_call('load_table', parameters)

    def test_launch_sync_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(dummyTapHandler)
        query = "query"
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.launch_job(query)
        dummyTapHandler.check_call('launch_job', parameters)
        # test with parameters
        dummyTapHandler.reset()
        name = 'name'
        output_file = 'output'
        output_format = 'format'
        verbose = True
        dump_to_file = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        parameters['query'] = query
        parameters['name'] = name
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = dump_to_file
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        tap.launch_job(query,
                       name=name,
                       output_file=output_file,
                       output_format=output_format,
                       verbose=verbose,
                       dump_to_file=dump_to_file,
                       upload_resource=upload_resource,
                       upload_table_name=upload_table_name)
        dummyTapHandler.check_call('launch_job', parameters)

    def test_launch_async_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(dummyTapHandler)
        query = "query"
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['background'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.launch_job_async(query)
        dummyTapHandler.check_call('launch_job_async', parameters)
        # test with parameters
        dummyTapHandler.reset()
        name = 'name'
        output_file = 'output'
        output_format = 'format'
        verbose = True
        dump_to_file = True
        background = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        parameters['query'] = query
        parameters['name'] = name
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = dump_to_file
        parameters['background'] = background
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        tap.launch_job_async(query,
                             name=name,
                             output_file=output_file,
                             output_format=output_format,
                             verbose=verbose,
                             dump_to_file=dump_to_file,
                             background=background,
                             upload_resource=upload_resource,
                             upload_table_name=upload_table_name)
        dummyTapHandler.check_call('launch_job_async', parameters)

    def test_list_async_jobs(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['verbose'] = False
        tap.list_async_jobs()
        dummyTapHandler.check_call('list_async_jobs', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters['verbose'] = True
        tap.list_async_jobs(verbose=True)
        dummyTapHandler.check_call('list_async_jobs', parameters)

    def test_query_region(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tapplus)
        # Launch response: we use default response because the query contains decimals
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
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree), frame='icrs')
        with pytest.raises(ValueError) as err:
            tap.query_region(sc)
            print(err.value.args[0])
        assert "Missing required argument: 'width'" in err.value.args[0]

        width = Quantity(12, u.deg)
        height = Quantity(10, u.deg)

        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width)
        assert "Missing required argument: 'height'" in err.value.args[0]

        #Test observation_id argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, observation_id=1)
        assert "observation_id must be string" in err.value.args[0]

        #Test cal_level argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, cal_level='a')
        assert "cal_level must be either 'Top' or an integer" in err.value.args[0]

        #Test only_public
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, only_public='a')
        assert "only_public must be boolean" in err.value.args[0]

        #Test dataproduct_type argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, prod_type=1)
        assert "prod_type must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, prod_type='a')
        assert "prod_type must be one of: " in err.value.args[0]

        #Test instrument_name argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, instrument_name=1)
        assert "instrument_name must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, instrument_name='a')
        assert "instrument_name must be one of: " in err.value.args[0]

        #Test filter_name argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, filter_name=1)
        assert "filter_name must be string" in err.value.args[0]

        #Test proposal_id argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, proposal_id=123)
        assert "proposal_id must be string" in err.value.args[0]

        table = tap.query_region(sc, width=width, height=height)
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
                                    np.object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        # by radius
        radius = Quantity(1, u.deg)
        table = tap.query_region(sc, radius=radius)
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
                                    np.object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_query_region_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tapplus)
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
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree), frame='icrs')
        width = Quantity(12, u.deg)
        height = Quantity(10, u.deg)
        table = tap.query_region_async(sc, width=width, height=height)
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
                                    np.object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        # by radius
        radius = Quantity(1, u.deg)
        table = tap.query_region_async(sc, radius=radius)
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
                                    np.object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_cone_search_sync(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tapplus)
        # Launch response: we use default response because the query contains decimals
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
                                    np.object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

        #Test observation_id argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, observation_id=1)
        assert "observation_id must be string" in err.value.args[0]

        #Test cal_level argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, cal_level='a')
        assert "cal_level must be either 'Top' or an integer" in err.value.args[0]

        #Test only_public
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, only_public='a')
        assert "only_public must be boolean" in err.value.args[0]

        #Test dataproduct_type argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, prod_type=1)
        assert "prod_type must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, prod_type='a')
        assert "prod_type must be one of: " in err.value.args[0]

        #Test instrument_name argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, instrument_name=1)
        assert "instrument_name must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, instrument_name='a')
        assert "instrument_name must be one of: " in err.value.args[0]

        #Test filter_name argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, filter_name=1)
        assert "filter_name must be string" in err.value.args[0]

        #Test proposal_id argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, proposal_id=123)
        assert "proposal_id must be string" in err.value.args[0]


    def test_cone_search_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tapplus)
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
                                    np.object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_get_product_by_artifactid(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(dummyTapHandler, dummyTapHandler)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product();
        assert "Missing required argument: 'artifact_id' or 'file_name'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

        parameters = {}
        parameters['output_file'] = 'my_artifact_id'
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        param_dict['DATA_RETRIEVAL_ORIGIN'] = 'ASTROQUERY'
        param_dict['ARTIFACTID'] = 'my_artifact_id'
        parameters['params_dict'] = param_dict

        jwst.get_product(artifact_id='my_artifact_id');
        dummyTapHandler.check_call('load_data', parameters)

    def test_get_product_by_filename(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(dummyTapHandler, dummyTapHandler)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product();
        assert "Missing required argument: 'artifact_id' or 'file_name'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

        parameters = {}
        parameters['output_file'] = 'file_name_id'
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        param_dict['DATA_RETRIEVAL_ORIGIN'] = 'ASTROQUERY'
        param_dict['ARTIFACT_URI'] = 'mast:JWST/product/file_name_id'
        parameters['params_dict'] = param_dict

        jwst.get_product(file_name='file_name_id');
        dummyTapHandler.check_call('load_data', parameters)

    def test_get_products_list(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(dummyTapHandler, dummyTapHandler)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product_list()
        assert "Missing required argument: 'observation_id'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

        observation_id = "obsid"
        cal_level_condition = " AND m.calibrationlevel = m.max_cal_level"
        prodtype_condition = ""

        query = "SELECT a.*, m.calibrationlevel FROM " +\
                "jwst.artifact AS a, " +\
                "jwst.main AS m " + \
                "WHERE a.obsid = m.obsid AND " + \
                "a.obsid = '" + observation_id + "' " + \
                cal_level_condition + \
                prodtype_condition + \
                " ORDER BY a.producttype ASC"

        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None

        jwst.get_product_list(observation_id=observation_id)
        dummyTapHandler.check_call('launch_job', parameters)

        dummyTapHandler.reset()
        cal_level = 2
        cal_level_condition = " AND m.calibrationlevel = "+str(cal_level)+" "
        product_type = "science"
        prodtype_condition = " AND producttype ILIKE '"+product_type+"' "

        query = "SELECT a.*, m.calibrationlevel FROM " +\
                "jwst.artifact AS a, " +\
                "jwst.main AS m " + \
                "WHERE a.obsid = m.obsid AND " + \
                "a.obsid = '" + observation_id + "' " + \
                cal_level_condition + \
                prodtype_condition + \
                " ORDER BY a.producttype ASC"

        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None

        jwst.get_product_list(observation_id=observation_id, cal_level=cal_level, product_type=product_type)
        dummyTapHandler.check_call('launch_job', parameters)

    def test_get_obs_products(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(dummyTapHandler, dummyTapHandler)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_obs_products()
        assert "Missing required argument: 'observation_id'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_1"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print("Creation of the directory %s failed: %s" % (output_file_full_path_dir, err.strerror))
            raise err

        observation_id = 'obsid'

        parameters = {}
        parameters['verbose'] = False

        param_dict = {}
        param_dict['obsid'] = observation_id
        param_dict['RETRIEVAL_TYPE'] = 'OBSERVATION'
        param_dict['DATA_RETRIEVAL_ORIGIN'] = 'ASTROQUERY'
        parameters['params_dict'] = param_dict

        # Test single product tar
        file = data_path('single_product_retrieval.tar')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files=[]
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_1.fits'
        expected_files.append(extracted_file_1)

        try:
            files_returned = jwst.get_obs_products(observation_id=observation_id, output_file=output_file_full_path)
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files, files_returned=files_returned)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        # Test single file
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_2"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print("Creation of the directory %s failed: %s" % (output_file_full_path_dir, err.strerror))
            raise err

        file = data_path('single_product_retrieval_1.fits')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files=[]
        expected_files.append(output_file_full_path)

        try:
            files_returned = jwst.get_obs_products(observation_id=observation_id, output_file=output_file_full_path)
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files, files_returned=files_returned)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        # Test single file zip
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_3"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print("Creation of the directory %s failed: %s" % (output_file_full_path_dir, err.strerror))
            raise err

        file = data_path('single_product_retrieval_3.fits.zip')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files=[]
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval.fits'
        expected_files.append(extracted_file_1)

        try:
            files_returned = jwst.get_obs_products(observation_id=observation_id, output_file=output_file_full_path)
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files, files_returned=files_returned)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        # Test single file gzip
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_4"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print("Creation of the directory %s failed: %s" % (output_file_full_path_dir, err.strerror))
            raise err

        file = data_path('single_product_retrieval_2.fits.gz')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files=[]
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_2.fits.gz'
        expected_files.append(extracted_file_1)

        try:
            files_returned = jwst.get_obs_products(observation_id=observation_id, output_file=output_file_full_path)
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files, files_returned=files_returned)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        # Test tar with 3 files, a normal one, a gzip one and a zip one
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_5"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print("Creation of the directory %s failed: %s" % (output_file_full_path_dir, err.strerror))
            raise err

        file = data_path('three_products_retrieval.tar')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files=[]
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_1.fits'
        expected_files.append(extracted_file_1)
        extracted_file_2 = output_file_full_path_dir + os.sep + 'single_product_retrieval_2.fits.gz'
        expected_files.append(extracted_file_2)
        extracted_file_3 = output_file_full_path_dir + os.sep + 'single_product_retrieval_3.fits.zip'
        expected_files.append(extracted_file_3)

        try:
            files_returned = jwst.get_obs_products(observation_id=observation_id, output_file=output_file_full_path)
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files, files_returned=files_returned)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

    def test_gunzip_file(self):
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_gunzip"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print("Creation of the directory %s failed: %s" % (output_file_full_path_dir, err.strerror))
            raise err

        file = data_path('single_product_retrieval_2.fits.gz')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        expected_files=[]
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_2.fits'
        expected_files.append(extracted_file_1)

        try:
            extracted_file = JwstClass.gzip_uncompress_and_rename_single_file(output_file_full_path)
            if extracted_file != extracted_file_1:
                raise ValueError("Extracted file not fond: %s" % extracted_file_1)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

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

    def __remove_folder_contents(self, folder):
        for root, dirs, files in os.walk(folder):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    def __check_extracted_files(self, files_expected, files_returned):
        if len(files_expected) != len(files_returned):
            raise ValueError("Expected files size error. Found %i, expected %i" %
                             (len(files_returned), len(files_expected)))
        for f in files_expected:
            if not os.path.exists(f):
                raise ValueError("Not found extracted file: %s" % f)
            if not f in files_returned:
                raise ValueError("Not found expected file: %s" % f)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
