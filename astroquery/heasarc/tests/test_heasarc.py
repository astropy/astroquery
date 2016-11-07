# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

from __future__ import print_function
from astropy.tests.helper import pytest, catch_warnings
from astropy.utils.exceptions import AstropyWarning

from ...utils.testing_tools import MockResponse
from ..heasarc import HeasarcClass

data_filenames = {"good": "testing_table.fits",
                  "bad_table": "bad_table.html",
                  "bad_object": "bad_object.html",
                  "fallback": "table_fallback.fits"}


# some basic defs of names
good_object = "3c273"
good_table = "rospublic"
bad_object = "ImABadObject"
bad_table = "ImABadTable"
fallback_table = "numaster"

def get_mockreturn(url, params=None, timeout=10, **kwargs):
    obejct_name = params.get('object_name')
    table_name = params.get('mission')

    if object_name == good_object and table_name == good_table:
        content = open(data_path(data_filenames['good']), "rb").read()
    elif object_name == bad_object:
        content = open(data_path(data_filenames['bad_object']), "r").read()
    elif table_name == bad_table:
        content = open(data_path(data_filenames['bad_table']), "r").read()
    elif table_name == fallback_table:
        content = open(data_path(data_filenames['fallback']), "rb").read()

    return MockResponse(content, **kwargs)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


class TestHeasarcObjectLocal(object):

    def setup_class(self):
        self.query_object = HeasarcClass().query_object
        self.bad_table_msg = 'Error: No table info found for heasarc for table ImABadTable'
        self.bad_object_msg = 'Object ImABadObject is not recognized by the GRB or SIMBAD+Sesame or NED name resolvers.'

    def test_good(self):
        '''Do a run through of everything with a good table'''
        table = self.query_object(object_name=good_object,
                                          mission=good_table)
        table.sort("NAME")
        col = table[:3]['NAME']
        assert col.tostring().replace(" ", "").lower() == 3 * good_object

    def test_bad_table(self):
        '''Test the table warnings are working'''
        with catch_warnings(AstropyWarning) as w:
            self.query_object(object_name, mission=bad_table)
        assert w[0].message.message == self.bad_table_msg

    def test_bad_object(self):
        '''Test the table warnings are working'''
        with catch_warnings(AstropyWarning) as w:
            self.query_object(bad_object, mission=good_table)
        assert w[0].message.message == self.bad_object_msg

    def test_fallback(self):
        '''Test fallback '''
        table self.query_object(good_object, mission=fallback_table)
        assert table[-1]['PUBLIC_DATE'] == -1
