# Licensed under a 3-clause BSD style license - see LICENSE.rst

__all__ = ['_ScriptParameterWildcard',
            '_ScriptParameterRadius',
            '_ScriptParameterFrame',
            '_ScriptParameterEquinox',
            '_ScriptParameterEpoch',
            '_ScriptParameterRowLimit',
            'ValidatedAttribute',
            ]


class _ScriptParameter(object):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    def __nonzero__(self):
        return self.__value not in [None, False]

    def __str__(self):
        if self:
            return str(self.__value)
        else:
            return ''


def ValidatedAttribute(attr_name, attr_class):
    def decorator(cls):
        name = "__" + attr_name

        def getter(self):
            return getattr(self, name)

        def setter(self, value):
            v = attr_class(value)
            setattr(self, name, v)

        setattr(cls, attr_name, property(getter, setter, None,
                                                        attr_class.__doc__))
        return cls

    return decorator


class _ScriptParameterWildcard(_ScriptParameter):
    """ If set to True the query will be processed as an expression with
    wildcards.
    """
    def __init__(self, value=None):
        if value is None:
            self.value = None
        elif value == False:
            self.value = False
        else:
            self.value = True

    def __str__(self):
        if self.value == True:
            return 'wildcard'
        else:
            return ''


class _ScriptParameterRadius(_ScriptParameter):
    """ Radius value for cone search. The value must be suffixed by
    'd' (degrees), 'm' (arcminutes) or 's' (arcseconds).
    """
    def __init__(self, value):
        if value is None:
            self.value = None
            return
        if not isinstance(value, basestring):
            raise ValueError("'radius' parameter must be a string object")
        if value[-1].lower() not in ('d', 'm', 's'):
            raise ValueError("'radius' parameter must be suffixed with " \
                                "either 'd', 'm' or 's'")
        try:
            float(value[:-1])
        except:
            raise ValueError("unable to interpret 'radius' parameter as a number")
        self.value = str(value.lower())


class _ScriptParameterFrame(_ScriptParameter):
    """ Input frame for coordinate query. Allowed values are ICRS, FK5, FK4, 
    GAL, SGAL or ECL.
    """
    _frames = ('ICRS', 'FK4', 'FK5', 'GAL', 'SGAL', 'ECL')
    def __init__(self, value):
        if value is None:
            self.value = None
            return
        v = str(value).upper()
        if v not in self._frames:
            raise ValueError("'frame' parameter must be one of %s " \
                                "('%s' was given)" % (str(self._frames), v))
        self.value = v


class _ScriptParameterEpoch(_ScriptParameter):
    """ Epoch value for coordinate query. Example 'J2000', 'B1950'.
    """
    def __init__(self, value):
        if value is None:
            self.value = None
            return
        v = str(value).upper()
        if v[0] not in ['J', 'B']:
            raise ValueError("'invalid value for parameter 'epoch' (%s)" % \
                                                                        value)
        try:
            float(v[1:])
        except:
            raise ValueError("'invalid value for parameter 'epoch' (%s)" % \
                                                                        value)
        self.value = v


class _ScriptParameterEquinox(_ScriptParameter):
    """ Equinox value for coordinate query. For example '2006.5'.
    """
    def __init__(self, value):
        if value is None:
            self.value = None
            return
        v = str(value)
        try:
            float(v)
        except:
            raise ValueError("invalid value for parameter 'equinox' (%s)" % \
                                                                        value)
        self.value = v


class _ScriptParameterRowLimit(_ScriptParameter):
    """ Limit of returnred rows (0 sets the limit to the maximum).
    """
    def __init__(self, value):
        if value is None:
            self.value = None
            return
        v = str(value)
        if not v.isdigit():
            raise ValueError("invalid value for 'row limit' parameter (%s)" % \
                                                                        value)
        self.value = v

