"""
=====================
ISO Astroquery Module
=====================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

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
