"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 4 Sept. 2019
"""


__all__ = ['DummyHandler']


class DummyHandler:

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
        if method == self._invokedMethod:
            return
        else:
            raise ValueError("Method '{}' is not invoked. (Invoked method \
                             is '{}'.)").format(method, self._invokedMethod)

    def check_parameters(self, parameters, method_name):
        if parameters is None:
            return len(self._parameters) == 0
        if len(parameters) != len(self._parameters):
            raise ValueError("Wrong number of parameters for method '{}'. \
                              Found: {}. Expected {}").format(
                                    method_name,
                                    len(self._parameters),
                                    len(parameters))
        for key in parameters:
            if key in self._parameters:
                # check value
                if self._parameters[key] != parameters[key]:
                    raise ValueError("Wrong '{}' parameter \
                                     value for method '{}'. \
                                     Found:'{}'. Expected:'{}'").format(
                                        method_name,
                                        key,
                                        self._parameters[key],
                                        parameters[key])
            else:
                raise ValueError("Parameter '%s' not found in method '%s'",
                                 (str(key), method_name))
        return True
