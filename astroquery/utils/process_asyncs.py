# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Process all "async" methods into direct methods.
"""

from class_or_instance import class_or_instance

def process_asyncs(cls):
    """
    Convert all query_x_async methods to query_x methods
    """
    methods = cls.__dict__.keys()
    for k in methods:
        newmethodname = k.replace("_async","")
        if 'async' in k and newmethodname not in methods:

            async_method = getattr(cls,k)

            @class_or_instance
            def newmethod(self, *args, **kwargs):
                if 'verbose' in kwargs:
                    verbose = kwargs.pop('verbose')
                else:
                    verbose = False
                response = async_method(*args,**kwargs)
                result = self._parse_result(response, verbose=verbose)
                return result

            newmethod.fn.__doc__ = ("Returns a table object.\n" +
                                    async_method.__doc__)

            setattr(cls,newmethodname,newmethod)
