# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import simbad


def test_simbad():
    r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    print r.table
    assert "M  31" in r.table["MAIN_ID"]


def test_multi():
    result = simbad.QueryMulti(
            [simbad.QueryId('m31'),
             simbad.QueryId('m51')])
    table = result.execute().table
    assert "M  31" in table["MAIN_ID"]
    assert "M  51" in table["MAIN_ID"]

if __name__ == "__main__":
    test_simbad()
    test_multi()
