# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Helper class that can be used to decorate instance
methods of a class so that they can be called either as a class method
or as instance methods.
"""
import functools
import inspect
import types

__all__ = ["class_or_instance","copy_argspec"]

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

class copy_argspec(object):
    """
    copy_argspec is a signature modifying decorator.  Specifically, it copies
    the signature from `source_func` to the wrapper, and the wrapper will call
    the original function (which should be using *args, **kwds).  The argspec,
    docstring, and default values are copied from src_func, and __module__ and
    __dict__ from tgt_func.
    (see http://stackoverflow.com/questions/18625510/how-can-i-programmatically-change-the-argspec-of-a-function-not-in-a-python-de?answertab=votes#tab-top)
    """
    def __init__(self, src_func):
        self.argspec = inspect.getargspec(src_func)
        self.src_doc = src_func.__doc__
        self.src_defaults = src_func.func_defaults

    def __call__(self, tgt_func):
        tgt_argspec = inspect.getargspec(tgt_func)
        need_self = False
        if tgt_argspec[0][0] == 'self':
            need_self = True

        name = tgt_func.__name__
        argspec = self.argspec
        if argspec[0][0] == 'self':
            need_self = False
        if need_self:
            newargspec = (['self'] + argspec[0],) + argspec[1:]
        else:
            newargspec = argspec
        signature = inspect.formatargspec(formatvalue=lambda val: "",
                                          *newargspec
                                          )[1:-1]
        new_func = ('def _wrapper_(%(signature)s):\n'
                    '    return %(tgt_func)s(%(signature)s)' %
                    {'signature':signature, 'tgt_func':'tgt_func'}
                    )
        evaldict = {'tgt_func': tgt_func}
        exec new_func in evaldict
        wrapped = evaldict['_wrapper_']
        wrapped.__name__ = name
        wrapped.__doc__ = self.src_doc
        wrapped.func_defaults = self.src_defaults
        wrapped.__module__ = tgt_func.__module__
        wrapped.__dict__ = tgt_func.__dict__
        return wrapped
