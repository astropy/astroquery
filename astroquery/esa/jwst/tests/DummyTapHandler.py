# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=======================
eJWST Dummy Tap Handler
=======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
from astropy.table import Table
import numpy as np

from astroquery.utils.tap.model.job import Job


class DummyTapHandler:

    def __init__(self):
        self.__invokedMethod = None
        self.__parameters = {}
        self.__dummy_results = {"filename": ["dummy_filename"],
                                "artifactid": ["dummy_artifact"],
                                "observationid": Table({'obs': np.arange(1)})}
        self.__job = Job(async_job=False)
        self.__job.set_results(self.__dummy_results)

    def reset(self):
        self.__parameters = {}
        self.__invokedMethod = None
        self.__dummy_results = {"filename": ["dummy_filename"],
                                "artifactid": ["dummy_artifact"],
                                "observationid": Table({'a': np.arange(1)})}
        self.__job = Job(async_job=False)
        self.__job.set_results(self.__dummy_results)

    def set_job(self, job):
        self.__job = job

    def get_job(self):
        return self.__job

    def check_call(self, method_name, parameters):
        self.check_method(method_name)
        self.check_parameters(parameters, method_name)

    def check_method(self, method):
        if method == self.__invokedMethod:
            return
        else:
            raise ValueError(f"Method '+{str(method)}' not invoked. (Invoked method is '{str(self.__invokedMethod)}')")

    def check_parameters(self, parameters, method_name):
        print("FOUND")
        print(self.__parameters)
        print("EXPECTED")
        print(parameters)
        if parameters is None:
            return len(self.__parameters) == 0
        if len(parameters) != len(self.__parameters):
            raise ValueError(f"Wrong number of parameters "
                             f"for method '{method_name}'"
                             f" Found: {len(self.__parameters)}. "
                             f"Expected {len(parameters)}")
        for key in parameters:
            if key in self.__parameters:
                # check value
                if self.__parameters[key] != parameters[key]:
                    raise ValueError(f"Wrong {key} parameter value for "
                                     f" method '{method_name}'. "
                                     f"Found: {self.__parameters[key]}. "
                                     f"Expected: {parameters[key]}")
            else:
                raise ValueError(f"Parameter '{str(key)}' not found "
                                 f"for method '{method_name}'")

    def load_tables(self, only_names=False, include_shared_tables=False,
                    verbose=False):
        self.__invokedMethod = 'load_tables'
        self.__parameters['only_names'] = only_names
        self.__parameters['include_shared_tables'] = include_shared_tables
        self.__parameters['verbose'] = verbose
        return None

    def load_table(self, table, verbose=False):
        self.__invokedMethod = 'load_table'
        self.__parameters['table'] = table
        self.__parameters['verbose'] = verbose
        return None

    def launch_job(self, query, name=None, output_file=None,
                   output_format="votable", verbose=False, dump_to_file=False,
                   upload_resource=None, upload_table_name=None):
        self.__invokedMethod = 'launch_job'
        self.__parameters['query'] = query
        self.__parameters['name'] = name
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        self.__parameters['upload_resource'] = upload_resource
        self.__parameters['upload_table_name'] = upload_table_name
        return self.__job

    def launch_job_async(self, query, name=None, output_file=None,
                         output_format="votable", verbose=False,
                         dump_to_file=False, background=False,
                         upload_resource=None, upload_table_name=None):
        self.__invokedMethod = 'launch_job_async'
        self.__parameters['query'] = query
        self.__parameters['name'] = name
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        self.__parameters['background'] = background
        self.__parameters['upload_resource'] = upload_resource
        self.__parameters['upload_table_name'] = upload_table_name
        return self.__job

    def load_async_job(self, jobid=None, name=None, verbose=False):
        self.__invokedMethod = 'load_async_job'
        self.__parameters['jobid'] = jobid
        self.__parameters['name'] = name
        self.__parameters['verbose'] = verbose
        return None

    def search_async_jobs(self, jobfilter=None, verbose=False):
        self.__invokedMethod = 'search_async_jobs'
        self.__parameters['jobfilter'] = jobfilter
        self.__parameters['verbose'] = verbose
        return None

    def list_async_jobs(self, verbose=False):
        self.__invokedMethod = 'list_async_jobs'
        self.__parameters['verbose'] = verbose
        return None

    def query_object(self, coordinate, radius=None, width=None, height=None,
                     verbose=False):
        self.__invokedMethod = 'query_object'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width
        self.__parameters['height'] = height
        self.__parameters['verbose'] = verbose
        return None

    def query_object_async(self, coordinate, radius=None, width=None,
                           height=None, verbose=False):
        self.__invokedMethod = 'query_object_async'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width
        self.__parameters['height'] = height
        self.__parameters['verbose'] = verbose
        return None

    def query_region(self, coordinate, radius=None, width=None):
        self.__invokedMethod = 'query_region'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width
        return None

    def query_region_async(self, coordinate, radius=None, width=None):
        self.__invokedMethod = 'query_region_async'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width
        return None

    def get_images(self, coordinate):
        self.__invokedMethod = 'get_images'
        self.__parameters['coordinate'] = coordinate
        return None

    def get_images_async(self, coordinate):
        self.__invokedMethod = 'get_images_sync'
        self.__parameters['coordinate'] = coordinate
        return None

    def cone_search(self, coordinate, radius, output_file=None,
                    output_format="votable", verbose=False,
                    dump_to_file=False):
        self.__invokedMethod = 'cone_search'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        return None

    def cone_search_async(self, coordinate, radius, background=False,
                          output_file=None, output_format="votable",
                          verbose=False, dump_to_file=False):
        self.__invokedMethod = 'cone_search_async'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['background'] = background
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        return None

    def remove_jobs(self, jobs_list, verbose=False):
        self.__invokedMethod = 'remove_jobs'
        self.__parameters['jobs_list'] = jobs_list
        self.__parameters['verbose'] = verbose
        return None

    def save_results(self, job, verbose=False):
        self.__invokedMethod = 'save_results'
        self.__parameters['job'] = job
        self.__parameters['verbose'] = verbose
        return None

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
        self.__invokedMethod = 'login'
        self.__parameters['user'] = user
        self.__parameters['password'] = password
        self.__parameters['credentials_file'] = credentials_file
        self.__parameters['verbose'] = verbose
        return None

    def login_gui(self, verbose=False):
        self.__invokedMethod = 'login_gui'
        self.__parameters['verbose'] = verbose
        return None

    def logout(self, verbose=False):
        self.__invokedMethod = 'logout'
        self.__parameters['verbose'] = verbose
        return None

    def load_data(self, params_dict, output_file=None, verbose=False):
        self.__invokedMethod = 'load_data'
        self.__parameters['params_dict'] = params_dict
        self.__parameters['output_file'] = output_file
        self.__parameters['verbose'] = verbose

    def set_job_results(self, results):
        self.__dummy_results = results
        self.__job.set_results(self.__dummy_results)
