# Licensed under a 3-clause BSD style license - see LICENSE.rst
__version__ = '0.2.0'


class SchemaError(Exception):

    """Error during Schema validation."""

    def __init__(self, autos, errors):
        self.autos = autos if type(autos) is list else [autos]
        self.errors = errors if type(errors) is list else [errors]
        Exception.__init__(self, self.code)

    @property
    def code(self):
        def uniq(seq):
            seen = set()
            seen_add = seen.add
            return [x for x in seq if x not in seen and not seen_add(x)]
        a = uniq(i for i in self.autos if i is not None)
        e = uniq(i for i in self.errors if i is not None)
        if e:
            return '\n'.join(e)
        return '\n'.join(a)


class And:

    def __init__(self, *args, **kw):
        self._args = args
        assert list(kw) in (['error'], [])
        self._error = kw.get('error')

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(repr(a) for a in self._args)})"

    def validate(self, data):
        for s in [Schema(s, error=self._error) for s in self._args]:
            data = s.validate(data)
        return data


class Or(And):

    def validate(self, data):
        x = SchemaError([], [])
        for s in [Schema(s, error=self._error) for s in self._args]:
            try:
                return s.validate(data)
            except SchemaError as _x:
                x = _x
        raise SchemaError([f'{self!r} did not validate {data!r}'] + x.autos,
                          [self._error] + x.errors)


class Use:

    def __init__(self, callable_, *, error=None):
        assert callable(callable_)
        self._callable = callable_
        self._error = error

    def __repr__(self):
        return f'{self.__class__.__name__}({self._callable!r})'

    def validate(self, data):
        try:
            return self._callable(data)
        except SchemaError as x:
            raise SchemaError([None] + x.autos, [self._error] + x.errors)
        except BaseException as x:
            f = self._callable.__name__
            raise SchemaError(f'{f}({data!r}) raised {x!r}', self._error)


def priority(s):
    """Return priority for a give object.

    :rtype: int
    """
    if type(s) in (list, tuple, set, frozenset):
        return 6
    if type(s) is dict:
        return 5
    # We exclude Optional from the test, otherwise it will make a
    # catch-all rule like "str" take precedence over any optional field,
    # which would be inintuitive.
    if hasattr(s, 'validate') and not type(s) is Optional:
        return 4
    if type(s) is type:
        return 3
    if callable(s):
        return 2
    else:
        return 1


class Schema:

    def __init__(self, schema, *, error=None):
        self._schema = schema
        self._error = error

    def __repr__(self):
        return f'{self.__class__.__name__}({self._schema!r})'

    def validate(self, data):
        s = self._schema
        e = self._error
        if type(s) in (list, tuple, set, frozenset):
            data = Schema(type(s), error=e).validate(data)
            return type(s)(Or(*s, error=e).validate(d) for d in data)
        if type(s) is dict:
            data = Schema(dict, error=e).validate(data)
            new = type(data)()
            x = None
            coverage = set()  # non-optional schema keys that were matched
            sorted_skeys = list(sorted(s, key=priority))

            for key, value in data.items():
                valid = False
                skey = None
                for skey in sorted_skeys:
                    svalue = s[skey]
                    try:
                        nkey = Schema(skey, error=e).validate(key)
                    except SchemaError:
                        pass
                    else:
                        try:
                            nvalue = Schema(svalue, error=e).validate(value)
                        except SchemaError as _x:
                            x = _x
                            raise
                        else:
                            coverage.add(skey)
                            valid = True
                            break
                if valid:
                    new[nkey] = nvalue
                elif skey is not None:
                    if x is not None:
                        raise SchemaError([f'key {key!r} is required'] + x.autos, [e] + x.errors)
                    else:
                        raise SchemaError(f'key {skey!r} is required', e)
            coverage = set(k for k in coverage if type(k) is not Optional)
            required = set(k for k in s if type(k) is not Optional)
            if coverage != required:
                raise SchemaError(f'missed keys {(required - coverage)!r}', e)
            if len(new) != len(data):
                raise SchemaError(f'wrong keys {new!r} in {data!r}', e)
            return new
        if hasattr(s, 'validate'):
            try:
                return s.validate(data)
            except SchemaError as x:
                raise SchemaError([None] + x.autos, [e] + x.errors)
            except BaseException as x:
                raise SchemaError(f'{s!r}.validate({data!r}) raised {x!r}', self._error)
        if type(s) is type:
            if isinstance(data, s):
                return data
            else:
                raise SchemaError(f'{data!r} should be instance of {s!r}', e)
        if callable(s):
            f = s.__name__
            try:
                if s(data):
                    return data
            except SchemaError as x:
                raise SchemaError([None] + x.autos, [e] + x.errors)
            except BaseException as x:
                raise SchemaError(f'{f}({data!r}) raised {x!r}', self._error)
            raise SchemaError(f'{f}({data!r}) should evaluate to True', e)
        if s == data:
            return data
        else:
            raise SchemaError(f'{s!r} does not match {data!r}', e)


class Optional(Schema):

    """Marker for an optional part of Schema."""
