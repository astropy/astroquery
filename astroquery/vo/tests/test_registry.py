from __future__ import print_function

import pytest
from astropy.tests.helper import pytest
from ...utils.testing_tools import MockResponse

from ... import vo

## Debugging only. Should be in thetests
import json, os, pandas
from astroquery.vo import Registry


## To run just this test,
##
## ( cd ../../ ; python setup.py test -t astroquery/vo/tests/test_registry.py )
##


@pytest.fixture
def patch(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(vo.Registry, '_request', mockreturn)
    return mp

def mockreturn(method="POST", url=None, data=None, params=None, timeout=10, **kwargs):
    # Determine the test case from the URL and/or data
    print("DEBUGGING:  Got into mockreturn().")
    assert "query" in data
    if "ivoid like '%heasarc%'" in data['query'] and "cap_type like '%simpleimageaccess%'" in data['query']:
        testcase = "query_basic_response"
    elif "order by count_" in data['query']:
        testcase = "query_counts_response"
    else:
        raise ValueError("Can't figure out the test case from data={}".format(data))

    filename = data_path(DATA_FILES[testcase])
    url, content=json2raw(filename)
    return MockResponse(content)


##
##  Tests that make an http request that we need to mock:
##

from .thetests import *

DATA_FILES=TestReg.DATA_FILES

def test_mockquery_basic(patch):
    t=TestReg()
    t.query_basic()

def test_mockquery_counts(patch):
    t=TestReg()
    t.query_counts()

def test_mockquery_timeout(patch):
    t=TestReg()
    t.query_timeout()

