#Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# astroquery uses the pytest framework for testing
# this is already available in astropy and does
# not require a separate install. Import it using:
from astropy.tests.helper import pytest

# It would be best if tests are separated in two
# modules. This module performs tests on local data
# by mocking HTTP requests and responses. To test the
# same functions on the remote server, put the relevant
# tests in the 'test_module_remote.py'

# Now import other commonly used modules for tests
import os
import requests

from numpy import testing as npt
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u

from ...utils.testing_tools import MockResponse

# finally import the module which is to be tested
# and the various configuration items created
from ... import template_module
from ...template_module import (SERVER, TIMEOUT)

# Local tests should have the corresponding data stored
# in the ./data folder. This is the actual HTTP response
# one would expect from the server when a valid query is made.
# Its best to keep the data file small, so that testing is
# quicker. When running tests locally the stored data is used
# to mock the HTTP requests and response part of the query
# thereby saving time and bypassing unreliability for
# an actual remote network query.


# ./setup_package.py helps the test function locate the data file
# define a function that can construct the full path to the file in the
# ./data directory:
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


# define the 'get_mockreturn' function that returns the
# dummy HTTP response for the dummy 'get' function, by
# reading in data from some data file:
def get_mockreturn(url, params=None, timeout=10, **kwargs):
    filename = data_path('dummy.dat')
    content = open(filename, "rb").read()
    return MockResponse(content, **kwargs)


# finally test the methods using the mock HTTP response
def test_query_object(patch_get):
    result = template_module.core.DummyClass.query_object('m1')
    assert isinstance(result, Table)

# similarly fill in tests for each of the methods
# look at tests in existing modules for more examples
