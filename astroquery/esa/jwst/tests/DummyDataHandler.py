# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
========================
eJWST Dummy Data Handler
========================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""


class DummyDataHandler:

    def __init__(self):
        self.base_url = "http://test/data?"
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
            raise ValueError(f"Method '+{str(method)} "
                             f"' not invoked. (Invoked method is '" +
                             f"{str(self.__invokedMethod)}')")

    def check_parameters(self, parameters, method_name):
        if parameters is None:
            return len(self.__parameters) == 0
        if len(parameters) != len(self.__parameters):
            raise ValueError(f"Wrong number of parameters for "
                             f"method '{method_name}'. "
                             f"Found: {len(self.__parameters)}. "
                             f"Expected {len(parameters)}")
        for key in parameters:
            if key in self.__parameters:
                # check value
                if self.__parameters[key] != parameters[key]:
                    raise ValueError(f"Wrong '{method_name}' parameter "
                                     f"value for method '{key}'. "
                                     f"Found: '{self.__parameters[key]}'. "
                                     f"Expected: '{parameters[key]}'")
            else:
                raise ValueError(f"Parameter '{str(key)}' not found for "
                                 f"method '{method_name}'")
        return False

    def download_file(self, url=None):
        self.__invokedMethod = 'download_file'
        self.__parameters['url'] = url
        return None
