# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import pytest

# It would be best if tests are separated in two
# modules. This module performs tests on local data
# by mocking HTTP requests and responses. To test the
# same functions on the remote server, put the relevant
# tests in the 'test_module_remote.py'

import os
import requests

from numpy import testing as npt
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u

from ...utils.testing_tools import MockResponse

from ... import esasky
from ...esasky import conf

# Local tests should have the corresponding data stored
# in the ./data folder. This is the actual HTTP response
# one would expect from the server when a valid query is made.
# Its best to keep the data file small, so that testing is
# quicker. When running tests locally the stored data is used
# to mock the HTTP requests and response part of the query
# thereby saving time and bypassing unreliability for
# an actual remote network query.

DATA_FILES = {'GET':
              # You might have a different response for each URL you're
              # querying:
              {
              'http://ammidev.n1data.lan:8080/esasky-tap/observations':
               'observations.txt' 
               },
              }


# ./setup_package.py helps the test function locate the data file
# define a function that can construct the full path to the file in the
# ./data directory:
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# define a monkeypatch replacement request function that returns the
# dummy HTTP response for the dummy 'get' function, by
# reading in data from some data file:
def nonremote_request(self, request_type, url, **kwargs):
    # kwargs are ignored in this case, but they don't have to be
    # (you could use them to define which data file to read)
    with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(esasky.core.ESASkyClass, '_request',
               nonremote_request)
    return mp


# finally test the methods using the mock HTTP response
def test_query_object(patch_request):
    result = esasky.core.ESASkyClass().query_object('m1')
    assert isinstance(result, Table)

# similarly fill in tests for each of the methods
# look at tests in existing modules for more examples

def test_list_catalogs():
    result = esasky.core.ESASkyClass().list_catalogs()
    assert (len(result) == 13)
    
test_list_catalogs()

