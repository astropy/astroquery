# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
Euclid TAP plus
===============
European Space Astronomy Centre (ESAC)
European Space Agency (ESA)
"""
from astroquery.utils.tap.model.job import Job

CONTENT_TYPE_POST_DEFAULT = "application/x-www-form-urlencoded"


class DummyTapHandler(object):

    def __init__(self):
        self.__invokedMethod = None
        self.__parameters = {}
        self.__job = Job(async_job=False)

    def reset(self):
        self.__parameters = {}
        self.__invokedMethod = None
        self.__job = Job(async_job=False)

    def check_call(self, method_name, parameters):
        self.check_method(method_name)
        self.check_parameters(parameters, method_name)

    def check_method(self, method):
        if method == self.__invokedMethod:
            return
        else:
            raise Exception("Method '" + str(method)
                            + "' not invoked. (Invoked method is '"
                            + str(self.__invokedMethod) + "')")

    def check_parameters(self, parameters, method_name):
        if parameters is None:
            return len(self.__parameters) == 0
        if len(parameters) != len(self.__parameters):
            raise Exception("Wrong number of parameters for method '%s'. \
            Found: %d. Expected %d",
                            (method_name,
                             len(self.__parameters),
                             len(parameters)))
        for key in parameters:
            if key in self.__parameters:
                # check value
                if self.__parameters[key] != parameters[key]:
                    raise Exception("Wrong '%s' parameter value for method '%s'. \
                    Found: '%s'. Expected: '%s'", (
                        method_name,
                        key,
                        self.__parameters[key],
                        parameters[key]))
            else:
                raise Exception("Parameter '%s' not found for method '%s'",
                                (str(key), method_name))
        return False

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

    def launch_job_data_context(self, query, name=None, output_file=None,
                                output_format="votable", verbose=False, dump_to_file=False,
                                upload_resource=None, upload_table_name=None):
        self.__invokedMethod = 'launch_job_data_context'
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
                    output_format="votable", verbose=False, dump_to_file=False):
        self.__invokedMethod = 'cone_search'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        return None

    def cone_search_async(self, coordinate, radius, background=False,
                          output_file=None, output_format="votable", verbose=False,
                          dump_to_file=False):
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

    def get_product_list(self, id=None,
                         schema="sedm_pvpr01",
                         product_type=None):
        self.__invokedMethod = 'get_product_list'
        self.__parameters['id'] = id
        self.__parameters['schema'] = schema
        self.__parameters['product_type'] = product_type
        return self.__job.get_results()

    def get_obs_products(self, id=None,
                         schema="sedm_pvpr01",
                         product_type=None,
                         product_subtype="STK",
                         filter="ALL",
                         output_file=None):
        self.__invokedMethod = 'get_obs_products'
        self.__parameters['id'] = id
        self.__parameters['schema'] = schema
        self.__parameters['product_type'] = product_type
        self.__parameters['product_subtype'] = product_subtype
        self.__parameters['filter'] = filter
        self.__parameters['output_file'] = output_file
        return output_file

    def get_product(self, file_name=None,
                    product_id=None,
                    schema='sedm_pvpr01',
                    output_file=None):
        self.__invokedMethod = 'get_product'
        self.__parameters['file_name'] = file_name
        self.__parameters['product_id'] = product_id
        self.__parameters['schema'] = schema
        self.__parameters['output_file'] = output_file
        return output_file

    def get_cutout(self, coordinate, file_path=None,
                   instrument=None,
                   id=None,
                   radius=None,
                   output_file=None):
        self.__invokedMethod = 'get_cutout'
        self.__parameters['file_path'] = file_path
        self.__parameters['instrument'] = instrument
        self.__parameters['id'] = id
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['output_file'] = output_file
        return output_file

    def get_spectrum(self, source_id=None,
                     schema='sedm_pvpr01',
                     output_file=None):
        self.__invokedMethod = 'get_spectrum'
        self.__parameters['source_id'] = source_id
        self.__parameters['schema'] = schema
        self.__parameters['output_file'] = output_file
        return output_file
