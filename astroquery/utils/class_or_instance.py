# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Helper class that can be used to decorate instance
methods of a class so that they can be called either as a class method
or as instance methods.
"""
import functools
import inspect
from collections import namedtuple

__all__ = ["class_or_instance"]

class class_or_instance(object):

    def __init__(self, fn):
        self.fn = fn
        argspec = inspect.getargspec(fn)
        if argspec.args[0] != 'self':
            raise ValueError('Method created with "self" not the first argument')
        else:
            # in the "fake" definition, we leave out "self"
            args = argspec.args[1:]

        # Some "default args" have repr's that are *not* evaluatable
        # These must be replaced with strings
        if argspec.defaults is not None:
            defaults = []
            for ii,default in enumerate(argspec.defaults):
                try:
                    eval("%s" % repr(default))
                    defaults.append(default)
                except SyntaxError:
                    defaults.append('%s' % repr(default))
        else:
            defaults = None

        self.argspec_d = dict(args=args, varargs=argspec.varargs,
                              varkw=argspec.keywords, defaults=defaults)

        if hasattr(fn,'__doc__'):
            self.__doc__ = fn.__doc__
        else:
            self.__doc__ = ""

    def __get__(self, obj, cls):
        if obj is not None:
            f = lambda *args, **kwds: self.fn(obj, *args, **kwds)
        else:
            f = lambda *args, **kwds: self.fn(cls, *args, **kwds)
        functools.update_wrapper(f, self.fn)
        return f

        # this was a failed attempt, preserved in history
        formatted_args = inspect.formatargspec(**self.argspec_d)
        fndef = 'lambda %s: f%s' % (formatted_args.lstrip('(').rstrip(')'),
                                    formatted_args)
        try:
            fake_fn = eval(fndef, {'f': f})
        except SyntaxError:
            # raise it at this level so it can be debugged
            raise Exception('syntax error')
        return functools.wraps(self.fn)(fake_fn)

class property_class_or_instance(property):

    def __get__(self, obj, cls):
        if obj is not None:
            return self.fget(obj)
        else:
            return self.fget(cls)

    def __set__(self, *args):
        raise ValueError("Setters don't work.")
