from __future__ import print_function

import pytest
from astropy.tests.helper import pytest
from ...utils.testing_tools import MockResponse

#from astroquery.vo import Registry

from ... import vo 

## To run just this test,
##
## ( cd ../../ ; python setup.py test -t astroquery/vo/tests/test_registry_remote.py --remote-data )
##


from .thetests import TestReg


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(vo.Registry, '_request', post_mockreturn)
    return mp


def post_mockreturn(method="POST", url=None, data=None, timeout=10, **kwargs):
    # Determine the test case from the URL and/or data
    assert "query" in data
    if "ivoid like 'heasarc'" in data[query] and "cap_type like 'simpleimageaccess'" in data[query]:
        testcase="basic"

    filename = data_path(DATA_FILES[testcase])
    content = open(filename, 'rb').read()

    # returning as list because this is what the mast _request function does
    return [MockResponse(content)]


