# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Process all "async" methods into direct methods.
"""

import inspect
from types import MethodType
from class_or_instance import class_or_instance

def process_asyncs(cls):
    """
    Convert all query_x_async methods to query_x methods
    """
    methods = inspect.getmembers(cls)
    for k in methods:
        methodname = k.replace("_async","")
        if 'async' in k and methodname not in methods:

            @class_or_instance
            def method(self, verbose=False, *args, **kwargs):
                response = self.__dict__[k](*args,**kwargs)
                result = self._parse_result(response, verbose=verbose)
                return result

            method.__docstr__ = ("Returns a table object.\n" +
                    cls.__dict__[k].__docstr__)

            cls.__dict__[methodname] = MethodType(method, None, cls)
