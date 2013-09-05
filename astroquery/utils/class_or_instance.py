# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Helper class that can be used to decorate instance
methods of a class so that they can be called either as a class method
or as instance methods.
"""
import functools
import inspect

__all__ = ["class_or_instance"]

class class_or_instance(object):

    def __init__(self, fn):
        self.fn = fn
        self.__name__ = fn.__name__
        self.__module__ = fn.__module__

        self.argspec = inspect.getargspec(fn)
        self.func_defaults = fn.func_defaults

        if hasattr(fn,'__file__'):
            self.__file__ = fn.__file__

        if hasattr(fn,'__doc__'):
            self.__doc__ = fn.__doc__
        else:
            self.__doc__ = ""

    def __get__(self, obj, cls):
        if obj is not None:
            def f(*args, **kwds):
                return self.fn(obj, *args, **kwds)
        else:
            def f(*args, **kwds):
                self.fn(cls, *args, **kwds)
        functools.update_wrapper(f, self.fn)
        return f
