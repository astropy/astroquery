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
from six.moves.urllib.parse import urlencode

CONTENT_TYPE_POST_DEFAULT = "application/x-www-form-urlencoded"


class DummyTapHandler(object):

    def __init__(self):
        self.__invokedMethod = None
        self.__parameters = {}

    def reset(self):
        self.__parameters = {}
        self.__invokedMethod = None

    def check_call(self, method_name, parameters):
        self.check_method(method_name)
        self.check_parameters(parameters, method_name)

    def execute_upload(self, data,
                       content_type=CONTENT_TYPE_POST_DEFAULT,
                       verbose=False):
        pass

    def check_method(self, method):
        if method == self.__invokedMethod:
            return
        else:
            raise Exception("Method '"+str(method) +
                            "' not invoked. (Invoked method is '" +
                            str(self.__invokedMethod)+"')")

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

    def load_table(self, table, verbose=False):
        self.__invokedMethod = 'load_table'
        self.__parameters['table'] = table
        self.__parameters['verbose'] = verbose

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

    def search_async_jobs(self, jobfilter=None, verbose=False):
        self.__invokedMethod = 'search_async_jobs'
        self.__parameters['jobfilter'] = jobfilter
        self.__parameters['verbose'] = verbose

    def list_async_jobs(self, verbose=False):
        self.__invokedMethod = 'list_async_jobs'
        self.__parameters['verbose'] = verbose

    def query_object(self, coordinate, radius=None, width=None, height=None,
                     verbose=False):
        self.__invokedMethod = 'query_object'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width
        self.__parameters['height'] = height
        self.__parameters['verbose'] = verbose

    def query_object_async(self, coordinate, radius=None, width=None,
                           height=None, verbose=False):
        self.__invokedMethod = 'query_object_async'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width
        self.__parameters['height'] = height
        self.__parameters['verbose'] = verbose

    def query_region(self, coordinate, radius=None, width=None):
        self.__invokedMethod = 'query_region'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width

    def query_region_async(self, coordinate, radius=None, width=None):
        self.__invokedMethod = 'query_region_async'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['width'] = width

    def get_images(self, coordinate):
        self.__invokedMethod = 'get_images'
        self.__parameters['coordinate'] = coordinate

    def get_images_async(self, coordinate):
        self.__invokedMethod = 'get_images_sync'
        self.__parameters['coordinate'] = coordinate

    def cone_search(self, coordinate, radius, output_file=None,
                    output_format="votable", verbose=False,
                    dump_to_file=False, columns=[]):
        self.__invokedMethod = 'cone_search'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        self.__parameters['columns'] = columns

    def cone_search_async(self, coordinate, radius, background=False,
                          output_file=None, output_format="votable",
                          verbose=False, dump_to_file=False, columns=[]):
        self.__invokedMethod = 'cone_search_async'
        self.__parameters['coordinate'] = coordinate
        self.__parameters['radius'] = radius
        self.__parameters['background'] = background
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        self.__parameters['columns'] = columns

    def remove_jobs(self, jobs_list, verbose=False):
        self.__invokedMethod = 'remove_jobs'
        self.__parameters['jobs_list'] = jobs_list
        self.__parameters['verbose'] = verbose

    def save_results(self, job, verbose=False):
        self.__invokedMethod = 'save_results'
        self.__parameters['job'] = job
        self.__parameters['verbose'] = verbose

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
        self.__invokedMethod = 'login'
        self.__parameters['user'] = verbose
        self.__parameters['password'] = verbose
        self.__parameters['credentials_file'] = verbose
        self.__parameters['verbose'] = verbose

    def login_gui(self, verbose=False):
        self.__invokedMethod = 'login_gui'
        self.__parameters['verbose'] = verbose

    def logout(self, verbose=False):
        self.__invokedMethod = 'logout'
        self.__parameters['verbose'] = verbose

    def load_data(self, params_dict, output_file=None, verbose=False):
        self.__invokedMethod = 'load_data'
        self.__parameters['params_dict'] = params_dict
        self.__parameters['output_file'] = output_file
        self.__parameters['verbose'] = verbose

    def get_datalinks(self, ids, verbose=False):
        self.__invokedMethod = 'get_datalinks'
        self.__parameters['ids'] = ids
        self.__parameters['verbose'] = verbose

    def upload_table(self, upload_resource=None, table_name=None,
                     table_description=None,
                     format=None, verbose=False):
        self.__invokedMethod = 'update_table'
        self.__parameters['resource'] = upload_resource
        self.__parameters['table_name'] = table_name
        self.__parameters['table_desc'] = table_description
        self.__parameters['format'] = format
        self.__parameters['verbose'] = verbose

    def upload_table_from_job(self, job=None, table_name=None,
                              table_description=None, verbose=False):
        self.__invokedMethod = 'upload_table_from_job'
        self.__parameters['job'] = job
        self.__parameters['table_name'] = table_name
        self.__parameters['table_description'] = table_description
        self.__parameters['verbose'] = verbose

    def delete_user_table(self, table_name=None, force_removal=False,
                          verbose=False):
        self.__invokedMethod = 'delete_user_table'
        self.__parameters['table_name'] = table_name
        self.__parameters['force_removal'] = force_removal
        self.__parameters['verbose'] = verbose

    def load_groups(self, verbose=False):
        self.__invokedMethod = 'load_groups'
        self.__parameters['verbose'] = verbose

    def load_group(self, group_name=None, verbose=False):
        self.__invokedMethod = 'load_group'
        self.__parameters['group_name'] = group_name
        self.__parameters['verbose'] = verbose

    def load_shared_items(self, verbose=False):
        self.__invokedMethod = 'load_shared_items'
        self.__parameters['verbose'] = verbose

    def share_table(self, group_name=None,
                    table_name=None,
                    description=None,
                    verbose=False):
        self.__invokedMethod = 'share_table'
        self.__parameters['group_name'] = group_name
        self.__parameters['table_name'] = table_name
        self.__parameters['description'] = description
        self.__parameters['verbose'] = verbose

    def share_table_stop(self,
                         group_name=None,
                         table_name=None,
                         verbose=False):
        self.__invokedMethod = 'share_table_stop'
        self.__parameters['table_name'] = table_name
        self.__parameters['group_name'] = group_name
        self.__parameters['verbose'] = verbose

    def share_group_create(self,
                           group_name=None,
                           description=None,
                           verbose=False):
        self.__invokedMethod = 'share_group_create'
        self.__parameters['group_name'] = group_name
        self.__parameters['description'] = description
        self.__parameters['verbose'] = verbose

    def share_group_delete(self,
                           group_name=None,
                           verbose=False):
        self.__invokedMethod = 'share_group_delete'
        self.__parameters['group_name'] = group_name
        self.__parameters['verbose'] = verbose

    def share_group_add_user(self,
                             group_name=None,
                             user_id=None,
                             verbose=False):
        self.__invokedMethod = 'share_group_add_user'
        self.__parameters['group_name'] = group_name
        self.__parameters['user_id'] = user_id
        self.__parameters['verbose'] = verbose

    def share_group_delete_user(self,
                                group_name=None,
                                user_id=None,
                                verbose=False):
        self.__invokedMethod = 'share_group_delete_user'
        self.__parameters['group_name'] = group_name
        self.__parameters['user_id'] = user_id
        self.__parameters['verbose'] = verbose

    def is_valid_user(self, user_id=None, verbose=False):
        self.__invokedMethod = 'is_valid_user'
        self.__parameters['user_id'] = user_id
        self.__parameters['verbose'] = verbose

    def url_encode(self, data):
        return urlencode(data)
