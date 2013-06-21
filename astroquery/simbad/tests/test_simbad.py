# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import simbad
from astropy.tests.helper import pytest, remote_data
import sys
import os
is_python3 = (sys.version_info >= (3,))

M31_DATA = "datam31"
MULTI_DATA = "datamulti"

def data(filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

@pytest.fixture
def patch_execute(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(simbad.queries, 'execute_query', execute_query_mockreturn)
    return mp

def execute_query_mockreturn(query, votabledef, limit, pedantic, mirror=None):
    if isinstance(query, simbad.queries.QueryMulti):
        return open(data(MULTI_DATA), "r").read()
    return open(data(M31_DATA), "r").read()

def test_simbad_1(patch_execute):
    r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    print r.table
    if is_python3:
        m31 = b"M  31"
    else:
        m31 = "M  31"
    assert m31 in r.table["MAIN_ID"]

def test_multi_1(patch_execute):
    result = simbad.QueryMulti(
            [simbad.QueryId('m31'),
             simbad.QueryId('m51')]).execute()
    table = result.table
    if is_python3:
        m31 = b"M  31"
        m51 = b"M  51"
    else:
        m31 = "M  31"
        m51 = "M  51"
    assert m31 in table["MAIN_ID"]
    assert m51 in table["MAIN_ID"]

@remote_data
def test_simbad_2():
    r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    print r.table
    if is_python3:
        m31 = b"M  31"
    else:
        m31 = "M  31"
    assert m31 in r.table["MAIN_ID"]

@remote_data
def test_multi_2():
    result = simbad.QueryMulti(
            [simbad.QueryId('m31'),
             simbad.QueryId('m51')])
    table = result.execute().table
    if is_python3:
        m31 = b"M  31"
        m51 = b"M  51"
    else:
        m31 = "M  31"
        m51 = "M  51"
    assert m31 in table["MAIN_ID"]
    assert m51 in table["MAIN_ID"]

if __name__ == "__main__":
    test_simbad_1()
    test_multi_1()
    test_simbad_2()
    test_multi_2()
