# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This sub-module has a helper class that can be used to decorate instance
methods of a class so that they can be called either as a class method
or as instance methods.
"""
import functools

__all__ = ["class_or_instance"]

class class_or_instance(object):
    def __init__(self, fn):
        self.fn = fn
        if hasattr(fn,'__docstr__'):
            self.__docstr__ = fn.__docstr__
        else:
            self.__docstr__ = ""

    def __get__(self, obj, cls):
        if obj is not None:
            f = lambda *args, **kwds: self.fn(obj, *args, **kwds)
        else:
            f = lambda *args, **kwds: self.fn(cls, *args, **kwds)
        functools.update_wrapper(f, self.fn)
        return f

    # Probably a bad idea: hack to make this callable
    def __call__(self,*args):
        self.fn(*args)
