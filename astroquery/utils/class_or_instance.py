# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Helper class that can be used to decorate instance
methods of a class so that they can be called either as a class method
or as instance methods.
"""
import inspect

__all__ = ["class_or_instance"]

class class_or_instance(object):

    def __init__(self, fn):
        self.fn = fn

        if hasattr(fn,'__doc__'):
            self.__doc__ = fn.__doc__
        else:
            self.__doc__ = ""

    def __get__(self, obj, cls):
        src_func = self.fn

        self.argspec = inspect.getargspec(src_func)
        self.src_doc = src_func.__doc__
        self.src_defaults = src_func.func_defaults

        #tgt_argspec = inspect.getargspec(src_func)

        name = src_func.__name__
        argspec = self.argspec
        if obj is not None:
            slf = obj
        else:
            slf = cls
        if argspec[0][0] == 'self':
            argspec[0].remove('self')
        tgt_func = src_func
        signature = inspect.formatargspec(formatvalue=lambda val: "",
                                          *argspec
                                          )[1:-1]
        new_func = ('def _wrapper_(%(signature)s):\n'
                    '    return %(tgt_func)s(%(slf)s,%(signature)s)' %
                      {'signature':signature,
                       'slf':'slf',
                       'tgt_func':'tgt_func'}
                   )
        evaldict = {'tgt_func': tgt_func, 'slf': slf}
        exec new_func in evaldict
        wrapped = evaldict['_wrapper_']
        wrapped.__name__ = name
        wrapped.__doc__ = self.src_doc
        wrapped.func_defaults = self.src_defaults
        wrapped.__module__ = tgt_func.__module__
        wrapped.__dict__ = tgt_func.__dict__
        return wrapped

class property_class_or_instance(property):

    def __get__(self, obj, cls):
        if obj is not None:
            return self.fget(obj)
        else:
            return self.fget(cls)

    def __set__(self, *args):
        raise ValueError("Setters don't work.")
