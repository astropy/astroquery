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
from astroquery.utils.tap.core import TapPlus


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTap(unittest.TestCase):

    def test_load_tables(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(tap_plus_handler=dummyTapHandler, datalink_handler=dummyTapHandler)
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
        tap = GaiaClass(tap_plus_handler=dummyTapHandler, datalink_handler=dummyTapHandler)
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
        tap = GaiaClass(tap_plus_handler=dummyTapHandler, datalink_handler=dummyTapHandler)
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
        tap = GaiaClass(tap_plus_handler=dummyTapHandler, datalink_handler=dummyTapHandler)
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
        tap = GaiaClass(tap_plus_handler=dummyTapHandler, datalink_handler=dummyTapHandler)
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

    def test_query_object(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(tapplus, tapplus)
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
        assert "Missing required argument: 'width'" in err.value.args[0]

        width = Quantity(12, u.deg)

        with pytest.raises(ValueError) as err:
            tap.query_object(sc, width=width)
        assert "Missing required argument: 'height'" in err.value.args[0]

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
                                    np.object)
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
                                    np.object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_query_object_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(tapplus, tapplus)
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
                                    np.object)
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
                                    np.object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_cone_search_sync(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(tapplus, tapplus)
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
                                    np.object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    def test_cone_search_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus("http://test:1111/tap", connhandler=connHandler)
        tap = GaiaClass(tapplus, tapplus)
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

        params_dict = {}
        params_dict['VALID_DATA'] = "true"
        params_dict['ID'] = ids
        params_dict['FORMAT'] = str(format)
        params_dict['RETRIEVAL_TYPE'] = str(retrieval_type)

        tap.load_data(ids, retrieval_type, valid_data, band, format, verbose)
        parameters = {}
        parameters['params_dict'] = params_dict
        parameters['output_file'] = None
        parameters['verbose'] = verbose

        dummyHandler.check_call('load_data', parameters)
        tap.load_data(ids,
                      retrieval_type,
                      valid_data,
                      band,
                      format,
                      verbose)
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

    def test_upload_table_file(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        resource = "1535553556177O-result.vot"
        table_name = "table1"
        table_desc = "Description"
        format = "VOTable"
        verbose = True

        parameters = {}
        parameters['resource'] = resource
        parameters['table_name'] = table_name
        parameters['table_desc'] = table_desc
        parameters['format'] = format
        parameters['verbose'] = verbose
        tap.upload_table(upload_resource=resource,
                         table_name=table_name,
                         table_description=table_desc,
                         format=format, verbose=verbose)
        dummyHandler.check_call('update_table', parameters)

    def test_upload_table_url(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        resource = "http://foo.com/tests"
        table_name = "table2"
        table_desc = "Description"
        format = "VOTable"
        verbose = True

        parameters = {}
        parameters['resource'] = resource
        parameters['table_name'] = table_name
        parameters['table_desc'] = table_desc
        parameters['format'] = format
        parameters['verbose'] = verbose
        tap.upload_table(upload_resource=resource,
                         table_name=table_name,
                         table_description=table_desc,
                         format=format, verbose=verbose)
        dummyHandler.check_call('update_table', parameters)

    def test_upload_table_from_job(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        job = "1536044389256O"
        verbose = True
        table_name='table'
        table_description='desc'
        parameters = {}
        parameters['job'] = job
        parameters['table_name'] = table_name
        parameters['table_description'] = table_description
        parameters['verbose'] = verbose
        tap.upload_table_from_job(job=job, table_name=table_name, table_description=table_description, verbose=verbose)
        dummyHandler.check_call('upload_table_from_job', parameters)

    def test_delete_user_table(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        table_name = "table2"
        force_removal = False
        verbose = True

        parameters = {}
        parameters['table_name'] = table_name
        parameters['force_removal'] = force_removal
        parameters['verbose'] = verbose
        tap.delete_user_table(table_name, force_removal, verbose)
        dummyHandler.check_call('delete_user_table', parameters)

    def test_load_groups(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        verbose = True

        parameters = {}
        parameters['verbose'] = verbose

        tap.load_groups(verbose)
        dummyHandler.check_call('load_groups', parameters)

    def test_load_group(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        group_name = "group1"
        verbose = True

        parameters = {}
        parameters['group_name'] = group_name
        parameters['verbose'] = verbose

        tap.load_group(group_name, verbose)
        dummyHandler.check_call('load_group', parameters)

    def test_load_shared_items(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        verbose = True

        parameters = {}
        parameters['verbose'] = verbose

        tap.load_shared_items(verbose)
        dummyHandler.check_call('load_shared_items', parameters)

    def test_share_table(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        group_name = "group1"
        table_name = "table1"
        description = "description1"
        verbose = True

        parameters = {}
        parameters['group_name'] = group_name
        parameters['table_name'] = table_name
        parameters['description'] = description
        parameters['verbose'] = verbose

        tap.share_table(group_name, table_name, description, verbose)
        dummyHandler.check_call('share_table', parameters)

    def test_share_table_stop(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        table_name = "table1"
        group_name = "group1"
        verbose = True

        parameters = {}
        parameters['table_name'] = table_name
        parameters['group_name'] = group_name
        parameters['verbose'] = verbose

        tap.share_table_stop(group_name=group_name, table_name=table_name, 
                             verbose=verbose)
        dummyHandler.check_call('share_table_stop', parameters)

    def test_share_group_create(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        group_name = "group1"
        description = "description1"
        verbose = True

        parameters = {}
        parameters['group_name'] = group_name
        parameters['description'] = description
        parameters['verbose'] = verbose

        tap.share_group_create(group_name, description, verbose)
        dummyHandler.check_call('share_group_create', parameters)

    def test_share_group_delete(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        group_name = "group1"
        verbose = True

        parameters = {}
        parameters['group_name'] = group_name
        parameters['verbose'] = verbose

        tap.share_group_delete(group_name, verbose)
        dummyHandler.check_call('share_group_delete', parameters)

    def test_is_valid_user(self):
        dummyHandler = DummyTapHandler()
        tap = GaiaClass(dummyHandler, dummyHandler)

        user_id = "user1"
        verbose = True

        parameters = {}
        parameters['user_id'] = user_id
        parameters['verbose'] = verbose

        tap.is_valid_user(user_id, verbose)
        dummyHandler.check_call('is_valid_user', parameters)

    def test_xmatch(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler, dummyTapHandler)
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
        tap.cross_match(full_qualified_table_name_a='schemaA.tableA', full_qualified_table_name_b='schemaB.tableB', results_table_name='results')
        dummyTapHandler.check_call('launch_job_async', parameters)
        # test with parameters
        dummyTapHandler.reset()
        radius = 1.0
        verbose = True
        background = True
        query = "SELECT crossmatch_positional(\
            'schemaA','tableA',\
            'schemaB','tableB',\
            "+str(radius)+",\
            'results')\
            FROM dual;"
        parameters['query'] = query
        parameters['name'] = 'results'
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = False
        parameters['background'] = background
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.cross_match(full_qualified_table_name_a='schemaA.tableA', full_qualified_table_name_b='schemaB.tableB', \
                        results_table_name='results', background=background, verbose=verbose)
        dummyTapHandler.check_call('launch_job_async', parameters)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
