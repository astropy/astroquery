# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.tests.helper import pytest, catch_warnings
from astropy.utils.exceptions import AstropyWarning
from ...utils.testing_tools import MockResponse
from ...heasarc import Heasarc
import os


data_filenames = {"good": "testing_table_good.fits",
                  "bad_table": "bad_table.html",
                  "bad_object": "bad_object.html",
                  "fallback": "table_fallback.fits"}


# some basic defs of names
good_object = "3c273"
good_table = "rospublic"
bad_object = "ImABadObject"
bad_table = "ImABadTable"
fallback_table = "numaster"

def get_mockreturn(type, url, params=None, timeout=10, cache=True, **kwargs):
    object_name = params.get('Entry')
    table_name = params.get('tablehead').split(' ')[-1]

    if object_name == good_object and table_name == good_table:
        content = open(data_path(data_filenames['good']), "rb").read()
    elif object_name == bad_object:
        content = open(data_path(data_filenames['bad_object']), "rb").read()
    elif table_name == bad_table:
        content = open(data_path(data_filenames['bad_table']), "rb").read()
    elif table_name == fallback_table:
        content = open(data_path(data_filenames['fallback']), "rb").read()
    payload = "?Entry={object_name}&tablehead=BATCHRETRIEVALCATALOG_2.0+{table_name}".format(object_name=object_name, table_name=table_name)
    return MockResponse(content, url=Heasarc.URL + payload, **kwargs)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(Heasarc, '_request', get_mockreturn)
    return mp


bad_table_msg = 'Error: No table info found for heasarc for table ImABadTable'
bad_object_msg = 'Object ImABadObject is not recognized by the GRB or SIMBAD+Sesame or NED name resolvers.'


def test_good(patch_get):
    '''Do a run through of everything with a good table'''
    table = Heasarc.query_object(good_object, good_table)
    table.sort("NAME")
    col = table[:3]['NAME']
    assert col[0].replace(" ", "").lower() == good_object.lower()


def test_bad_table(patch_get):
    '''Test the table warnings are working'''
    with catch_warnings(AstropyWarning) as w:
        Heasarc.query_object(good_object, bad_table)
    assert str(w[0].message) == bad_table_msg


def test_bad_object(patch_get):
    '''Test the table warnings are working'''
    with catch_warnings(AstropyWarning) as w:
        Heasarc.query_object(bad_object, good_table)
    assert str(w[0].message) == bad_object_msg
