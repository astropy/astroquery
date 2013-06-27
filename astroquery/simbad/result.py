# Licensed under a 3-clause BSD style license - see LICENSE.rst

import re
import tempfile
from collections import namedtuple
import warnings
from astropy.table import Table
try:
    import astropy.io.vo.table as votable
except ImportError:
    import astropy.io.votable as votable

__all__ = ['SimbadResult']


error_regex = re.compile(r'(?ms)\[(?P<line>\d+)\]\s?(?P<msg>.+?)(\[|\Z)')
bibcode_regex = re.compile(r'query\s+bibcode\s+(wildcard)?\s+([\w]*)')

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
        self.__file = None

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
        if self.__file is None:
            self.__file = tempfile.NamedTemporaryFile()
            self.__file.write(self.data.encode('utf-8'))
            self.__file.flush()
            # if bibcode query then first create table from raw data
            bibcode_match = bibcode_regex.search(self.script)
            if bibcode_match:
                self.__table = _create_bibcode_table(self.data, bibcode_match.group(2))
            else:
                self.__table = Table.read(self.__file, format="votable")
        return self.__table

def _create_bibcode_table(data, splitter):
    ref_list = [splitter + ref for ref in data.split(splitter)][1:]
    table = Table(names=['References'], dtypes=['object'])
    for ref in ref_list:
        table.add_row([ref.decode('utf-8')])
    return table
