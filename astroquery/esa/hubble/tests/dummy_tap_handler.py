# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
======================
eHST Dummy Tap Handler
======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astroquery.utils.tap.model.taptable import TapTableMeta
from astroquery.utils.tap.model.job import Job


class DummyHubbleTapHandler:

    def __init__(self, method, parameters):
        self._invokedMethod = method
        self._parameters = parameters

    def reset(self):
        self._parameters = {}
        self._invokedMethod = None

    def check_call(self, method_name, parameters):
        self.check_method(method_name)
        self.check_parameters(parameters, method_name)

    def check_method(self, method):
        if method != self._invokedMethod:
            raise ValueError(f"Method '{method}' is not invoked. (Invoked method "
                             f"is '{self._invokedMethod}').")

    def check_parameters(self, parameters, method_name):
        if parameters is None:
            return len(self._parameters) == 0
        if len(parameters) != len(self._parameters):
            raise ValueError(f"Wrong number of parameters for method '{method_name}'. "
                             f"Found: {len(self._parameters)}. Expected {len(parameters)}")
        for key in parameters:
            if key in self._parameters:
                # check value
                if self._parameters[key] != parameters[key]:
                    raise ValueError(f"Wrong '{key}' parameter "
                                     f"value for method '{method_name}'. "
                                     f"Found:'{self._parameters[key]}'. Expected:'{parameters[key]}'")
            else:
                raise ValueError(f"Parameter '{key}' not found in method '{method_name}'")

    def launch_job(self, query, name=None, output_file=None,
                   output_format="votable", verbose=False, dump_to_file=False,
                   upload_resource=None, upload_table_name=None):
        self.__invokedMethod = 'launch_job'
        self._parameters['query'] = query
        self._parameters['name'] = name
        self._parameters['output_file'] = output_file
        self._parameters['output_format'] = output_format
        self._parameters['verbose'] = verbose
        self._parameters['dump_to_file'] = dump_to_file
        self._parameters['upload_resource'] = upload_resource
        self._parameters['upload_table_name'] = upload_table_name
        return Job(False)

    def load_tables(self,
                    only_names=True,
                    include_shared_tables=False,
                    verbose=True):
        table = TapTableMeta()
        table.name = "table"
        return [table]

    def load_data(self, params_dict, output_file=None, verbose=False):
        self.__invokedMethod = 'load_data'
        self._parameters['params_dict'] = params_dict
        self._parameters['output_file'] = output_file
        self._parameters['verbose'] = verbose
