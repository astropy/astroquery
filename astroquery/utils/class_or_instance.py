# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Helper class that can be used to decorate instance
methods of a class so that they can be called either as a class method
or as instance methods.
"""
import functools

__all__ = ["class_or_instance"]


class class_or_instance:

    def __init__(self, fn):
        self.fn = fn

        if hasattr(fn, '__doc__'):
            self.__doc__ = fn.__doc__
        else:
            self.__doc__ = ""

    def __get__(self, obj, cls):
        def f(*args, **kwds):
            if obj is not None:
                return self.fn(obj, *args, **kwds)
            else:
                return self.fn(cls, *args, **kwds)
        functools.update_wrapper(f, self.fn)
        return f


class property_class_or_instance(property):

    def __get__(self, obj, cls):
        if obj is not None:
            return self.fget(obj)
        else:
            return self.fget(cls)

    def __set__(self, *args):
        raise ValueError("Setters don't work.")
