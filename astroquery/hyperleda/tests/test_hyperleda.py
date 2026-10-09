# Licensed under a 3-clause BSD style license - see LICENSE.rst

# Based on astroquery/template_module
# https://github.com/astropy/astroquery/tree/8248ba8fd0aa3a4c8221db729a127db047e18f4e/astroquery/template_module

import pytest

# Import commonly used modules for tests
import os
import requests
from numpy import testing as npt
from astropy.table import Table

from ...utils.testing_tools import MockResponse

# Import the module which is to be tested
# and the various configuration items created
from ... import hyperleda
from ...hyperleda import conf


# Local tests should have the corresponding data stored
# in the ./data folder. This is the actual HTTP response
# one would expect from the server when a valid query is made.

DATA_FILES = {'query': 'query_object.dat',
              }


# ./setup_package.py helps the test function locate the data file
# define a function that can construct the full path to the file in the
# ./data directory:
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# Define a monkeypatch replacement request function that returns the
# dummy HTTP response for the dummy 'get' function, by
# reading in data from some data file:
def nonremote_request(self, request_type, url, **kwargs):
    # kwargs are ignored in this case, but they don't have to be
    # (you could use them to define which data file to read)
    pick_file = 'query'
    with open(data_path(DATA_FILES[pick_file]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


# pytest fixture creates a dummy 'requests.get' function, that
# mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(hyperleda.core.HyperLEDAClass, '_request',
               nonremote_request)
    return mp


# Test the methods using the mock HTTP response
def test_query_object(patch_request):
    result = hyperleda.core.HyperLEDAClass().query_object('UGC12591',
                                                   properties=['bt', 'vt'])
    assert isinstance(result, Table)


def test_query_sql(patch_request):
    sample_query = "(mod0<=27 and t>=-3 and t<=0 and type='S0') \
    or (mod0<=27 and t>=-3 and t<=0 and type='S0-a')"
    result = hyperleda.core.HyperLEDAClass().query_sql(sample_query,
                                                       properties=['bt', 'vt'])
    assert isinstance(result, Table)
