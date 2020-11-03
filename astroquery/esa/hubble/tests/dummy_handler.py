import os
from astroquery.utils.tap.model import modelutils, taptable
from requests.models import Response

__all__ = ['DummyHandler']


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class DummyHandler:

    def get_file(self, filename, response=None, verbose=False):
        return None

    def get_table(self, filename=None, response=None, output_format='votable',
                  verbose=False):
        return None

    def request(self, t="GET", link=None, params=None,
                cache=None,
                timeout=None):
        return None

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
            raise ValueError("".join(("Method '",
                                      str(method),
                                      "' not invoked. (Invoked method is '",
                                      str(self._invokedMethod)+"')")))

    def check_parameters(self, parameters, method_name):
        if parameters is None:
            return len(self._parameters) == 0
            if len(parameters) != len(self._parameters):
                raise ValueError("Wrong number of parameters for method '%s'. \
                                 Found: %d. Expected %d",
                                 (method_name,
                                  len(self._parameters),
                                  len(parameters)))
            for key in parameters:
                if key in self._parameters:
                    # check value
                    if self._parameters[key] != parameters[key]:
                        raise ValueError("".join(("Wrong '%s' parameter ",
                                                  "value for method '%s'. ",
                                                  "Found:'%s'. Expected:'%s'",
                                                  (method_name,
                                                   key,
                                                   self._parameters[key],
                                                   parameters[key]))))
                else:
                    raise ValueError("Parameter '%s' not found in method '%s'",
                                     (str(key), method_name))
        return False
