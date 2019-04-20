# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc TAP plus
=============

"""

from astroquery.cadc.tests.DummyJob import DummyJob


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

    def load_tables(self, only_names=False, verbose=False):
        self.__invokedMethod = 'get_tables'
        self.__parameters['only_names'] = only_names
        self.__parameters['verbose'] = verbose
        return None

    def load_table(self, table, verbose=False):
        self.__invokedMethod = 'get_table'
        self.__parameters['table'] = table
        self.__parameters['verbose'] = verbose
        return None

    def launch_job(self, query, name=None, output_file=None,
                   output_format="votable", verbose=False, dump_to_file=False,
                   upload_resource=None, upload_table_name=None):
        self.__invokedMethod = 'run_query'
        self.__parameters['query'] = query
        self.__parameters['name'] = name
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['dump_to_file'] = dump_to_file
        self.__parameters['upload_resource'] = upload_resource
        self.__parameters['upload_table_name'] = upload_table_name

        job = DummyJob()
        job.set_parameter('query', query)
        job.set_parameter('format', output_format)

        return job

    def load_async_job(self, jobid=None, verbose=False):
        self.__invokedMethod = 'load_async_job'
        self.__parameters['jobid'] = jobid
        self.__parameters['verbose'] = verbose
        return None

    def list_async_jobs(self, verbose=False):
        self.__invokedMethod = 'list_async_jobs'
        self.__parameters['verbose'] = verbose
        return [DummyJob()]

    def save_results(self, job, filename, verbose=False):
        self.__invokedMethod = 'save_results'
        self.__parameters['job'] = job
        self.__parameters['filename'] = filename
        self.__parameters['verbose'] = verbose
        return None

    def login(self, user, password, certificate_file, cookie_prefix=None,
              login_url=None, verbose=False):
        self.__invokedMethod = 'login'
        self.__parameters['user'] = user
        self.__parameters['password'] = password
        self.__parameters['certificate_file'] = certificate_file
        self.__parameters['cookie_prefix'] = cookie_prefix
        self.__parameters['login_url'] = login_url
        self.__parameters['verbose'] = verbose
        return None

    def logout(self, verbose=False):
        self.__invokedMethod = 'logout'
        self.__parameters['verbose'] = verbose
        return None

    def _TapPlus__getconnhandler(self):
        return self
