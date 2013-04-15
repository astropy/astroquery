# Licensed under a 3-clause BSD style license - see LICENSE.rst

__all__ = ['VoTableDef']


class VoTableDef(object):
    def __init__(self, *args, **kwargs):
        self.__fields = []
        for value in args:
            names = str(value).split(',')
            for name in [v.strip() for v in names if v.strip()]:
                self.__fields.append(name)
        if 'name' in kwargs:
            self.name = kwargs['name']
            del kwargs['name']
        else:
            self.name = ''
        if kwargs:
            raise ValueError("'name' is the only keyword argument allowed")

    @property
    def fields(self):
        return list(self.__fields)

    @property
    def __fields_str(self):
        return ', '.join(self.fields)

    @property
    def def_str(self):
        return 'votable %s {%s}\n' % (self.name, self.__fields_str)

    @property
    def open_str(self):
        return 'votable open %s\n' % self.name

    @property
    def close_str(self):
        return 'votable close %s\n' % self.name
