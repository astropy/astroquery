import os
from astroquery.utils.tap.model import modelutils

__all__ = ['ESAHubble', 'ESAHubbleClass', 'Conf', 'conf',
           'DummyHandler', 'dummy']


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class DummyHandler(object):

    def get_file(self, url, filename, verbose=False):
        print("************* DummyHandler!!!!!!!!")
        file = data_path(filename)
        print(file)
        if file.endswith(".xml"):
            with open(file, 'r') as myfile:
                data = myfile.read().replace("\n", "")
        else:
            with open(file, 'rb') as myfile:
                data = myfile.read()
        return data

    def get_table(self, url, filename=None, output_format='votable',
                  verbose=False):
        print("************* DummyHandler!!!!!!!!")
        if filename is None:
            raise ValueError("filename must be specified")
        table = modelutils.read_results_table_from_file(filename,
                                                        str(output_format))
        return table

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
            raise Exception("".join(("Method '",
                                     str(method),
                                     "' not invoked. (Invoked method is '",
                                     str(self._invokedMethod)+"')")))

    def check_parameters(self, parameters, method_name):
        if parameters is None:
            return len(self._parameters) == 0
            if len(parameters) != len(self._parameters):
                raise Exception("Wrong number of parameters for method '%s'. \
                                Found: %d. Expected %d",
                                (method_name,
                                 len(self._parameters),
                                 len(parameters)))
            for key in parameters:
                if key in self._parameters:
                    # check value
                    if self._parameters[key] != parameters[key]:
                        raise Exception("".join(("Wrong '%s' parameter ",
                                                 "value for method '%s'. ",
                                                 "Found: '%s'. Expected: '%s'",
                                                 (method_name,
                                                  key,
                                                  self._parameters[key],
                                                  parameters[key]))))
                else:
                    raise Exception("Parameter '%s' not found for method '%s'",
                                    (str(key), method_name))
        return False
