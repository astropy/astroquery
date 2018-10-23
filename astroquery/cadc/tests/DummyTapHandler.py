# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc TAP plus
=============

"""


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
            raise Exception("Method '"+str(method)
                            + "' not invoked. (Invoked method is '"
                            + str(self.__invokedMethod)+"')")

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
                    Found: '%s'. Expected: '%s'",  (
                        method_name,
                        key,
                        self.__parameters[key],
                        parameters[key]))
            else:
                raise Exception("Parameter '%s' not found for method '%s'",
                                (str(key), method_name))
        return False

    def get_tables(self, only_names=False, verbose=False, authentication=None):
        self.__invokedMethod = 'get_tables'
        self.__parameters['only_names'] = only_names
        self.__parameters['verbose'] = verbose
        self.__parameters['authentication'] = authentication
        return None

    def get_table(self, table, verbose=False, authentication=None):
        self.__invokedMethod = 'get_table'
        self.__parameters['table'] = table
        self.__parameters['verbose'] = verbose
        self.__parameters['authentication'] = authentication
        return None

    def run_query(self, query, operation, output_file=None, background=False,
                  output_format="votable", verbose=False, save_to_file=False,
                  upload_resource=None, upload_table_name=None,
                  authentication=None):
        self.__invokedMethod = 'run_query'
        self.__parameters['query'] = query
        self.__parameters['operation'] = operation
        self.__parameters['output_file'] = output_file
        self.__parameters['output_format'] = output_format
        self.__parameters['verbose'] = verbose
        self.__parameters['background'] = background
        self.__parameters['save_to_file'] = save_to_file
        self.__parameters['upload_resource'] = upload_resource
        self.__parameters['upload_table_name'] = upload_table_name
        self.__parameters['authentication'] = authentication
        return None

    def load_async_job(self, jobid=None, verbose=False, authentication=None):
        self.__invokedMethod = 'load_async_job'
        self.__parameters['jobid'] = jobid
        self.__parameters['verbose'] = verbose
        self.__parameters['authentication'] = authentication
        return None

    def list_async_jobs(self, verbose=False, authentication=None):
        self.__invokedMethod = 'list_async_jobs'
        self.__parameters['verbose'] = verbose
        self.__parameters['authentication'] = authentication
        return None

    def save_results(self, job, verbose=False, authentication=None):
        self.__invokedMethod = 'save_results'
        self.__parameters['job'] = job
        self.__parameters['verbose'] = verbose
        self.__parameters['authentication'] = authentication
        return None
