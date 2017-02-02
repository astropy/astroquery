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
from astroquery.gaia.core import GaiaClass
from astroquery.gaia.tests.DummyTapHandler import DummyTapHandler


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class TestTap(unittest.TestCase):

    def test_load_tables(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        #default parameters
        parameters = {}
        parameters['only_names'] = False
        parameters['include_shared_tables'] = False
        parameters['verbose'] = False
        tap.load_tables()
        dummyTapHandler.check_call('load_tables', parameters)
        #test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['only_names'] = True
        parameters['include_shared_tables'] = True
        parameters['verbose'] = True
        tap.load_tables(True, True, True)
        dummyTapHandler.check_call('load_tables', parameters)
        pass
    
    def test_load_table(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        #default parameters
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = False
        tap.load_table('table')
        dummyTapHandler.check_call('load_table', parameters)
        #test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = True
        tap.load_table('table', verbose=True)
        dummyTapHandler.check_call('load_table', parameters)
        pass
    
    def test_launch_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        query = "query"
        #default parameters
        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['async'] = False
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['background'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.launch_job(query)
        dummyTapHandler.check_call('launch_job', parameters)
        #test with parameters
        dummyTapHandler.reset()
        name = 'name'
        async = True
        output_file = 'output'
        output_format = 'format'
        verbose = True
        dump_to_file = True
        background = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        parameters['query'] = query
        parameters['name'] = name
        parameters['async'] = async
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = dump_to_file
        parameters['background'] = background
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        tap.launch_job(query, 
                       name=name, 
                       async=async, 
                       output_file=output_file, 
                       output_format=output_format, 
                       verbose=verbose, 
                       dump_to_file=dump_to_file, 
                       background=background, 
                       upload_resource=upload_resource, 
                       upload_table_name=upload_table_name)
        dummyTapHandler.check_call('launch_job', parameters)
        pass
    
    def test_launch_async_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        query = "query"
        #default parameters
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
        tap.launch_async_job(query)
        dummyTapHandler.check_call('launch_async_job', parameters)
        #test with parameters
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
        tap.launch_async_job(query, 
                             name=name, 
                             output_file=output_file, 
                             output_format=output_format, 
                             verbose=verbose, 
                             dump_to_file=dump_to_file, 
                             background=background, 
                             upload_resource=upload_resource, 
                             upload_table_name=upload_table_name)
        dummyTapHandler.check_call('launch_async_job', parameters)
        pass
    
    def test_launch_sync_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        query = "query"
        #default parameters
        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.launch_sync_job(query)
        dummyTapHandler.check_call('launch_sync_job', parameters)
        #test with parameters
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
        tap.launch_sync_job(query, 
                            name=name, 
                            output_file=output_file, 
                            output_format=output_format, 
                            verbose=verbose, 
                            dump_to_file=dump_to_file, 
                            upload_resource=upload_resource, 
                            upload_table_name=upload_table_name)
        dummyTapHandler.check_call('launch_sync_job', parameters)
        pass
    
    def test_list_async_jobs(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        #default parameters
        parameters = {}
        parameters['verbose'] = False
        tap.list_async_jobs()
        dummyTapHandler.check_call('list_async_jobs', parameters)
        #test with parameters
        dummyTapHandler.reset()
        parameters['verbose'] = True
        tap.list_async_jobs(verbose=True)
        dummyTapHandler.check_call('list_async_jobs', parameters)
        pass
    
    def test_query_object(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        sc = 'coord'
        #default parameters
        parameters = {}
        parameters['coordinate'] = sc
        parameters['radius'] = None
        parameters['width'] = None
        parameters['height'] = None
        parameters['async'] = False
        parameters['verbose'] = False
        tap.query_object(sc)
        dummyTapHandler.check_call('query_object', parameters)
        #test with parameters
        dummyTapHandler.reset()
        width = 'w'
        height = 'h'
        radius = 'r'
        async = True
        verbose = True
        parameters['coordinate'] = sc
        parameters['radius'] = radius
        parameters['width'] = width
        parameters['height'] = height
        parameters['async'] = async
        parameters['verbose'] = verbose
        tap.query_object(sc, 
                         radius=radius, 
                         width=width, 
                         height=height, 
                         async=async, 
                         verbose=verbose)
        dummyTapHandler.check_call('query_object', parameters)
        pass
    
    def test_query_object_async(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        sc = 'coord'
        #default parameters
        parameters = {}
        parameters['coordinate'] = sc
        parameters['radius'] = None
        parameters['width'] = None
        parameters['height'] = None
        parameters['verbose'] = False
        tap.query_object_async(sc)
        dummyTapHandler.check_call('query_object_async', parameters)
        #test with parameters
        dummyTapHandler.reset()
        width = 'w'
        height = 'h'
        radius = 'r'
        verbose = True
        parameters['coordinate'] = sc
        parameters['radius'] = radius
        parameters['width'] = width
        parameters['height'] = height
        parameters['verbose'] = verbose
        tap.query_object_async(sc, 
                               radius=radius, 
                               width=width, 
                               height=height, 
                               verbose=verbose)
        dummyTapHandler.check_call('query_object_async', parameters)
        pass
    
    def test_cone_search_sync(self):
        dummyTapHandler = DummyTapHandler()
        tap = GaiaClass(dummyTapHandler)
        #default parameters
        coordinate = 'coord'
        radius = 'r'
        parameters = {}
        parameters['coordinate'] = coordinate
        parameters['radius'] = radius
        parameters['async'] = False
        parameters['background'] = False
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        tap.cone_search(coordinate, radius)
        dummyTapHandler.check_call('cone_search', parameters)
        #test with parameters
        dummyTapHandler.reset()
        async = True
        background = True
        output_file = 'output'
        output_format = 'format'
        verbose = True
        dump_to_file = True
        parameters['coordinate'] = coordinate
        parameters['radius'] = radius
        parameters['async'] = async
        parameters['background'] = background
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = dump_to_file
        tap.cone_search(coordinate, 
                        radius, 
                        async=async, 
                        background=background, 
                        output_file=output_file, 
                        output_format=output_format, 
                        verbose=verbose, 
                        dump_to_file=dump_to_file)
        dummyTapHandler.check_call('cone_search', parameters)
        pass
    
    pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()