from __future__ import print_function

import warnings
import functools
from distutils.version import LooseVersion

import astropy
from astropy.utils.exceptions import AstropyDeprecationWarning, AstropyUserWarning

# We use functionality of the deprecated and deprecated_renamed_argument
# decorators from astropy that was added in v2.0.12 LTS and v3.1.2
av = astropy.__version__
ASTROPY_LT_31 = (LooseVersion(av) < LooseVersion("2.0.12") or
                 (LooseVersion("3.0") <= LooseVersion(av) and LooseVersion(av) < LooseVersion("3.1.2")))

__all__ = ['deprecated', 'deprecated_renamed_argument']


if not ASTROPY_LT_31:
    from astropy.utils.decorators import deprecated, deprecated_renamed_argument
else:
    def deprecated(since, message='', alternative=None, **kwargs):

        def deprecate_function(func, message=message, since=since,
                               alternative=alternative):
            if message == '':
                message = ('Function {} has been deprecated since {}.'
                           .format(func.__name__, since))
                if alternative is not None:
                    message += '\n Use {} instead.'.format(alternative)

            @functools.wraps(func)
            def deprecated_func(*args, **kwargs):
                warnings.warn(message, AstropyDeprecationWarning)
                return func(*args, **kwargs)
            return deprecated_func

        def deprecate_class(cls, message=message, since=since,
                            alternative=alternative):
            if message == '':
                message = ('Class {} has been deprecated since {}.'
                           .format(cls.__name__, since))
                if alternative is not None:
                    message += '\n Use {} instead.'.format(alternative)

            cls.__init__ = deprecate_function(cls.__init__, message=message)

            return cls

        def deprecate(obj):
            if isinstance(obj, type):
                return deprecate_class(obj)
            else:
                return deprecate_function(obj)

        return deprecate

    def deprecated_renamed_argument(old_name, new_name, since,
                                    arg_in_kwargs=False, relax=False,
                                    pending=False,
                                    warning_type=AstropyDeprecationWarning,
                                    alternative=''):
        cls_iter = (list, tuple)
        if isinstance(old_name, cls_iter):
            n = len(old_name)
            # Assume that new_name and since are correct (tuple/list with the
            # appropriate length) in the spirit of the "consenting adults". But the
            # optional parameters may not be set, so if these are not iterables
            # wrap them.
            if not isinstance(arg_in_kwargs, cls_iter):
                arg_in_kwargs = [arg_in_kwargs] * n
            if not isinstance(relax, cls_iter):
                relax = [relax] * n
            if not isinstance(pending, cls_iter):
                pending = [pending] * n
        else:
            # To allow a uniform approach later on, wrap all arguments in lists.
            n = 1
            old_name = [old_name]
            new_name = [new_name]
            since = [since]
            arg_in_kwargs = [arg_in_kwargs]
            relax = [relax]
            pending = [pending]

        def decorator(function):
            # Lazy import to avoid cyclic imports
            from astropy.utils.compat.funcsigs import signature

            # The named arguments of the function.
            arguments = signature(function).parameters
            keys = list(arguments.keys())
            position = [None] * n

            for i in range(n):
                # Determine the position of the argument.
                if arg_in_kwargs[i]:
                    pass
                else:
                    if new_name[i] is None:
                        continue
                    elif new_name[i] in arguments:
                        param = arguments[new_name[i]]
                        # In case the argument is not found in the list of arguments
                        # the only remaining possibility is that it should be caught
                        # by some kind of **kwargs argument.
                        # This case has to be explicitly specified, otherwise throw
                        # an exception!
                    else:
                        raise TypeError('"{}" was not specified in the function '
                                        'signature. If it was meant to be part of '
                                        '"**kwargs" then set "arg_in_kwargs" to "True"'
                                        '.'.format(new_name[i]))

                    # There are several possibilities now:

                    # 1.) Positional or keyword argument:
                    if param.kind == param.POSITIONAL_OR_KEYWORD:
                        position[i] = keys.index(new_name[i])

                    # 2.) Keyword only argument (Python 3 only):
                    elif param.kind == param.KEYWORD_ONLY:
                        # These cannot be specified by position.
                        position[i] = None

                    # 3.) positional-only argument, varargs, varkwargs or some
                    #     unknown type:
                    else:
                        raise TypeError('cannot replace argument "{0}" of kind '
                                        '{1!r}.'.format(new_name[i], param.kind))

            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                for i in range(n):
                    # The only way to have oldkeyword inside the function is
                    # that it is passed as kwarg because the oldkeyword
                    # parameter was renamed to newkeyword.
                    if old_name[i] in kwargs:
                        value = kwargs.pop(old_name[i])
                        # Display the deprecation warning only when it's not
                        # pending.
                        if not pending[i]:
                            message = ('"{0}" was deprecated in version {1} '
                                       'and will be removed in a future version. '
                                       .format(old_name[i], since[i]))
                            if new_name[i] is not None:
                                message += ('Use argument "{}" instead.'
                                            .format(new_name[i]))
                            elif alternative:
                                message += ('\n        Use {} instead.'
                                            .format(alternative))
                            warnings.warn(message, warning_type, stacklevel=2)

                        # Check if the newkeyword was given as well.
                        newarg_in_args = (position[i] is not None and
                                          len(args) > position[i])
                        newarg_in_kwargs = new_name[i] in kwargs

                        if newarg_in_args or newarg_in_kwargs:
                            if not pending[i]:
                                # If both are given print a Warning if relax is
                                # True or raise an Exception is relax is False.
                                if relax[i]:
                                    warnings.warn(
                                        '"{0}" and "{1}" keywords were set. '
                                        'Using the value of "{1}".'
                                        ''.format(old_name[i], new_name[i]),
                                        AstropyUserWarning)
                                else:
                                    raise TypeError(
                                        'cannot specify both "{}" and "{}"'
                                        '.'.format(old_name[i], new_name[i]))
                        else:
                            # Pass the value of the old argument with the
                            # name of the new argument to the function
                            if new_name[i] is not None:
                                kwargs[new_name[i]] = value

                return function(*args, **kwargs)

            return wrapper
        return decorator
