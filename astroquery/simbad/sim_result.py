# Licensed under a 3-clause BSD style license - see LICENSE.rst

import re
import StringIO
from collections import namedtuple
import warnings

from astropy.io import vo
from astropy.table import Table

__all__ = ['SimbadResult',
            ]


error_regex = re.compile(r'(?ms)\[(?P<line>\d+)\]\s?(?P<msg>.+?)(\[|\Z)')

SimbadError = namedtuple('SimbadError', ('line', 'msg'))
VersionInfo = namedtuple('VersionInfo', ('major', 'minor', 'micro', 'patch'))


class SimbadResult(object):
    __sections = ('script', 'console', 'error', 'data')

    def __init__(self, txt, pedantic=False):
        self.__txt = txt
        self.__pedantic = pedantic
        self.__table = None
        self.__stringio = None
        self.__indexes = {}
        self.exectime = None
        self.sim_version = None
        self.__split_sections()
        self.__parse_console_section()
        self.__warn()

    def __split_sections(self):
        for section in self.__sections:
            match = re.search(r'(?ims)^::%s:+?$(?P<content>.*?)(^::|\Z)' % \
                                                        section, self.__txt)
            if match:
                self.__indexes[section] = (match.start('content'),
                                                        match.end('content'))

    def __parse_console_section(self):
        if self.console is None:
            return
        m = re.search(r'(?ims)total execution time: ([.\d]+?)\s*?secs',
                                                                self.console)
        if m:
            try:
                self.exectime = float(m.group(1))
            except:
                # TODO: do something useful here.
                pass
        m = re.search(r'(?ms)SIMBAD(\d) rel (\d)[.](\d+)([^\d^\s])?',
                                                                self.console)
        if m:
            self.sim_version = VersionInfo(*m.groups(None))

    def __warn(self):
        for error in self.errors:
            warnings.warn("Warning: The script line number %i raised "
                            "the error: %s." %\
                            (error.line, error.msg))

    def __get_section(self, section_name):
        if section_name in self.__indexes:
            return self.__txt[self.__indexes[section_name][0]:\
                                    self.__indexes[section_name][1]].strip()

    @property
    def script(self):
        return self.__get_section('script')

    @property
    def console(self):
        return self.__get_section('console')

    @property
    def error_raw(self):
        return self.__get_section('error')

    @property
    def data(self):
        return self.__get_section('data')

    @property
    def errors(self):
        result = []
        if self.error_raw is None:
            return result
        for err in error_regex.finditer(self.error_raw):
            result.append(SimbadError(int(err.group('line')),
                                        err.group('msg').replace('\n', ' ')))
        return result

    @property
    def nb_errors(self):
        if self.error_raw is None:
            return 0
        return len(self.errors)

    @property
    def table(self):
        if self.__stringio is None:
            self.__stringio = StringIO.StringIO(self.data)
            votable = vo.table.parse_single_table(self.__stringio,
                                                    pedantic=self.__pedantic)
            self.__table = Table(votable.array)
        return self.__table

