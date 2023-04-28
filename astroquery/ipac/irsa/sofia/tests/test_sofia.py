# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

import os

from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u

from astroquery.utils.mocks import MockResponse

from .... import sofia
from ....sofia import conf

DATA_FILES = {'GET':
              {'http://dummy_server_mirror_1':
               'dummy.dat'}}

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

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
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(sofia.core.SOFIAClass, '_request',
               nonremote_request)
    return mp


# finally test the methods using the mock HTTP response
def test_query_object(patch_request):
    result = sofia.core.SOFIAClass().query_object('m1')
    assert isinstance(result, Table)

# similarly fill in tests for each of the methods
# look at tests in existing modules for more examples
