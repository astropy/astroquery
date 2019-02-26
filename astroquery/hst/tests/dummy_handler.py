import os

__all__ = ['Hst', 'HstClass', 'Conf', 'conf', 'DummyHandler', 'dummy']


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class DummyHandler(object):

    def get_file(self, url, filename, verbose=False):
        file = data_path(filename)
        print(file)
        if file.endswith(".xml"):
            with open(file, 'r') as myfile:
                data = myfile.read().replace("\n", "")
        else:
            with open(file, 'rb') as myfile:
                data = myfile.read()
        return data

    def __init__(self, method, parameters):
        self.__invokedMethod = method
        self.__parameters = parameters

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
            raise Exception("".join((
                                     "Method '",
                                     str(method),
                                     "' not invoked. (Invoked method is '",
                                     str(self.__invokedMethod)+"')")))

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
                        raise Exception("".join((
                                                 "Wrong '%s' parameter ",
                                                 "value for method '%s'. ",
                                                 "Found: '%s'. Expected: '%s'",
                                                 (method_name,
                                                  key,
                                                  self.__parameters[key],
                                                  parameters[key]))))
                else:
                    raise Exception("Parameter '%s' not found for method '%s'",
                                    (str(key), method_name))
        return False
