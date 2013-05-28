# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import simbad
import sys
is_python3 = (sys.version_info >= (3,))


def test_simbad():
    r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    print r.table
    if is_python3:
        m31 = b"M  31"
    else:
        m31 = "M  31"
    assert m31 in r.table["MAIN_ID"]


def test_multi():
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
    test_simbad()
    test_multi()
