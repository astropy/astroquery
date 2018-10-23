# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc TAP plus
=============

"""
import unittest
import os
import pytest

from astroquery.cadc.core import CadcTAP
from astroquery.cadc import auth 
from astroquery.cadc.tests.DummyTapHandler import DummyTapHandler
from astroquery.cadc.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.cadc.tap.conn.tests.DummyResponse import DummyResponse
import astropy.units as u
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.units import Quantity
import numpy as np
from astroquery.cadc.tap.xmlparser import utils
from astroquery.cadc.tap.core import TapPlus


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTap(unittest.TestCase):

    def test_get_tables(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['only_names'] = False
        parameters['verbose'] = False
        parameters['authentication'] = anon
        tap.get_tables(authentication=anon)
        dummyTapHandler.check_call('get_tables', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['only_names'] = True
        parameters['verbose'] = True
        parameters['authentication'] = cert
        tap.get_tables(True, True, cert)
        dummyTapHandler.check_call('get_tables', parameters)

    def test_get_table(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = False
        parameters['authentication'] = anon
        tap.get_table('table', authentication=anon)
        dummyTapHandler.check_call('get_table', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = True
        parameters['authentication'] = cert
        tap.get_table('table', verbose=True, authentication=cert)
        dummyTapHandler.check_call('get_table', parameters)

    def test_run_query_sync(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        query = "query"
        operation = 'sync'
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['operation'] = operation
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['background'] = False
        parameters['save_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        parameters['authentication'] = anon
        tap.run_query(query, operation, authentication=anon)
        dummyTapHandler.check_call('run_query', parameters)
        # test with parameters
        dummyTapHandler.reset()
        output_file = 'output'
        output_format = 'format'
        verbose = True
        background = True
        save_to_file = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        authentication = cert
        parameters['query'] = query
        parameters['operation'] = operation
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['background'] = background
        parameters['save_to_file'] = save_to_file
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        parameters['authentication'] = authentication
        tap.run_query(query,
                      operation,
                      output_file=output_file,
                      output_format=output_format,
                      verbose=verbose,
                      background=background,
                      save_to_file=save_to_file,
                      upload_resource=upload_resource,
                      upload_table_name=upload_table_name,
                      authentication=authentication)
        dummyTapHandler.check_call('run_query', parameters)

    def test_run_query_async(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        query = "query"
        operation = 'async'
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['operation'] = operation
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['save_to_file'] = False
        parameters['background'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        parameters['authentication'] = anon
        tap.run_query(query, operation, authentication=anon)
        dummyTapHandler.check_call('run_query', parameters)
        # test with parameters
        dummyTapHandler.reset()
        output_file = 'output'
        output_format = 'format'
        verbose = True
        save_to_file = True
        background = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        authentication = cert
        parameters['query'] = query
        parameters['operation'] = operation
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['save_to_file'] = save_to_file
        parameters['background'] = background
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        parameters['authentication'] = authentication
        tap.run_query(query,
                      operation,
                      output_file=output_file,
                      output_format=output_format,
                      verbose=verbose,
                      save_to_file=save_to_file,
                      background=background,
                      upload_resource=upload_resource,
                      upload_table_name=upload_table_name,
                      authentication=authentication)
        dummyTapHandler.check_call('run_query', parameters)

    def test_load_async_job(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        jobid = '123'
        # default parameters
        parameters = {}
        parameters['jobid'] = jobid
        parameters['verbose'] = False
        parameters['authentication'] = anon
        tap.load_async_job(jobid, authentication=anon)
        dummyTapHandler.check_call('load_async_job', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters['jobid'] = jobid
        parameters['verbose'] = True
        parameters['authentication'] = cert
        tap.load_async_job(jobid, verbose=True, authentication=cert)
        dummyTapHandler.check_call('load_async_job', parameters)

    def test_list_async_jobs(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['verbose'] = False
        parameters['authentication'] = anon
        tap.list_async_jobs(authentication=anon)
        dummyTapHandler.check_call('list_async_jobs', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters['verbose'] = True
        parameters['authentication'] = cert
        tap.list_async_jobs(verbose=True, authentication=cert)
        dummyTapHandler.check_call('list_async_jobs', parameters)

    def test_save_results(self):
        anon=auth.AnonAuthMethod()
        cert=auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        dummyTapHandler = DummyTapHandler()
        tap = CadcTAP(tap_plus_handler=dummyTapHandler)
        job = '123'
        # default parameters
        parameters = {}
        parameters['job'] = job
        parameters['verbose'] = False
        parameters['authentication'] = anon
        tap.save_results(job, authentication=anon)
        dummyTapHandler.check_call('save_results', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters['job'] = job
        parameters['verbose'] = True
        parameters['authentication'] = cert
        tap.save_results(job, verbose=True, authentication=cert)
        dummyTapHandler.check_call('save_results', parameters)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
