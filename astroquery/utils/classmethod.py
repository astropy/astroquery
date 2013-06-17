# Licensed under a 3-clause BSD style license - see LICENSE.rst
import functools

__all__ = ["class_or_instance"]

class class_or_instance(object):
    def __init__(self, fn):
        self.fn = fn

    def __get__(self, obj, cls):
        if obj is not None:
            return lambda *args, **kwds: self.fn(obj, *args, **kwds)
        else:
            return lambda *args, **kwds: self.fn(cls, *args, **kwds)
